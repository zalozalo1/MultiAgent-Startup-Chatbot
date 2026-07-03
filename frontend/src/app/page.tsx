"use client";

import { useCallback, useEffect, useState, useSyncExternalStore } from "react";

import { ChatPanel } from "@/components/ChatPanel";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { WorkflowPanel } from "@/components/WorkflowPanel";
import { deleteConversation, fetchConversations } from "@/lib/api";
import { useResearchChat } from "@/hooks/useResearchChat";
import type { ConversationSummary } from "@/lib/types";

const subscribeToHydration = (onStoreChange: () => void) => {
  const timer = window.setTimeout(onStoreChange, 0);
  return () => window.clearTimeout(timer);
};
const getClientHydrationSnapshot = () => true;
const getServerHydrationSnapshot = () => false;

function Workspace({
  conversationId,
  onSwitch,
}: {
  conversationId: string;
  onSwitch: (id: string) => void;
}) {
  const { messages, agents, feed, running, error, connected, sendMessage, stopRun } =
    useResearchChat(conversationId);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);

  const refresh = useCallback(() => {
    fetchConversations().then(setConversations);
  }, []);

  // Refresh the sidebar on load and after each run finishes.
  useEffect(() => {
    if (!running) refresh();
  }, [running, refresh]);

  const handleDelete = useCallback(
    async (id: string) => {
      await deleteConversation(id);
      refresh();
      if (id === conversationId) onSwitch(crypto.randomUUID());
    },
    [conversationId, onSwitch, refresh],
  );

  return (
    <div className="flex h-dvh flex-col">
      <Header connected={connected} running={running} />
      <div className="flex min-h-0 flex-1">
        <Sidebar
          conversations={conversations}
          activeId={conversationId}
          onSelect={onSwitch}
          onNew={() => onSwitch(crypto.randomUUID())}
          onDelete={handleDelete}
        />
        <main className="flex min-w-0 flex-1">
          <ChatPanel
            messages={messages}
            running={running}
            connected={connected}
            error={error}
            onSend={sendMessage}
            onStop={stopRun}
          />
        </main>
        <WorkflowPanel agents={agents} feed={feed} running={running} />
      </div>
    </div>
  );
}

function ClientWorkspace() {
  // Generated client-side after hydration; the id doubles as the AI
  // conversation thread id on the backend and must be a valid UUID.
  const [conversationId, setConversationId] = useState(() => crypto.randomUUID());

  return <Workspace conversationId={conversationId} onSwitch={setConversationId} />;
}

export default function Home() {
  const hydrated = useSyncExternalStore(
    subscribeToHydration,
    getClientHydrationSnapshot,
    getServerHydrationSnapshot,
  );

  if (!hydrated) {
    return <div className="h-dvh bg-surface" />;
  }

  return <ClientWorkspace />;
}
