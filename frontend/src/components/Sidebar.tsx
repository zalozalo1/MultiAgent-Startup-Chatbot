"use client";

import { MessageSquare, Plus, Trash2 } from "lucide-react";

import type { ConversationSummary } from "@/lib/types";

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: {
  conversations: ConversationSummary[];
  activeId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-edge bg-panel md:flex">
      <div className="p-3">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent/15 px-3 py-2 text-sm font-medium text-accent transition-colors hover:bg-accent/25"
        >
          <Plus size={15} />
          New research
        </button>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
        {conversations.length === 0 && (
          <p className="px-2 pt-2 text-xs text-ink-dim">
            Past research appears here.
          </p>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            className={`group flex items-center gap-2 rounded-lg px-2 py-2 text-sm cursor-pointer ${
              c.id === activeId
                ? "bg-panel-2 text-ink"
                : "text-ink-dim hover:bg-panel-2/60 hover:text-ink"
            }`}
            onClick={() => onSelect(c.id)}
          >
            <MessageSquare size={14} className="shrink-0 opacity-60" />
            <span className="flex-1 truncate">{c.title ?? "Untitled"}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(c.id);
              }}
              className="hidden shrink-0 text-ink-dim hover:text-bad group-hover:block"
              aria-label="Delete conversation"
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
