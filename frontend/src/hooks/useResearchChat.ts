"use client";

// WebSocket-driven chat + live workflow state. One hook instance per
// conversation; every AgentEvent from the backend flows through the reducer.

import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { fetchConversation, wsUrl } from "@/lib/api";
import type {
  AgentEvent,
  AgentPanelState,
  ChatMessage,
  FeedItem,
} from "@/lib/types";

interface ChatState {
  messages: ChatMessage[];
  agents: AgentPanelState[];
  feed: FeedItem[];
  running: boolean;
  error: string | null;
  seq: number;
}

const INITIAL: ChatState = {
  messages: [],
  agents: [],
  feed: [],
  running: false,
  error: null,
  seq: 0,
};

type Action =
  | { kind: "event"; event: AgentEvent }
  | { kind: "user_message"; content: string }
  | { kind: "load_messages"; messages: ChatMessage[] }
  | { kind: "reset" };

const FEED_EVENTS = new Set([
  "run_started",
  "workflow_started",
  "agent_completed",
  "agent_failed",
  "handoff",
  "tool_started",
  "tool_completed",
  "tool_failed",
  "run_completed",
  "run_failed",
  "run_cancelled",
]);

function patchAgent(
  agents: AgentPanelState[],
  name: string | undefined,
  patch: (agent: AgentPanelState) => AgentPanelState,
): AgentPanelState[] {
  if (!name) return agents;
  return agents.map((a) => (a.info.name === name ? patch(a) : a));
}

function applyEvent(state: ChatState, event: AgentEvent): ChatState {
  const next = { ...state };

  if (FEED_EVENTS.has(event.type)) {
    next.seq += 1;
    next.feed = [...next.feed, { id: next.seq, event }];
  }

  switch (event.type) {
    case "run_started":
      next.running = true;
      next.error = null;
      next.feed = next.feed.slice(-1); // fresh feed per run
      next.agents = next.agents.map((a) => ({
        info: a.info,
        status: "idle",
        toolsUsed: [],
      }));
      break;

    case "workflow_started":
      if (event.agents?.length) {
        next.agents = event.agents.map((info) => ({
          info,
          status: "idle",
          toolsUsed: [],
        }));
      }
      break;

    case "agent_started":
      next.agents = patchAgent(next.agents, event.agent, (a) => ({
        ...a,
        status: "working",
        currentTask: event.task,
        activity: "Thinking…",
        summary: undefined,
        error: undefined,
      }));
      break;

    case "tool_started":
      next.agents = patchAgent(next.agents, event.agent, (a) => ({
        ...a,
        activity: `Using ${event.tool}…`,
        toolsUsed: a.toolsUsed.includes(event.tool ?? "")
          ? a.toolsUsed
          : [...a.toolsUsed, event.tool ?? ""],
      }));
      break;

    case "tool_completed":
    case "tool_failed":
      next.agents = patchAgent(next.agents, event.agent, (a) => ({
        ...a,
        activity: "Analyzing results…",
      }));
      break;

    case "agent_completed":
      next.agents = patchAgent(next.agents, event.agent, (a) => ({
        ...a,
        status: "completed",
        activity: undefined,
        summary: event.summary,
      }));
      break;

    case "agent_failed":
      next.agents = patchAgent(next.agents, event.agent, (a) => ({
        ...a,
        status: "failed",
        activity: undefined,
        error: event.error,
      }));
      break;

    case "token": {
      const messages = [...next.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === "assistant" && last.streaming) {
        messages[messages.length - 1] = {
          ...last,
          content: last.content + (event.content ?? ""),
        };
      } else {
        messages.push({
          id: `stream-${Date.now()}`,
          role: "assistant",
          content: event.content ?? "",
          streaming: true,
        });
      }
      next.messages = messages;
      break;
    }

    case "message": {
      const messages = [...next.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === "assistant" && last.streaming) {
        messages[messages.length - 1] = {
          ...last,
          content: event.content ?? last.content,
          streaming: false,
        };
      } else if (event.content) {
        messages.push({
          id: `msg-${Date.now()}`,
          role: "assistant",
          content: event.content,
        });
      }
      next.messages = messages;
      break;
    }

    case "run_completed":
      next.running = false;
      break;

    case "run_failed": {
      next.running = false;
      next.error = event.error ?? "The research run failed.";
      // An agent mid-flight when the run died is what failed.
      next.agents = next.agents.map((a) =>
        a.status === "working"
          ? { ...a, status: "failed", activity: undefined, error: event.error }
          : a,
      );
      const messages = [...next.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === "assistant" && last.streaming) {
        messages[messages.length - 1] = { ...last, streaming: false };
        next.messages = messages;
      }
      break;
    }

    case "run_cancelled": {
      next.running = false;
      next.error = null;
      next.agents = next.agents.map((a) =>
        a.status === "working"
          ? { ...a, status: "idle", activity: undefined, error: undefined }
          : a,
      );
      const messages = [...next.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === "assistant" && last.streaming) {
        messages[messages.length - 1] = { ...last, streaming: false };
        next.messages = messages;
      }
      break;
    }
  }

  return next;
}

function reducer(state: ChatState, action: Action): ChatState {
  switch (action.kind) {
    case "event":
      return applyEvent(state, action.event);
    case "user_message":
      return {
        ...state,
        error: null,
        messages: [
          ...state.messages,
          { id: `user-${Date.now()}`, role: "user", content: action.content },
        ],
      };
    case "load_messages":
      return { ...state, messages: action.messages };
    case "reset":
      return INITIAL;
  }
}

export function useResearchChat(conversationId: string) {
  const [state, dispatch] = useReducer(reducer, INITIAL);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    dispatch({ kind: "reset" });
    let disposed = false;
    let retryTimer: number | undefined;

    const connect = () => {
      const socket = new WebSocket(wsUrl(conversationId));
      socketRef.current = socket;
      socket.onopen = () => setConnected(true);
      socket.onmessage = (e) => {
        try {
          dispatch({ kind: "event", event: JSON.parse(e.data) as AgentEvent });
        } catch {
          // ignore malformed frames
        }
      };
      socket.onclose = () => {
        setConnected(false);
        if (!disposed) retryTimer = window.setTimeout(connect, 2000);
      };
    };
    connect();

    // Load persisted history when reopening an existing conversation.
    fetchConversation(conversationId).then((detail) => {
      if (disposed || !detail) return;
      dispatch({
        kind: "load_messages",
        messages: detail.messages
          .filter((m) => m.role === "user" || m.role === "assistant")
          .map((m) => ({
            id: m.id,
            role: m.role as "user" | "assistant",
            content: m.content,
          })),
      });
    });

    return () => {
      disposed = true;
      window.clearTimeout(retryTimer);
      socketRef.current?.close();
    };
  }, [conversationId]);

  const sendMessage = useCallback((content: string): boolean => {
    const socket = socketRef.current;
    const trimmed = content.trim();
    if (!trimmed || !socket || socket.readyState !== WebSocket.OPEN) return false;
    dispatch({ kind: "user_message", content: trimmed });
    socket.send(JSON.stringify({ type: "chat", content: trimmed }));
    return true;
  }, []);

  const stopRun = useCallback((): boolean => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify({ type: "stop" }));
    return true;
  }, []);

  return { ...state, connected, sendMessage, stopRun };
}
