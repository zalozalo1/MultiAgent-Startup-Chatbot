// Wire types mirroring the backend's AgentEvent schema (ai_core.schemas.events)

export type AgentEventType =
  | "workflow_started"
  | "agent_started"
  | "agent_completed"
  | "agent_failed"
  | "handoff"
  | "tool_started"
  | "tool_completed"
  | "tool_failed"
  | "token"
  | "message"
  | "run_started"
  | "run_completed"
  | "run_failed"
  | "run_cancelled";

export interface AgentInfo {
  name: string;
  display_name: string;
  description: string;
  tools: string[];
}

export interface AgentEvent {
  type: AgentEventType;
  agent?: string;
  task?: string;
  from_agent?: string;
  to_agent?: string;
  reasoning?: string;
  tool?: string;
  tool_input?: string;
  output_preview?: string;
  summary?: string;
  content?: string;
  error?: string;
  agents?: AgentInfo[];
  timestamp?: string;
  run_id?: string;
}

// UI state

export type AgentStatus = "idle" | "working" | "completed" | "failed";

export interface AgentPanelState {
  info: AgentInfo;
  status: AgentStatus;
  /** Task brief assigned by the supervisor. */
  currentTask?: string;
  /** What the agent is doing right now (e.g. "Searching the web…"). */
  activity?: string;
  toolsUsed: string[];
  summary?: string;
  error?: string;
}

export interface FeedItem {
  id: number;
  event: AgentEvent;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

// REST types

export interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: { id: string; role: string; content: string; created_at: string }[];
}
