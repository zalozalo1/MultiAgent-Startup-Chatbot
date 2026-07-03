"""Shared state flowing through the research workflow.

The checkpointer persists this state per conversation thread, so findings and
completed work survive across runs — follow-up questions reuse them instead
of re-running research.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


def merge_findings(current: dict[str, str] | None, new: dict[str, str] | None) -> dict[str, str]:
    return {**(current or {}), **(new or {})}


def add_unique(current: list[str] | None, new: list[str] | None) -> list[str]:
    merged = list(current or [])
    for item in new or []:
        if item not in merged:
            merged.append(item)
    return merged


class ResearchState(TypedDict, total=False):
    # Full conversation history (user + assistant turns).
    messages: Annotated[list[AnyMessage], add_messages]
    # The business idea being researched (first user message of the thread).
    idea: str
    # The latest user request (may be a follow-up about existing findings).
    request: str
    # Specialist name -> markdown findings, accumulated across the run.
    findings: Annotated[dict[str, str], merge_findings]
    # Specialists that have reported back (or failed) this thread.
    completed_agents: Annotated[list[str], add_unique]
    # Task brief the supervisor assigned to the agent currently running.
    current_task: str
    # Supervisor loop counter for the active run (reset by the intake node).
    iteration: int
    # Final report produced by the finalizer.
    report: str
