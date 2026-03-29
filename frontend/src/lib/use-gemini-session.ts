/**
 * useGeminiSession - Direct connection to Gemini Live API
 */
import { useState, useEffect, useRef, useCallback } from "react";
import type { DirectGeminiClient } from "@/lib/direct-gemini-client";
import type { MediaHandler } from "@/lib/media-handler";

const INITIAL_GREETING_PROMPT =
  "System: Introduce yourself as a concise, friendly voice assistant and invite the user to start speaking.";

type SessionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "listening"
  | "speaking"
  | "error";

interface UseGeminiSessionOptions {
  onInputTranscript?: (text: string, isFinal: boolean) => void;
  onOutputTranscript?: (text: string, isFinal: boolean) => void;
  onAudioResponse?: (audioData: ArrayBuffer) => void;
  onError?: (error: Error) => void;
  onStateChange?: (state: SessionState) => void;
}

interface UseGeminiSessionReturn {
  state: SessionState;
  startSession: () => Promise<void>;
  stopSession: () => void;
  sendText: (text: string) => void;
  startAudio: () => Promise<void>;
  stopAudio: () => void;
  startVideo: (videoElement: HTMLVideoElement) => Promise<void>;
  stopVideo: (videoElement: HTMLVideoElement) => void;
  isMicMuted: boolean;
  toggleMicMute: () => void;
  isCameraOn: boolean;
  toggleCamera: () => void;
}

