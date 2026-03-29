/**
 * MediaHandler: Manages audio/video capture and playback.
 */

export class MediaHandler {
  captureAudioContext: AudioContext | null = null;
  playbackAudioContext: AudioContext | null = null;
  mediaStream: MediaStream | null = null;
  captureWorkletNode: AudioWorkletNode | null = null;
  playbackWorkletNode: AudioWorkletNode | null = null;
  playbackGainNode: GainNode | null = null;
  muteGainNode: GainNode | null = null;
  videoStream: MediaStream | null = null;
  videoInterval: ReturnType<typeof setInterval> | null = null;
  videoCanvas: HTMLCanvasElement | null = null;
  canvasCtx: CanvasRenderingContext2D | null = null;
  isRecording = false;
  inputSampleRate = 16000;
  outputSampleRate = 24000;
  private playbackEndTimer: number | null = null;

  private getAudioContextCtor() {
    return (
      window.AudioContext ||
      (window as Window & typeof globalThis & { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext
    );
  }

  async initializeAudio() {
    const AudioContextCtor = this.getAudioContextCtor();
    if (!AudioContextCtor) {
      throw new Error("AudioContext is not available in this browser");
    }

    if (!this.captureAudioContext) {
      this.captureAudioContext = new AudioContextCtor({
        sampleRate: this.inputSampleRate,
      });
      await this.captureAudioContext.audioWorklet.addModule(
        "/audio-processors/capture.worklet.js"
      );
    }

    if (!this.playbackAudioContext) {
      this.playbackAudioContext = new AudioContextCtor({
        sampleRate: this.outputSampleRate,
      });
      await this.playbackAudioContext.audioWorklet.addModule(
        "/audio-processors/playback.worklet.js"
      );

      this.playbackWorkletNode = new AudioWorkletNode(
        this.playbackAudioContext,
        "pcm-processor"
      );
      this.playbackGainNode = this.playbackAudioContext.createGain();
      this.playbackGainNode.gain.value = 1;
      this.playbackWorkletNode.connect(this.playbackGainNode);
      this.playbackGainNode.connect(this.playbackAudioContext.destination);
    }

    if (this.captureAudioContext.state === "suspended") {
      await this.captureAudioContext.resume();
    }
    if (this.playbackAudioContext.state === "suspended") {
      await this.playbackAudioContext.resume();
    }
  }

  async startAudio(onAudioData: (pcmData: ArrayBuffer) => void) {
    if (this.isRecording) {
      return;
    }

    await this.initializeAudio();

    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: this.inputSampleRate,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    const source = this.captureAudioContext!.createMediaStreamSource(this.mediaStream);
    this.captureWorkletNode = new AudioWorkletNode(
      this.captureAudioContext!,
      "audio-capture-processor"
    );

    this.captureWorkletNode.port.onmessage = (event: MessageEvent<Float32Array>) => {
      if (!this.isRecording) {
        return;
      }
      onAudioData(this.convertFloat32ToInt16(event.data));
    };

    source.connect(this.captureWorkletNode);
    this.muteGainNode = this.captureAudioContext!.createGain();
    this.muteGainNode.gain.value = 0;
    this.captureWorkletNode.connect(this.muteGainNode);
    this.muteGainNode.connect(this.captureAudioContext!.destination);
    this.isRecording = true;
  }

  stopAudio() {
    this.isRecording = false;
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
    if (this.captureWorkletNode) {
      this.captureWorkletNode.disconnect();
      this.captureWorkletNode = null;
    }
    if (this.muteGainNode) {
      this.muteGainNode.disconnect();
      this.muteGainNode = null;
    }
  }

  async startVideo(videoElement: HTMLVideoElement, onFrame: (base64: string) => void) {
    this.videoStream = await navigator.mediaDevices.getUserMedia({
      video: true,
    });
    videoElement.srcObject = this.videoStream;
    this.videoInterval = setInterval(() => {
      this.captureFrame(videoElement, onFrame);
    }, 1000);
  }

  async startScreen(
    videoElement: HTMLVideoElement,
    onFrame: (base64: string) => void,
    onEnded?: () => void
  ) {
    this.videoStream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
    });
    videoElement.srcObject = this.videoStream;

    this.videoStream.getVideoTracks()[0].onended = () => {
      this.stopVideo(videoElement);
      onEnded?.();
    };

    this.videoInterval = setInterval(() => {
      this.captureFrame(videoElement, onFrame);
    }, 1000);
  }

  stopVideo(videoElement: HTMLVideoElement) {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach((track) => track.stop());
      this.videoStream = null;
    }
    if (this.videoInterval) {
      clearInterval(this.videoInterval);
      this.videoInterval = null;
    }
    videoElement.srcObject = null;
  }

  captureFrame(videoElement: HTMLVideoElement, onFrame: (base64: string) => void) {
    if (!this.videoStream) {
      return;
    }
    if (!this.videoCanvas) {
      this.videoCanvas = document.createElement("canvas");
      this.canvasCtx = this.videoCanvas.getContext("2d");
    }
    this.videoCanvas.width = 640;
    this.videoCanvas.height = 480;
    this.canvasCtx!.drawImage(videoElement, 0, 0, 640, 480);
    const base64 = this.videoCanvas.toDataURL("image/jpeg", 0.7).split(",")[1];
    onFrame(base64);
  }

  playAudio(arrayBuffer: ArrayBuffer, onEnded?: () => void) {
    if (!this.playbackAudioContext || !this.playbackWorkletNode) {
      return;
    }
    if (this.playbackAudioContext.state === "suspended") {
      void this.playbackAudioContext.resume();
    }

    const pcmData = new Int16Array(arrayBuffer);
    const float32Data = new Float32Array(pcmData.length);
    for (let i = 0; i < pcmData.length; i++) {
      float32Data[i] = pcmData[i] / 32768.0;
    }

    this.playbackWorkletNode.port.postMessage(float32Data);

    if (this.playbackEndTimer) {
      window.clearTimeout(this.playbackEndTimer);
    }
    if (onEnded) {
      const durationMs = (float32Data.length / this.outputSampleRate) * 1000;
      this.playbackEndTimer = window.setTimeout(() => {
        this.playbackEndTimer = null;
        onEnded();
      }, durationMs + 60);
    }
  }

  stopAudioPlayback() {
    if (this.playbackWorkletNode) {
      this.playbackWorkletNode.port.postMessage("interrupt");
    }
    if (this.playbackEndTimer) {
      window.clearTimeout(this.playbackEndTimer);
      this.playbackEndTimer = null;
    }
  }

  convertFloat32ToInt16(buffer: Float32Array) {
    let l = buffer.length;
    const out = new Int16Array(l);
    while (l--) {
      out[l] = Math.min(1, Math.max(-1, buffer[l])) * 0x7fff;
    }
    return out.buffer;
  }
}
