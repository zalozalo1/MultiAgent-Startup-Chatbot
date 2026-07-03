"""Typed events emitted by the workflow while it runs.

Every node and tool reports progress as an AgentEvent. The backend forwards
these over WebSocket to the frontend, which renders the live agent timeline.
The schema is intentionally flat so it serializes to simple JSON.
"""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class EventType(StrEnum):
    # Emitted by the graph
    WORKFLOW_STARTED = "workflow_started"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    HANDOFF = "handoff"
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"
    TOKEN = "token"
    MESSAGE = "message"
    # Emitted by the backend around a run
    RUN_STARTED = "run_started"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"


class AgentInfo(BaseModel):
    """Static metadata about an agent, sent once at workflow start so the UI
    can render the full roster before any agent has run."""

    name: str
    display_name: str
    description: str
    tools: list[str] = []


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentEvent(BaseModel):
    type: EventType
    agent: str | None = None
    task: str | None = None
    from_agent: str | None = None
    to_agent: str | None = None
    reasoning: str | None = None
    tool: str | None = None
    tool_input: str | None = None
    output_preview: str | None = None
    summary: str | None = None
    content: str | None = None
    error: str | None = None
    agents: list[AgentInfo] | None = None
    timestamp: datetime = Field(default_factory=_utcnow)

    def to_wire(self) -> dict:
        """JSON-safe dict with None fields dropped — the WebSocket payload."""
        return self.model_dump(mode="json", exclude_none=True)