export function useGeminiSession(options: UseGeminiSessionOptions = {}): UseGeminiSessionReturn {
  const { onInputTranscript, onOutputTranscript, onAudioResponse, onError, onStateChange } = options;
  const [state, setState] = useState<SessionState>("disconnected");
  const [isMicMuted, setIsMicMuted] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const clientRef = useRef<DirectGeminiClient | null>(null);
  const mediaHandlerRef = useRef<MediaHandler | null>(null);
  const videoElementRef = useRef<HTMLVideoElement | null>(null);
  const stateRef = useRef<SessionState>("disconnected");
  const isSessionActiveRef = useRef(false);
  const isMicMutedRef = useRef(false);
  const isAudioActiveRef = useRef(false);

  const updateState = useCallback(
    (nextState: SessionState) => {
      stateRef.current = nextState;
      setState(nextState);
      onStateChange?.(nextState);
    },
    [onStateChange]
  );

  useEffect(() => {
    isMicMutedRef.current = isMicMuted;
  }, [isMicMuted]);

  const stopAudio = useCallback(() => {
    const wasRecording = isAudioActiveRef.current;
    mediaHandlerRef.current?.stopAudio();
    isAudioActiveRef.current = false;
    if (wasRecording) {
      console.log("[Voice] Microphone stopped");
    }
    if (isSessionActiveRef.current && stateRef.current !== "speaking") {
      updateState("connected");
    }
  }, [updateState]);

  const startAudio = useCallback(async () => {
    if (!mediaHandlerRef.current || !clientRef.current || isAudioActiveRef.current) {
      return;
    }

    try {
      await mediaHandlerRef.current.startAudio((pcmData: ArrayBuffer) => {
        if (!isMicMutedRef.current && clientRef.current?.isConnected()) {
          clientRef.current.sendAudio(pcmData);
        }
      });
      isAudioActiveRef.current = true;
      if (isSessionActiveRef.current) {
        updateState("listening");
      }
      console.log("[Voice] Microphone active");
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error("Failed to start audio"));
    }
  }, [onError, updateState]);

  const startSession = useCallback(async () => {
    if (isSessionActiveRef.current) {
      return;
    }

    updateState("connecting");

    try {
      const { DirectGeminiClient } = await import("@/lib/direct-gemini-client");
      const { MediaHandler } = await import("@/lib/media-handler");

      mediaHandlerRef.current = new MediaHandler();
      await mediaHandlerRef.current.initializeAudio();

      const client = new DirectGeminiClient({
        onOpen: () => {
          isSessionActiveRef.current = true;
          updateState("connected");
        },
        onInputTranscript: (text, isFinal) => {
          onInputTranscript?.(text, isFinal);
        },
        onOutputTranscript: (text, isFinal) => {
          onOutputTranscript?.(text, isFinal);
        },
        onTurnComplete: () => {
          if (isSessionActiveRef.current && !isMicMutedRef.current && isAudioActiveRef.current) {
            updateState("listening");
          }
        },
        onInterrupted: () => {
          mediaHandlerRef.current?.stopAudioPlayback();
          if (isSessionActiveRef.current && !isMicMutedRef.current && isAudioActiveRef.current) {
            updateState("listening");
          }
        },
        onMessage: (event: MessageEvent) => {
          if (!(event.data instanceof ArrayBuffer)) {
            return;
          }
          updateState("speaking");
          mediaHandlerRef.current?.playAudio(event.data);

          onAudioResponse?.(event.data);
        },
        onClose: () => {
          isSessionActiveRef.current = false;
          isAudioActiveRef.current = false;
          updateState("disconnected");
        },
        onError: () => {
          onError?.(new Error("WebSocket connection failed"));
          updateState("error");
        },
      });

      clientRef.current = client;
      await client.connect();
      client.sendText(INITIAL_GREETING_PROMPT);
      await startAudio();
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error("Failed to start session"));
      updateState("error");
    }
  }, [onAudioResponse, onError, onInputTranscript, onOutputTranscript, startAudio, updateState]);

  const stopSession = useCallback(() => {
    isSessionActiveRef.current = false;
    stopAudio();

    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }

    if (mediaHandlerRef.current) {
      if (videoElementRef.current) {
        mediaHandlerRef.current.stopVideo(videoElementRef.current);
      }
      mediaHandlerRef.current = null;
    }

    updateState("disconnected");
  }, [stopAudio, updateState]);

  const sendText = useCallback((text: string) => {
    if (clientRef.current?.isConnected()) {
      clientRef.current.sendText(text);
    }
  }, []);

  const startVideo = useCallback(async (videoElement: HTMLVideoElement) => {
    if (!mediaHandlerRef.current || !clientRef.current) {
      return;
    }

    videoElementRef.current = videoElement;

    try {
      await mediaHandlerRef.current.startVideo(videoElement, () => {
        // Video frames are not wired into the direct client yet.
      });
      setIsCameraOn(true);
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error("Failed to start video"));
    }
  }, [onError]);

  const stopVideo = useCallback((videoElement: HTMLVideoElement) => {
    mediaHandlerRef.current?.stopVideo(videoElement);
    videoElementRef.current = null;
    setIsCameraOn(false);
  }, []);

  const toggleMicMute = useCallback(() => {
    setIsMicMuted((prev) => {
      const next = !prev;
      if (next) {
        stopAudio();
      } else if (isSessionActiveRef.current) {
        void startAudio();
      }
      return next;
    });
  }, [startAudio, stopAudio]);

  const toggleCamera = useCallback(() => {
    if (isCameraOn && videoElementRef.current) {
      stopVideo(videoElementRef.current);
      return;
    }

    if (videoElementRef.current) {
      void startVideo(videoElementRef.current);
    }
  }, [isCameraOn, startVideo, stopVideo]);

  useEffect(() => {
    return () => {
      clientRef.current?.disconnect();
      mediaHandlerRef.current?.stopAudio();
      if (mediaHandlerRef.current?.audioContext) {
        void mediaHandlerRef.current.audioContext.close();
      }
    };
  }, []);

  return {
    state,
    startSession,
    stopSession,
    sendText,
    startAudio,
    stopAudio,
    startVideo,
    stopVideo,
    isMicMuted,
    toggleMicMute,
    isCameraOn,
    toggleCamera,
  };
}
