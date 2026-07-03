import type { ConversationDetail, ConversationSummary } from "@/lib/types";

const BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export function wsUrl(conversationId: string): string {
  return `${BASE.replace(/^http/, "ws")}/ws/conversations/${conversationId}`;
}

export async function fetchConversations(): Promise<ConversationSummary[]> {
  try {
    const res = await fetch(`${BASE}/api/conversations`);
    if (!res.ok) return [];
    return (await res.json()) as ConversationSummary[];
  } catch {
    return []; // backend down or DB unavailable — sidebar just stays empty
  }
}

export async function fetchConversation(id: string): Promise<ConversationDetail | null> {
  try {
    const res = await fetch(`${BASE}/api/conversations/${id}`);
    if (!res.ok) return null;
    return (await res.json()) as ConversationDetail;
  } catch {
    return null;
  }
}

export async function deleteConversation(id: string): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/api/conversations/${id}`, { method: "DELETE" });
    return res.ok;
  } catch {
    return false;
  }
}
