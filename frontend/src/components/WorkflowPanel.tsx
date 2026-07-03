"use client";

import { Activity, Network } from "lucide-react";

import { ActivityFeed } from "@/components/ActivityFeed";
import { AgentCard } from "@/components/AgentCard";
import type { AgentPanelState, FeedItem } from "@/lib/types";

export function WorkflowPanel({
  agents,
  feed,
  running,
}: {
  agents: AgentPanelState[];
  feed: FeedItem[];
  running: boolean;
}) {
  return (
    <aside className="hidden w-[380px] shrink-0 flex-col border-l border-edge bg-panel/50 lg:flex xl:w-[440px]">
      <div className="flex items-center justify-between border-b border-edge px-4 py-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Network size={15} className="text-accent" />
          Agent Workflow
        </h2>
        {running && (
          <span className="flex items-center gap-1.5 rounded-full bg-accent/15 px-2.5 py-1 text-[11px] font-medium text-accent">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
            Live
          </span>
        )}
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
    </aside>
  );
}
