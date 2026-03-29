/**
 * DirectGeminiClient: Connects directly to Gemini Live API
 * Uses ephemeral token from backend for authentication
 */

interface DirectGeminiConfig {
  model?: string;
  onOpen?: () => void;
  onMessage?: (event: MessageEvent) => void;
  onInputTranscript?: (text: string, isFinal: boolean) => void;
  onOutputTranscript?: (text: string, isFinal: boolean) => void;
  onTurnComplete?: () => void;
  onInterrupted?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
}

interface GeminiInlineDataPart {
  inlineData?: {
    data: string;
    mimeType?: string;
  };
  text?: string;
}

interface GeminiServerContent {
  modelTurn?: {
    parts?: GeminiInlineDataPart[];
  };
  outputTranscription?: {
    text?: string;
    finished?: boolean;
  };
  inputTranscription?: {
    text?: string;
    finished?: boolean;
  };
  interrupted?: boolean;
  turnComplete?: boolean;
}

interface GeminiLiveResponse {
  setupComplete?: boolean;
  serverContent?: GeminiServerContent;
  error?: unknown;
}

export class DirectGeminiClient {
  private static systemInstructionCache: string | null = null;
  private websocket: WebSocket | null = null;
  private model: string;
  private systemInstruction = "";
  private onInputTranscript?: (text: string, isFinal: boolean) => void;
  private onOutputTranscript?: (text: string, isFinal: boolean) => void;
  private onTurnComplete?: () => void;
  private onInterrupted?: () => void;
  private onMessage?: (event: MessageEvent) => void;
  private onOpen?: () => void;
  private onClose?: (event: CloseEvent) => void;
  private onError?: (event: Event) => void;
  private accumulatedText = "";
  private accumulatedInputTranscript = "";
  private accumulatedOutputTranscript = "";
  private token: string = "";

  constructor(config: DirectGeminiConfig) {
    this.model = config.model || "gemini-3.1-flash-live-preview";
    this.onInputTranscript = config.onInputTranscript;
    this.onOutputTranscript = config.onOutputTranscript;
    this.onTurnComplete = config.onTurnComplete;
    this.onInterrupted = config.onInterrupted;
    this.onMessage = config.onMessage;
    this.onOpen = config.onOpen;
    this.onClose = config.onClose;
    this.onError = config.onError;
  }

