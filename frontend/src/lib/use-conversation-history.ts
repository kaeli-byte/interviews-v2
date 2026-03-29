import { useCallback, useEffect, useRef, useState } from "react";
import {
  appendConversationMessage,
  createConversation,
  loadConversationMessages,
  loadLatestConversation,
  touchConversation,
  type ConversationRole,
} from "@/lib/conversations";

export interface ConversationUiMessage {
  id: string;
  role: ConversationRole;
  content: string;
  timestamp: Date;
  isLive?: boolean;
}

interface UseConversationHistoryReturn {
  messages: ConversationUiMessage[];
  conversationId: string | null;
  isHydrating: boolean;
  error: Error | null;
  setDraft: (role: ConversationRole, text: string) => void;
  finalizeTurn: (role: ConversationRole, text: string) => Promise<void>;
  resetConversation: () => void;
}

export function useConversationHistory(): UseConversationHistoryReturn {
  const [messages, setMessages] = useState<ConversationUiMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isHydrating, setIsHydrating] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const nextMessageIdRef = useRef(1);
  const nextSequenceRef = useRef(1);
  const conversationIdRef = useRef<string | null>(null);

  useEffect(() => {
    conversationIdRef.current = conversationId;
  }, [conversationId]);

  useEffect(() => {
    let isCancelled = false;

    const hydrateConversation = async () => {
      try {
        const latestConversation = await loadLatestConversation();
        if (!latestConversation || isCancelled) {
          return;
        }

        const storedMessages = await loadConversationMessages(latestConversation.id);
        if (isCancelled) {
          return;
        }

        conversationIdRef.current = latestConversation.id;
        setConversationId(latestConversation.id);
        nextSequenceRef.current = storedMessages.length + 1;
        nextMessageIdRef.current = storedMessages.length + 1;
        setMessages(
          storedMessages.map((message) => ({
            id: `message-${message.sequence}`,
            role: message.role,
            content: message.content,
            timestamp: new Date(message.created_at),
          }))
        );
      } catch (hydrateError) {
        if (!isCancelled) {
          setError(
            hydrateError instanceof Error
              ? hydrateError
              : new Error("Failed to load conversation history")
          );
        }
      } finally {
        if (!isCancelled) {
          setIsHydrating(false);
        }
      }
    };

    void hydrateConversation();

    return () => {
      isCancelled = true;
    };
  }, []);

  const setDraft = useCallback((role: ConversationRole, text: string) => {
    const draftId = `live-${role}`;
    const trimmedText = text.trim();

    setMessages((prev) => {
      const withoutDraft = prev.filter((message) => message.id !== draftId);
      if (!trimmedText) {
        return withoutDraft;
      }

      return [
        ...withoutDraft,
        {
          id: draftId,
          role,
          content: trimmedText,
          timestamp: new Date(),
          isLive: true,
        },
      ];
    });
  }, []);

  const ensureConversation = useCallback(async () => {
    if (conversationIdRef.current) {
      return conversationIdRef.current;
    }

    const conversation = await createConversation();
    if (!conversation) {
      return null;
    }

    conversationIdRef.current = conversation.id;
    setConversationId(conversation.id);
    return conversation.id;
  }, []);

  const finalizeTurn = useCallback(
    async (role: ConversationRole, text: string) => {
      const trimmedText = text.trim();
      const draftId = `live-${role}`;
      if (!trimmedText) {
        setMessages((prev) => prev.filter((message) => message.id !== draftId));
        return;
      }

      const messageId = `message-${nextMessageIdRef.current++}`;
      const sequence = nextSequenceRef.current++;
      const timestamp = new Date();

      setMessages((prev) => {
        const withoutDraft = prev.filter((message) => message.id !== draftId);
        return [
          ...withoutDraft,
          {
            id: messageId,
            role,
            content: trimmedText,
            timestamp,
          },
        ];
      });

      try {
        const activeConversationId = await ensureConversation();
        if (!activeConversationId) {
          return;
        }

        await appendConversationMessage({
          conversationId: activeConversationId,
          role,
          content: trimmedText,
          sequence,
        });
        await touchConversation(activeConversationId);
      } catch (persistError) {
        setError(
          persistError instanceof Error
            ? persistError
            : new Error("Failed to persist conversation turn")
        );
      }
    },
    [ensureConversation]
  );

  const resetConversation = useCallback(() => {
    conversationIdRef.current = null;
    setConversationId(null);
    nextMessageIdRef.current = 1;
    nextSequenceRef.current = 1;
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    conversationId,
    isHydrating,
    error,
    setDraft,
    finalizeTurn,
    resetConversation,
  };
}
