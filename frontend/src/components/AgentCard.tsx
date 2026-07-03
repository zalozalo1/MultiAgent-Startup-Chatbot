"use client";

import { CheckCircle2, Loader2, Wrench, XCircle } from "lucide-react";

import { agentVisual } from "@/lib/agents";
import type { AgentPanelState } from "@/lib/types";

export function AgentCard({ agent }: { agent: AgentPanelState }) {
  const { icon: Icon, color } = agentVisual(agent.info.name);
  const working = agent.status === "working";

  return (
    <div
      className={`rounded-xl border p-3 transition-all ${
        working
          ? "border-accent/60 bg-panel-2 shadow-[0_0_18px_-6px] shadow-accent/40"
          : agent.status === "completed"
            ? "border-edge bg-panel"
            : agent.status === "failed"
              ? "border-bad/40 bg-panel"
              : "border-edge bg-panel opacity-65"
      }`}
    >
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${color}22`, color }}
        >
          <Icon size={16} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-semibold leading-tight">
            {agent.info.display_name}
          </p>
          <p className="truncate text-[11px] text-ink-dim">
            {working
              ? (agent.activity ?? "Working…")
              : agent.status === "completed"
                ? "Completed"
                : agent.status === "failed"
                  ? "Failed"
                  : "Standing by"}
          </p>
        </div>
        <span className="shrink-0">
          {working && (
            <Loader2 size={15} className="animate-spin text-accent" />
          )}
          {agent.status === "completed" && (
            <CheckCircle2 size={15} className="text-ok" />
          )}
          {agent.status === "failed" && (
            <XCircle size={15} className="text-bad" />
          )}
        </span>
      </div>

      {working && agent.currentTask && (
        <p className="mt-2 line-clamp-3 rounded-md bg-surface/60 px-2 py-1.5 text-[11px] leading-snug text-ink-dim">
          <span className="font-medium text-ink">Task:</span>{" "}
          {agent.currentTask}
        </p>
      )}

      {agent.status === "completed" && agent.summary && (
        <p className="mt-2 line-clamp-2 text-[11px] leading-snug text-ink-dim">
          {agent.summary}
        </p>
      )}

      {agent.status === "failed" && agent.error && (
        <p className="mt-2 line-clamp-2 text-[11px] leading-snug text-bad">
          {agent.error}
        </p>
      )}

      {agent.toolsUsed.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {agent.toolsUsed.map((tool) => (
            <span
              key={tool}
              className="flex items-center gap-1 rounded-full border border-edge bg-surface/60 px-2 py-0.5 text-[10px] text-ink-dim"
            >
              <Wrench size={9} />
              {tool}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
