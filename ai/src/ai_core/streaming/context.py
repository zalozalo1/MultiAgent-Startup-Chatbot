"""Event emission plumbing.

Graph nodes run inside the LangGraph runtime, where ``get_stream_writer()``
gives direct access to the ``custom`` stream. Tools, however, execute inside a
*nested* agent invocation (create_agent subgraph), where the parent stream
writer is not reliably reachable. To keep tool events flowing to the same
stream, each node binds the parent writer and its agent name into context
variables before invoking its agent; tools then emit through this module
without knowing anything about the graph.
"""

import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Iterator

from langgraph.config import get_stream_writer

from ai_core.schemas.events import AgentEvent, EventType

logger = logging.getLogger(__name__)

_sink: ContextVar[Callable[[dict], None] | None] = ContextVar("ai_event_sink", default=None)
_agent: ContextVar[str | None] = ContextVar("ai_current_agent", default=None)


@contextmanager
def agent_event_scope(agent_name: str, writer: Callable[[dict], None]) -> Iterator[None]:
    """Bind the active agent name and stream writer for the current task tree."""
    sink_token = _sink.set(writer)
    agent_token = _agent.set(agent_name)
    try:
        yield
    finally:
        _sink.reset(sink_token)
        _agent.reset(agent_token)


def _resolve_writer() -> Callable[[dict], None] | None:
    writer = _sink.get()
    if writer is not None:
        return writer
    try:
        return get_stream_writer()
    except Exception:  # outside a LangGraph runtime (e.g. unit tests)
        return None


def emit(event: AgentEvent) -> None:
    writer = _resolve_writer()
    if writer is None:
        logger.debug("No stream writer available, dropping event: %s", event.type)
        return
    writer(event.to_wire())


def _preview(value: Any, limit: int = 300) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except TypeError:
            text = str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def emit_tool_started(tool: str, tool_input: Any) -> None:
    emit(
        AgentEvent(
            type=EventType.TOOL_STARTED,
            agent=_agent.get(),
            tool=tool,
            tool_input=_preview(tool_input, 200),
        )
    )


def emit_tool_completed(tool: str, output: Any) -> None:
    emit(
        AgentEvent(
            type=EventType.TOOL_COMPLETED,
            agent=_agent.get(),
            tool=tool,
            output_preview=_preview(output),
        )
    )


def emit_tool_failed(tool: str, error: Exception) -> None:
    emit(
        AgentEvent(
            type=EventType.TOOL_FAILED,
            agent=_agent.get(),
            tool=tool,
            error=_preview(str(error), 300),
        )
    )
