"use client";

import { AlertTriangle, ArrowUp, Rocket, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { MessageBubble } from "@/components/MessageBubble";
import type { ChatMessage } from "@/lib/types";

const EXAMPLE_IDEAS = [
  "A subscription service that delivers personalized plant care kits",
  "An AI copilot that helps freelancers write winning project proposals",
  "A marketplace connecting local chefs with busy families for weekly meal prep",
];

export function ChatPanel({
  messages,
  running,
  connected,
  error,
  onSend,
  onStop,
}: {
  messages: ChatMessage[];
  running: boolean;
  connected: boolean;
  error: string | null;
  onSend: (content: string) => boolean;
  onStop: () => boolean;
}) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, running]);

  const submit = (content: string) => {
    if (running) return;
    if (onSend(content)) setDraft("");
  };

  return (
    <div className="flex h-full min-w-0 flex-1 flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-3xl flex-col gap-4 px-5 py-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center gap-4 pt-20 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/15 text-accent">
                <Rocket size={26} />
              </div>
              <div>
                <h2 className="text-lg font-semibold">
                  Pitch your business idea
                </h2>
                <p className="mt-1 max-w-md text-sm text-ink-dim">
                  A team of AI agents will research the market, size up
                  competitors, profile your customers, shape the product and
                  deliver a full startup research report.
                </p>
              </div>
              <div className="mt-2 flex max-w-xl flex-wrap justify-center gap-2">
                {EXAMPLE_IDEAS.map((idea) => (
                  <button
                    key={idea}
                    onClick={() => submit(idea)}
                    disabled={!connected}
                    className="rounded-full border border-edge bg-panel px-3.5 py-1.5 text-xs text-ink-dim transition-colors hover:border-accent/50 hover:text-ink disabled:opacity-50"
                  >
                    {idea}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}
        </div>
      </div>

      <div className="shrink-0 border-t border-edge bg-panel/60 px-5 py-4">
        <div className="mx-auto max-w-3xl">
          {error && (
            <div className="mb-3 flex items-start gap-2 rounded-lg border border-bad/40 bg-bad/10 px-3 py-2 text-xs text-bad">
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(draft);
            }}
            className="flex items-end gap-2 rounded-xl border border-edge bg-panel p-2 focus-within:border-accent/50"
          >
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit(draft);
                }
              }}
              rows={2}
              placeholder={
                running
                  ? "Agents are researching — hang tight…"
                  : "Describe your business or startup idea…"
              }
              disabled={running}
              className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1 text-sm outline-none placeholder:text-ink-dim/70 disabled:opacity-60"
            />
            <button
              type={running ? "button" : "submit"}
              onClick={running ? onStop : undefined}
              disabled={running ? !connected : !connected || !draft.trim()}
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors disabled:opacity-40 ${
                running
                  ? "bg-white text-surface hover:bg-ink"
                  : "rounded-lg bg-accent text-surface hover:bg-accent-dim"
              }`}
              aria-label={running ? "Stop research" : "Send"}
              title={running ? "Stop research" : "Send"}
            >
              {running ? (
                <Square size={14} fill="currentColor" strokeWidth={0} />
              ) : (
                <ArrowUp size={17} />
              )}
            </button>
          </form>
          <p className="mt-2 text-center text-[11px] text-ink-dim/70">
            Follow-up questions reuse the research already gathered in this
            conversation.
          </p>
        </div>
      </div>
    </div>
  );
}
