"use client";

import { cn } from "@/lib/utils";
import { useGeminiSession } from "@/lib/use-gemini-session";
import { useConversationHistory } from "@/lib/use-conversation-history";
import {
  Mic,
  MicOff,
  Settings,
  Bot,
  User,
  Video,
  VideoOff,
  MessageCircle,
  MessageCircleOff,
  MessageCircleMore,
} from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";

interface LiquidGlassVoiceAssistantProps {
  className?: string;
}

type VoiceState = "idle" | "listening" | "processing" | "speaking";

export function LiquidGlassVoiceAssistant({
  className,
}: LiquidGlassVoiceAssistantProps) {
  const SCROLL_BOTTOM_THRESHOLD = 48;
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [volume, setVolume] = useState(0);
  const [isMicActive, setIsMicActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isPinnedToBottomRef = useRef(true);

  const { messages, setDraft, finalizeTurn, error: conversationError } =
    useConversationHistory();

  const isNearBottom = useCallback((element: HTMLDivElement) => {
    const distanceFromBottom =
      element.scrollHeight - element.scrollTop - element.clientHeight;
    return distanceFromBottom <= SCROLL_BOTTOM_THRESHOLD;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const container = scrollContainerRef.current;
    if (!container) {
      return;
    }

    container.scrollTo({
      top: container.scrollHeight,
      behavior,
    });
  }, []);

  const upsertLiveMessage = useCallback(
    (role: "user" | "assistant", content: string) => {
      const container = scrollContainerRef.current;
      const shouldStickToBottom = container ? isNearBottom(container) : true;

      isPinnedToBottomRef.current = shouldStickToBottom;
      setDraft(role, content);
    },
    [isNearBottom, setDraft]
  );

  const finalizeLiveMessage = useCallback(
    async (role: "user" | "assistant", content: string) => {
      await finalizeTurn(role, content);
    },
    [finalizeTurn]
  );

  const {
    state: sessionState,
    startSession,
    stopSession,
    startAudio,
    stopAudio,
    isCameraOn,
    toggleCamera,
  } = useGeminiSession({
    onInputTranscript: (text, isFinal) => {
      if (isFinal && text) {
        void finalizeLiveMessage("user", text);
        return;
      }

      upsertLiveMessage("user", text);
    },
    onOutputTranscript: (text, isFinal) => {
      if (isFinal && text) {
        void finalizeLiveMessage("assistant", text);
        return;
      }

      upsertLiveMessage("assistant", text);
    },
    onAudioResponse: () => {
      setIsMicActive(false);
      setVoiceState("speaking");
    },
    onError: (error) => {
      console.error("Session error:", error);
      setVoiceState("idle");
      setIsMicActive(false);
    },
    onStateChange: (newState) => {
      if (newState === "connected" || newState === "listening") {
        setVoiceState("listening");
        setIsMicActive(newState === "listening");
      } else if (newState === "speaking") {
        setVoiceState("speaking");
        setIsMicActive(false);
      } else if (newState === "disconnected") {
        setVoiceState("idle");
        setIsMicActive(false);
      } else if (newState === "error") {
        setVoiceState("idle");
        setIsMicActive(false);
      }
    },
  });

  useEffect(() => {
    if (isPinnedToBottomRef.current) {
      scrollToBottom(messages.length <= 1 ? "auto" : "smooth");
    }
  }, [messages, scrollToBottom]);

  const handleTranscriptScroll = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) {
      return;
    }

    isPinnedToBottomRef.current = isNearBottom(container);
  }, [isNearBottom]);

  const toggleVoice = async () => {
    console.log("toggleVoice called, voiceState:", voiceState);
    if (voiceState !== "idle") {
      stopAudio();
      setIsMicActive(false);
      stopSession();
      setVoiceState("idle");
      return;
    }

    await startSession();
    setVoiceState("listening");
    setIsMicActive(true);
  };

  const toggleMicCapture = async () => {
    if (!["connected", "listening", "speaking"].includes(sessionState)) {
      return;
    }

    if (isMicActive) {
      stopAudio();
      setIsMicActive(false);
      setVoiceState("processing");
      return;
    }

    try {
      await startAudio();
      setIsMicActive(true);
      setVoiceState("listening");
    } catch (err) {
      console.error("[Voice] Failed to start audio:", err);
    }
  };

  useEffect(() => {
    if (voiceState === "listening" || voiceState === "speaking") {
      const interval = setInterval(() => {
        setVolume(Math.random() * 100);
      }, 100);
      return () => clearInterval(interval);
    }
  }, [voiceState]);

  useEffect(() => {
    if (conversationError) {
      console.error("Conversation persistence error:", conversationError);
    }
  }, [conversationError]);

  const waveformBars = [4, 6, 3, 8, 2, 5, 7, 4, 6, 3, 8, 2, 5, 7];

  return (
    <div className="relative w-full self-stretch">
      <video ref={videoRef} className="hidden" autoPlay playsInline muted />

      <div
        className={cn(
          "w-full rounded-2xl border border-[var(--glass-border)]",
          "bg-[var(--glass-bg)] backdrop-blur-xl backdrop-saturate-150",
          "shadow-[var(--glass-shadow),var(--glass-shadow-inset)]",
          "before:pointer-events-none before:absolute before:inset-0 before:rounded-2xl",
          "before:bg-[var(--glass-highlight)]",
          "after:pointer-events-none after:absolute after:inset-0 after:rounded-2xl",
          "after:bg-[var(--glass-edge-glow)]",
          "overflow-hidden",
          className
        )}
      >
        <div className="relative z-10 flex h-[42rem] min-h-[36rem] flex-col">
          <div className="flex shrink-0 items-center justify-between border-b border-[var(--glass-border-subtle)] p-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </div>
              <div>
                <span className="text-sm font-medium">AI Voice Assistant</span>
                <div className="flex items-center gap-1.5">
                  <div
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      voiceState === "listening" || voiceState === "speaking"
                        ? "animate-pulse bg-green-400"
                        : "bg-muted-foreground/50"
                    )}
                  />
                  <span className="text-xs opacity-70">
                    {voiceState === "idle" && "Ready"}
                    {voiceState === "listening" && "Listening..."}
                    {voiceState === "processing" && "Processing..."}
                    {voiceState === "speaking" && "Speaking"}
                  </span>
                </div>
              </div>
            </div>
            <button
              aria-label="Assistant settings"
              className="p-2 rounded-lg hover:bg-[var(--glass-bg-hover)] transition-colors"
            >
              <Settings className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>

          <div
            ref={scrollContainerRef}
            onScroll={handleTranscriptScroll}
            className="min-h-0 flex-1 overflow-y-auto px-4 py-4"
          >
            <div className="space-y-4 pr-1">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-3",
                    message.role === "user" ? "flex-row-reverse" : "flex-row"
                  )}
                >
                  <div
                    className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                      message.role === "user" ? "bg-muted" : "bg-primary"
                    )}
                  >
                    {message.role === "user" ? (
                      <User className="h-4 w-4 text-foreground" />
                    ) : (
                      <Bot className="h-4 w-4 text-primary-foreground" />
                    )}
                  </div>

                  <div
                    className={cn(
                      "max-w-[80%] rounded-2xl p-3",
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-[var(--glass-bg-hover)] border border-[var(--glass-border-subtle)]",
                      message.isLive && "opacity-80 ring-1 ring-primary/20"
                    )}
                  >
                    <p className="text-sm">{message.content}</p>
                    <div className="mt-2 flex items-center gap-2">
                      {message.isLive ? (
                        <span className="text-[10px] uppercase tracking-[0.2em] opacity-60">
                          Live
                        </span>
                      ) : (
                        <span
                          className={cn(
                            "text-xs opacity-60",
                            message.role === "user"
                              ? "text-primary-foreground"
                              : "text-muted-foreground"
                          )}
                        >
                          {message.timestamp.toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {(voiceState === "listening" || voiceState === "speaking") && (
            <div className="shrink-0 border-t border-[var(--glass-border-subtle)] px-4 py-2">
              <div className="flex items-center justify-center gap-1 h-8 mb-2">
                {waveformBars.map((baseHeight, index) => (
                  <div
                    key={index}
                    className={cn("w-1 rounded-full animate-pulse bg-primary")}
                    style={{
                      height: `${Math.max(4, baseHeight * 4 * (volume / 100))}px`,
                      animationDelay: `${index * 50}ms`,
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          <div className="shrink-0 border-t border-[var(--glass-border-subtle)] p-4">
            <div className="flex justify-center items-center gap-4">
              <button
                aria-label={isMicActive ? "Stop microphone" : "Start microphone"}
                onClick={toggleMicCapture}
                className={cn(
                  "group inline-flex h-14 w-14 items-center justify-center rounded-full",
                  "border border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] backdrop-blur-sm",
                  "shadow-[var(--glass-shadow-subtle)]",
                  "transition-all duration-300",
                  isMicActive
                    ? "bg-destructive/20 border-destructive"
                    : "hover:bg-[var(--glass-bg-hover)] hover:scale-105",
                  "active:scale-95"
                )}
              >
                {isMicActive ? (
                  <MicOff className="h-6 w-6 text-destructive" />
                ) : (
                  <Mic className="h-6 w-6 text-foreground transition-transform duration-200 group-hover:scale-110" />
                )}
              </button>

              <button
                aria-label={
                  voiceState === "idle"
                    ? "Activate voice assistant"
                    : "Deactivate voice assistant"
                }
                onClick={toggleVoice}
                className={cn(
                  "group inline-flex h-20 w-20 items-center justify-center rounded-full",
                  "border border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] backdrop-blur-sm",
                  "shadow-[var(--glass-shadow-subtle)]",
                  "transition-all duration-300",
                  voiceState === "listening"
                    ? "bg-destructive/20 border-destructive animate-pulse"
                    : voiceState === "processing" || voiceState === "speaking"
                      ? "bg-primary/20 border-primary"
                      : "hover:bg-[var(--glass-bg-hover)] hover:scale-105",
                  "active:scale-95"
                )}
              >
                {voiceState === "idle" ? (
                  <MessageCircleOff className="h-10 w-10 text-foreground transition-transform duration-200 group-hover:scale-110" />
                ) : voiceState === "listening" ? (
                  <MessageCircle className="h-10 w-10 text-destructive animate-pulse" />
                ) : (
                  <MessageCircleMore className="h-10 w-10 text-primary animate-pulse" />
                )}
              </button>

              <button
                aria-label={isCameraOn ? "Turn off camera" : "Turn on camera"}
                onClick={toggleCamera}
                className={cn(
                  "group inline-flex h-14 w-14 items-center justify-center rounded-full",
                  "border border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] backdrop-blur-sm",
                  "shadow-[var(--glass-shadow-subtle)]",
                  "transition-all duration-300",
                  isCameraOn
                    ? "bg-primary/20 border-primary"
                    : "hover:bg-[var(--glass-bg-hover)] hover:scale-105",
                  "active:scale-95"
                )}
              >
                {isCameraOn ? (
                  <Video className="h-6 w-6 text-primary transition-transform duration-200 group-hover:scale-110" />
                ) : (
                  <VideoOff className="h-6 w-6 text-muted-foreground" />
                )}
              </button>
            </div>
            <p className="text-center text-sm text-muted-foreground mt-3">
              {voiceState === "idle" && "Tap to start a live conversation"}
              {voiceState === "listening" && "Listening..."}
              {voiceState === "processing" && "Microphone paused"}
              {voiceState === "speaking" && "Speaking..."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