  async connect(): Promise<void> {
    try {
      this.systemInstruction = await DirectGeminiClient.getSystemInstruction();
      const response = await fetch("/api/token", { method: "POST" });
      if (!response.ok) {
        throw new Error(`Failed to get token: ${response.statusText}`);
      }
      const { token } = await response.json();
      this.token = token;
    } catch (e) {
      console.error("[Direct Gemini] Failed to get token:", e);
      if (this.onError) this.onError(new Event("token-fetch-failed"));
      return;
    }

    // Now connect using the token
    const wsUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContentConstrained?access_token=${this.token}`;

    this.websocket = new WebSocket(wsUrl);
    this.websocket.binaryType = "arraybuffer";

    return await new Promise<void>((resolve, reject) => {
      let setupResolved = false;

      this.websocket!.onopen = () => {
        this.sendConfig();
      };

      this.websocket!.onmessage = async (event) => {
        const response = await this.parseServerMessage(event.data);
        if (!response) {
          return;
        }

        if (response.setupComplete) {
          setupResolved = true;
          this.onOpen?.();
          resolve();
          return;
        }

        const parts = response.serverContent?.modelTurn?.parts;
        if (parts?.length) {
          for (const part of parts) {
            if (part.inlineData?.data) {
              const audioBuffer = this.base64ToArrayBuffer(part.inlineData.data);
              this.onMessage?.(new MessageEvent("message", { data: audioBuffer }));
            } else if (part.text) {
              this.accumulatedText += part.text;
              this.onOutputTranscript?.(this.accumulatedText, false);
            }
          }
        }

        if (response.serverContent?.outputTranscription) {
          const transcript = response.serverContent.outputTranscription.text || "";
          const finished = response.serverContent.outputTranscription.finished || false;
          if (transcript) {
            this.accumulatedOutputTranscript += transcript;
            const fullOutputTranscript = this.accumulatedOutputTranscript.trim();
            if (finished) {
              console.log("[Direct Gemini] Output transcription:", fullOutputTranscript);
              this.accumulatedOutputTranscript = "";
            }
            this.onOutputTranscript?.(fullOutputTranscript, finished);
          }
        }

        if (response.serverContent?.inputTranscription) {
          const transcript = response.serverContent.inputTranscription.text || "";
          const finished = response.serverContent.inputTranscription.finished || false;
          if (transcript) {
            this.accumulatedInputTranscript += transcript;
            const fullInputTranscript = this.accumulatedInputTranscript.trim();
            if (finished) {
              console.log(
                "[Direct Gemini] Input transcription:",
                fullInputTranscript
              );
              this.accumulatedInputTranscript = "";
            }
            this.onInputTranscript?.(fullInputTranscript, finished);
          }
        }

        if (response.serverContent?.interrupted) {
          this.onInterrupted?.();
        }

        if (response.serverContent?.turnComplete) {
          if (this.accumulatedInputTranscript.trim()) {
            console.log(
              "[Direct Gemini] Input transcription:",
              this.accumulatedInputTranscript.trim()
            );
          }
          if (this.accumulatedOutputTranscript.trim()) {
            console.log("[Direct Gemini] Output transcription:", this.accumulatedOutputTranscript.trim());
          }
          if (this.accumulatedText) {
            this.onOutputTranscript?.(this.accumulatedText, true);
          }
          this.accumulatedText = "";
          this.accumulatedInputTranscript = "";
          this.accumulatedOutputTranscript = "";
          this.onTurnComplete?.();
        }

        if (response.error) {
          console.error("[Direct Gemini] API Error:", response.error);
        }
      };

      this.websocket!.onclose = (event) => {
        console.log("[Direct Gemini] Closed", { code: event.code, reason: event.reason });
        if (!setupResolved) {
          reject(new Error(`WebSocket closed before setup completed (${event.code})`));
        }
        if (this.onClose) this.onClose(event);
      };

      this.websocket!.onerror = (event) => {
        console.error("[Direct Gemini] Error:", event);
        if (!setupResolved) {
          reject(new Error("WebSocket setup failed"));
        }
        if (this.onError) this.onError(event);
      };
    });
  }

  private static async getSystemInstruction(): Promise<string> {
    if (DirectGeminiClient.systemInstructionCache) {
      return DirectGeminiClient.systemInstructionCache;
    }

    const response = await fetch("/prompts/role");
    if (!response.ok) {
      throw new Error(`Failed to load role prompt: ${response.statusText}`);
    }

    const prompt = await response.text();
    DirectGeminiClient.systemInstructionCache = prompt;
    return prompt;
  }

  private sendConfig() {
    const config = {
      setup: {
        model: `models/${this.model}`,
        generationConfig: {
          responseModalities: ["AUDIO"],
          temperature: 1.0,
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: {
                voiceName: "Puck",
              },
            },
          },
        },
        systemInstruction: {
          parts: [
            {
              text: this.systemInstruction,
            },
          ],
        },
        realtimeInputConfig: {
          automaticActivityDetection: {
            disabled: false,
            silenceDurationMs: 2000,
            prefixPaddingMs: 500,
            endOfSpeechSensitivity: "END_SENSITIVITY_UNSPECIFIED",
            startOfSpeechSensitivity: "START_SENSITIVITY_UNSPECIFIED",
          },
          activityHandling: "ACTIVITY_HANDLING_UNSPECIFIED",
          turnCoverage: "TURN_INCLUDES_ONLY_ACTIVITY",
        },
        inputAudioTranscription: {},
        outputAudioTranscription: {},
      },
    };

    this.websocket?.send(JSON.stringify(config));
  }

  sendText(text: string) {
    const msg = {
      realtimeInput: {
        text: text,
      },
    };
    this.websocket?.send(JSON.stringify(msg));
  }

  sendAudio(audioData: ArrayBuffer) {
    // Convert to base64 like the reference demo
    const bytes = new Uint8Array(audioData);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    const base64Audio = btoa(binary);

    const message = {
      realtimeInput: {
        audio: {
          mimeType: "audio/pcm",
          data: base64Audio
        }
      }
    };
    this.websocket?.send(JSON.stringify(message));
  }

  disconnect() {
    this.websocket?.close();
    this.websocket = null;
  }

  isConnected() {
    return this.websocket?.readyState === WebSocket.OPEN;
  }

  private async parseServerMessage(
    data: string | ArrayBuffer | Blob
  ): Promise<GeminiLiveResponse | null> {
    let raw = "";

    if (typeof data === "string") {
      raw = data;
    } else if (data instanceof Blob) {
      raw = await data.text();
    } else if (data instanceof ArrayBuffer) {
      raw = new TextDecoder().decode(data);
    }

    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as GeminiLiveResponse;
    } catch (error) {
      console.warn("[Direct Gemini] Non-JSON frame:", raw, error);
      return null;
    }
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }
}
