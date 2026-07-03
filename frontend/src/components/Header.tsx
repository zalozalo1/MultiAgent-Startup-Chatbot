"use client";

import { Radar, Sparkles } from "lucide-react";

export function Header({
  connected,
  running,
}: {
  connected: boolean;
  running: boolean;
}) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-edge bg-panel px-5">
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15 text-accent">
          <Sparkles size={17} />
        </div>
        <div>
          <h1 className="text-sm font-semibold leading-tight">
            Startup Research Assistant
          </h1>
          <p className="text-[11px] leading-tight text-ink-dim">
            Multi-agent business idea analysis
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs">
        {running && (
          <span className="flex items-center gap-1.5 text-accent">
            <Radar size={14} className="animate-pulse" />
            Research in progress
          </span>
        )}
        <span className="flex items-center gap-1.5 text-ink-dim">
          <span
            className={`h-2 w-2 rounded-full ${
              connected ? "bg-ok" : "bg-bad"
            }`}
          />
          {connected ? "Connected" : "Reconnecting…"}
        </span>
      </div>
    </header>
  );
}
