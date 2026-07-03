"""Public runner: turn a user message into a stream of AgentEvents.

This is the only surface the backend consumes. Everything LangGraph-specific
(stream modes, chunk shapes) stays behind this boundary.
"""

import logging
from typing import AsyncIterator

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from pydantic import ValidationError

from ai_core.schemas.events import AgentEvent

logger = logging.getLogger(__name__)

# Generous parent-graph budget: each supervisor->specialist round trip costs
# two supersteps; the real cap is the workflow's max_iterations.
GRAPH_RECURSION_LIMIT = 100


class ResearchWorkflowRunner:
    def __init__(self, graph: CompiledStateGraph):
        self._graph = graph

    async def astream(self, *, thread_id: str, message: str) -> AsyncIterator[AgentEvent]:
        """Run the workflow for one user message, yielding events as they happen.

        ``thread_id`` scopes short-term memory: reusing it continues the same
        conversation with all prior findings available to the supervisor.
        """
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": GRAPH_RECURSION_LIMIT,
        }
        payload = {"messages": [HumanMessage(content=message)]}

        async for chunk in self._graph.astream(payload, config=config, stream_mode="custom"):
            try:
                yield AgentEvent.model_validate(chunk)
            except ValidationError:
                logger.debug("Ignoring non-AgentEvent custom chunk: %r", chunk)
