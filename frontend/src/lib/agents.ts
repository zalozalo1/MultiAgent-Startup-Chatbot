// Visual identity for agents. Purely presentational — the authoritative
// roster (names, descriptions, tools) arrives at runtime via the
// workflow_started event, so new agents added in YAML show up automatically
// (with the fallback style until given one here).

import {
  Bot,
  Compass,
  FileText,
  Lightbulb,
  Megaphone,
  ShieldAlert,
  Swords,
  TrendingUp,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface AgentVisual {
  icon: LucideIcon;
  color: string;
}

const VISUALS: Record<string, AgentVisual> = {
  supervisor: { icon: Compass, color: "#a78bfa" },
  market_research: { icon: TrendingUp, color: "#38bdf8" },
  competitor_analysis: { icon: Swords, color: "#f472b6" },
  customer_research: { icon: Users, color: "#34d399" },
  product_strategy: { icon: Lightbulb, color: "#fbbf24" },
  risk_analysis: { icon: ShieldAlert, color: "#f87171" },
  marketing_strategy: { icon: Megaphone, color: "#fb923c" },
  report_writer: { icon: FileText, color: "#818cf8" },
};

const FALLBACK: AgentVisual = { icon: Bot, color: "#94a3b8" };

export function agentVisual(name: string | undefined): AgentVisual {
  return (name && VISUALS[name]) || FALLBACK;
}

export function agentLabel(name: string | undefined): string {
  if (!name) return "Agent";
  return name
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
