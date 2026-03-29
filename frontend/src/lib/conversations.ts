import { supabase } from "@/lib/supabase";

export type ConversationRole = "user" | "assistant";

export interface ConversationRecord {
  id: string;
  user_id: string | null;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessageRecord {
  id: string;
  conversation_id: string;
  role: ConversationRole;
  content: string;
  sequence: number;
  created_at: string;
}

async function getCurrentUserId(): Promise<string | null> {
  const { data, error } = await supabase.auth.getUser();
  if (error) {
    if (error.name === "AuthSessionMissingError") {
      return null;
    }
    throw error;
  }

  return data.user?.id ?? null;
}

export async function loadLatestConversation(): Promise<ConversationRecord | null> {
  const userId = await getCurrentUserId();
  if (!userId) {
    return null;
  }

  const { data, error } = await supabase
    .from("conversations")
    .select("id,user_id,title,created_at,updated_at")
    .eq("user_id", userId)
    .order("updated_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) {
    throw error;
  }

  return data;
}

export async function createConversation(title?: string): Promise<ConversationRecord | null> {
  const userId = await getCurrentUserId();
  if (!userId) {
    return null;
  }

  const payload = {
    user_id: userId,
    title: title ?? null,
  };

  const { data, error } = await supabase
    .from("conversations")
    .insert(payload)
    .select("id,user_id,title,created_at,updated_at")
    .single();

  if (error) {
    throw error;
  }

  return data;
}

export async function loadConversationMessages(
  conversationId: string
): Promise<ConversationMessageRecord[]> {
  const { data, error } = await supabase
    .from("conversation_messages")
    .select("id,conversation_id,role,content,sequence,created_at")
    .eq("conversation_id", conversationId)
    .order("sequence", { ascending: true });

  if (error) {
    throw error;
  }

  return data ?? [];
}

export async function appendConversationMessage(input: {
  conversationId: string;
  role: ConversationRole;
  content: string;
  sequence: number;
}): Promise<ConversationMessageRecord> {
  const { data, error } = await supabase
    .from("conversation_messages")
    .insert({
      conversation_id: input.conversationId,
      role: input.role,
      content: input.content,
      sequence: input.sequence,
    })
    .select("id,conversation_id,role,content,sequence,created_at")
    .single();

  if (error) {
    throw error;
  }

  return data;
}

export async function touchConversation(conversationId: string): Promise<void> {
  const { error } = await supabase
    .from("conversations")
    .update({ updated_at: new Date().toISOString() })
    .eq("id", conversationId);

  if (error) {
    throw error;
  }
}
