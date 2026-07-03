"""ai_core — multi-agent startup research engine.

Public API:
    build_startup_research_graph  — compile the LangGraph workflow
    ResearchWorkflowRunner        — stream AgentEvents for a user message
    create_checkpointer           — async context manager for short-term memory
    AgentEvent / EventType        — typed events emitted during a run
    get_settings                  — AI engine configuration
"""

from ai_core.config import get_settings
from ai_core.graphs.startup_research import build_startup_research_graph
from ai_core.memory.checkpointer import create_checkpointer
from ai_core.schemas.events import AgentEvent, AgentInfo, EventType
from ai_core.workflow import ResearchWorkflowRunner

__version__ = "0.1.0"

__all__ = [
    "AgentEvent",
    "AgentInfo",
    "EventType",
    "ResearchWorkflowRunner",
    "build_startup_research_graph",
    "create_checkpointer",
    "get_settings",
    "__version__",
]
