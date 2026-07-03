"use client";

import {
  ArrowRight,
  CheckCircle2,
  Flag,
  Play,
  Users,
  Wrench,
  XCircle,
} from "lucide-react";
import { useEffect, useRef, type ReactNode } from "react";

import { agentLabel, agentVisual } from "@/lib/agents";
import type { AgentEvent, FeedItem } from "@/lib/types";

function AgentChip({ name }: { name?: string }) {
  const { color } = agentVisual(name);
  return (
    <span
      className="rounded px-1 py-px text-[10px] font-medium"
      style={{ backgroundColor: `${color}22`, color }}
    >
      {agentLabel(name)}
    </span>
  );
}

function describe(event: AgentEvent): { icon: ReactNode; body: ReactNode } | null {
  switch (event.type) {
    case "run_started":
      return {
        icon: <Play size={12} className="text-accent" />,
        body: <span>Research run started</span>,
      };
    case "workflow_started":
      return {
        icon: <Users size={12} className="text-accent" />,
        body: <span>Team assembled — {event.agents?.length ?? 0} agents</span>,
      };
    case "handoff":
      return {
        icon: <ArrowRight size={12} className="text-ink-dim" />,
        body: (
          <span>
            <AgentChip name={event.from_agent} />{" "}
            <span className="text-ink-dim">→</span>{" "}
            <AgentChip name={event.to_agent} />
            {event.task && <span className="text-ink-dim"> — {event.task}</span>}
          </span>
        ),
      };
    case "tool_started":
      return {
        icon: <Wrench size={12} className="text-warn" />,
        body: (
          <span>
            <AgentChip name={event.agent} />{" "}
            <span className="text-ink-dim">
              running <span className="font-mono text-[10.5px]">{event.tool}</span>
              {event.tool_input && ` ${event.tool_input}`}
            </span>
          </span>
        ),
      };
    case "tool_completed":
      return {
        icon: <CheckCircle2 size={12} className="text-ok/70" />,
        body: (
          <span className="text-ink-dim">
            <span className="font-mono text-[10.5px]">{event.tool}</span> finished
          </span>
        ),
      };
    case "tool_failed":
      return {
        icon: <XCircle size={12} className="text-bad" />,
        body: (
          <span className="text-bad">
            <span className="font-mono text-[10.5px]">{event.tool}</span> failed
            {event.error && ` — ${event.error}`}
          </span>
        ),
      };
    case "agent_completed":
      return {
        icon: <CheckCircle2 size={12} className="text-ok" />,
        body: (
          <span>
            <AgentChip name={event.agent} />{" "}
            <span className="text-ink-dim">
              done{event.summary ? ` — ${event.summary}` : ""}
            </span>
          </span>
        ),
      };
    case "agent_failed":
      return {
        icon: <XCircle size={12} className="text-bad" />,
        body: (
          <span>
            <AgentChip name={event.agent} />{" "}
            <span className="text-bad">failed{event.error ? ` — ${event.error}` : ""}</span>
          </span>
        ),
      };
    case "run_completed":
      return {
        icon: <Flag size={12} className="text-ok" />,
        body: <span className="text-ok">Research complete</span>,
      };
    case "run_failed":
      return {
        icon: <XCircle size={12} className="text-bad" />,
        body: <span className="text-bad">Run failed{event.error ? ` — ${event.error}` : ""}</span>,
      };
    case "run_cancelled":
      return {
        icon: <XCircle size={12} className="text-ink-dim" />,
        body: <span className="text-ink-dim">Research stopped</span>,
      };
    default:
      return null;
  }
}

function time(event: AgentEvent): string {
  if (!event.timestamp) return "";
  try {
    return new Date(event.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

export function ActivityFeed({ feed }: { feed: FeedItem[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [feed]);

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 pb-4">
      {feed.length === 0 ? (
        <p className="pt-2 text-xs text-ink-dim">
          Agent activity will stream here during a run.
        </p>
      ) : (
        <ul className="space-y-1.5">
          {feed.map((item) => {
            const rendered = describe(item.event);
            if (!rendered) return null;
            return (
              <li
                key={item.id}
                className="flex items-start gap-2 text-xs leading-snug"
              >
                <span className="mt-0.5 w-14 shrink-0 font-mono text-[10px] text-ink-dim/60">
                  {time(item.event)}
                </span>
                <span className="mt-0.5 shrink-0">{rendered.icon}</span>
                <span className="min-w-0 break-words [overflow-wrap:anywhere]">
                  {rendered.body}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
