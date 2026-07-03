"use client";

import {
  Activity,
  CheckCircle2,
  Loader2,
  Network,
  PanelRightClose,
  PanelRightOpen,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

import { ActivityFeed } from "@/components/ActivityFeed";
import { AgentCard } from "@/components/AgentCard";
import { agentVisual } from "@/lib/agents";
import type { AgentPanelState, FeedItem } from "@/lib/types";

const COLLAPSE_KEY = "workflow-collapsed";

function statusText(agent: AgentPanelState): string {
  switch (agent.status) {
    case "working":
      return agent.activity ?? "Working…";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    default:
      return "Standing by";
  }
}

/** A single agent shown as an avatar in the collapsed rail. */
function RailAvatar({ agent }: { agent: AgentPanelState }) {
  const { icon: Icon, color } = agentVisual(agent.info.name);
  const working = agent.status === "working";

  return (
    <div className="group relative">
      <div
        className={`flex h-9 w-9 items-center justify-center rounded-lg transition-all ${
          working
            ? "ring-2 ring-accent ring-offset-2 ring-offset-panel"
            : agent.status === "idle"
              ? "opacity-45"
              : ""
        }`}
        style={{ backgroundColor: `${color}22`, color }}
      >
        <Icon size={16} />
      </div>

      {agent.status !== "idle" && (
        <span className="absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-panel">
          {working && <Loader2 size={11} className="animate-spin text-accent" />}
          {agent.status === "completed" && (
            <CheckCircle2 size={12} className="text-ok" />
          )}
          {agent.status === "failed" && <XCircle size={12} className="text-bad" />}
        </span>
      )}

      {/* Hover tooltip — keeps names/activity available while collapsed. */}
      <div className="pointer-events-none absolute right-full top-1/2 z-20 mr-2.5 hidden -translate-y-1/2 whitespace-nowrap rounded-lg border border-edge bg-panel-2 px-2.5 py-1.5 shadow-xl group-hover:block">
        <p className="text-xs font-semibold leading-tight">
          {agent.info.display_name}
        </p>
        <p className="mt-0.5 text-[11px] leading-tight text-ink-dim">
          {statusText(agent)}
        </p>
      </div>
    </div>
  );
}

/** Slim, always-visible status rail shown when the panel is collapsed. */
function CollapsedRail({
  agents,
  running,
  onExpand,
}: {
  agents: AgentPanelState[];
  running: boolean;
  onExpand: () => void;
}) {
  const total = agents.length;
  const done = agents.filter((a) => a.status === "completed").length;

  return (
    <div className="flex h-full flex-col items-center py-3">
      <button
        onClick={onExpand}
        title="Expand workflow"
        aria-label="Expand workflow"
        className="flex h-9 w-9 items-center justify-center rounded-lg border border-edge bg-panel text-ink-dim transition-colors hover:border-accent/50 hover:text-ink"
      >
        <PanelRightOpen size={16} />
      </button>

      {total > 0 && (
        <div className="mt-3 flex flex-col items-center gap-1">
          {running && (
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
          )}
          <span className="text-[10px] font-semibold tabular-nums text-ink-dim">
            {done}/{total}
          </span>
        </div>
      )}

      <div className="mt-3 flex flex-1 flex-col items-center gap-2.5 overflow-y-auto py-1">
        {agents.length === 0 ? (
          <Network size={16} className="mt-2 text-ink-dim/40" />
        ) : (
          agents.map((agent) => (
            <RailAvatar key={agent.info.name} agent={agent} />
          ))
        )}
      </div>
    </div>
  );
}

export function WorkflowPanel({
  agents,
  feed,
  running,
}: {
  agents: AgentPanelState[];
  feed: FeedItem[];
  running: boolean;
}) {
  const [collapsed, setCollapsed] = useState(false);

  // Restore the user's last choice once mounted (client only).
  useEffect(() => {
    setCollapsed(window.localStorage.getItem(COLLAPSE_KEY) === "1");
  }, []);

  const toggle = () => {
    setCollapsed((prev) => {
      const next = !prev;
      window.localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
      return next;
    });
  };

  return (
    <aside
      className={`relative hidden shrink-0 flex-col border-l border-edge bg-panel/50 transition-[width] duration-300 ease-in-out lg:flex ${
        collapsed ? "w-16" : "w-[380px] xl:w-[440px]"
      }`}
    >
      {collapsed ? (
        <CollapsedRail agents={agents} running={running} onExpand={toggle} />
      ) : (
        <>
          <div className="flex items-center justify-between border-b border-edge px-4 py-3">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <Network size={15} className="text-accent" />
              Agent Workflow
            </h2>
            <div className="flex items-center gap-2">
              {running && (
                <span className="flex items-center gap-1.5 rounded-full bg-accent/15 px-2.5 py-1 text-[11px] font-medium text-accent">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
                  Live
                </span>
              )}
              <button
                onClick={toggle}
                title="Collapse workflow"
                aria-label="Collapse workflow"
                className="flex h-7 w-7 items-center justify-center rounded-md text-ink-dim transition-colors hover:bg-panel-2 hover:text-ink"
              >
                <PanelRightClose size={16} />
              </button>
            </div>
          </div>

          <div className="max-h-[55%] overflow-y-auto p-4">
            {agents.length === 0 ? (
              <div className="rounded-xl border border-dashed border-edge p-6 text-center text-xs text-ink-dim">
                The agent team appears here once you submit an idea.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-2 xl:grid-cols-2">
                {agents.map((agent) => (
                  <AgentCard key={agent.info.name} agent={agent} />
                ))}
              </div>
            )}
          </div>

          <div className="flex min-h-0 flex-1 flex-col border-t border-edge">
            <h3 className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-ink-dim">
              <Activity size={13} />
              ACTIVITY
            </h3>
            <ActivityFeed feed={feed} />
          </div>
        </>
      )}
    </aside>
  );
}
