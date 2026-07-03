"""Node factories for the startup research graph.

Each factory closes over the YAML-derived specs and returns an async node
function. Nodes communicate progress exclusively through AgentEvents on the
``custom`` stream — the backend and frontend never inspect raw graph state.
"""

import logging
from typing import Literal

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from langgraph.types import Command
from pydantic import BaseModel, Field, create_model

from ai_core.agents.registry import AgentSpec
from ai_core.config import get_settings
from ai_core.models.factory import get_chat_model
from ai_core.prompts.loader import WorkflowConfig, render
from ai_core.schemas.events import AgentEvent, EventType
from ai_core.streaming.context import agent_event_scope, emit

logger = logging.getLogger(__name__)

FINISH = "finish"

DEFAULT_TASK_PROMPT = """## Business idea
{idea}

## Your assigned task
{task}

## Findings from teammates so far
{context}

Complete your assigned task now. Return only your final findings in markdown.
"""


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _text(content: object) -> str:
    """Normalize message content (str or content-block list) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content)


def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _findings_digest(findings: dict[str, str], each: int = 400) -> str:
    if not findings:
        return "(none yet)"
    return "\n\n".join(f"### {name}\n{_truncate(text, each)}" for name, text in findings.items())


def _findings_full(findings: dict[str, str]) -> str:
    if not findings:
        return "(no research findings for this conversation)"
    return "\n\n".join(f"## Findings: {name}\n{text.strip()}" for name, text in findings.items())


def _conversation_digest(messages: list[AnyMessage], keep: int = 8) -> str:
    lines: list[str] = []
    for msg in messages[-keep:]:
        role = "User" if msg.type == "human" else "Assistant" if msg.type == "ai" else None
        if role is None:
            continue
        text = _text(msg.content)
        if text:
            lines.append(f"{role}: {_truncate(text, 600)}")
    return "\n".join(lines) or "(start of conversation)"


def _first_human_text(messages: list[AnyMessage]) -> str:
    for msg in messages:
        if msg.type == "human":
            return _text(msg.content)
    return ""


def _last_human_text(messages: list[AnyMessage]) -> str:
    for msg in reversed(messages):
        if msg.type == "human":
            return _text(msg.content)
    return ""


def _build_route_model(options: list[str]) -> type[BaseModel]:
    """Routing schema with the allowed agents baked in as a Literal, so the
    LLM structurally cannot pick a nonexistent agent."""
    return create_model(
        "RouteDecision",
        next_agent=(
            Literal[tuple(options)],  # type: ignore[valid-type]
            Field(description="The specialist to dispatch next, or 'finish' to write the final answer."),
        ),
        task=(
            str,
            Field(description="Concrete, specific task brief for the chosen specialist (1-3 sentences)."),
        ),
        reasoning=(
            str,
            Field(description="One sentence explaining this routing decision."),
        ),
    )


# --------------------------------------------------------------------------
# node factories
# --------------------------------------------------------------------------

def make_intake_node(
    workflow: WorkflowConfig,
    supervisor_spec: AgentSpec,
    specialist_specs: dict[str, AgentSpec],
    finalizer_spec: AgentSpec,
):
    roster = [supervisor_spec.info, *(s.info for s in specialist_specs.values()), finalizer_spec.info]

    async def intake(state: dict) -> dict:
        messages = state.get("messages", [])
        emit(AgentEvent(type=EventType.WORKFLOW_STARTED, agents=roster))
        return {
            "idea": _first_human_text(messages),
            "request": _last_human_text(messages),
            "iteration": 0,
            "current_task": "",
        }

    return intake


def make_supervisor_node(
    workflow: WorkflowConfig,
    spec: AgentSpec,
    specialist_specs: dict[str, AgentSpec],
):
    name = spec.name
    options = [*workflow.specialists, FINISH]
    route_model = _build_route_model(options)

    def _roster_text(completed: list[str]) -> str:
        lines = []
        for s in specialist_specs.values():
            status = "completed" if s.name in completed else "available"
            lines.append(f"- {s.name} — {s.config.description} [{status}]")
        return "\n".join(lines)

    async def supervisor(state: dict) -> Command:
        writer = get_stream_writer()
        iteration = state.get("iteration", 0)
        completed = state.get("completed_agents", [])
        findings = state.get("findings", {})

        with agent_event_scope(name, writer):
            emit(AgentEvent(
                type=EventType.AGENT_STARTED,
                agent=name,
                task="Reviewing progress and planning the next step",
            ))

            if iteration >= workflow.max_iterations:
                next_agent = FINISH
                task = "Compile the final answer from the findings gathered so far."
                reasoning = f"Iteration budget ({workflow.max_iterations}) exhausted."
            else:
                human = render(
                    spec.config.task_prompt or "",
                    idea=state.get("idea", ""),
                    request=state.get("request", ""),
                    conversation=_conversation_digest(state.get("messages", [])),
                    roster=_roster_text(completed),
                    findings_digest=_findings_digest(findings),
                    completed=", ".join(completed) or "(none)",
                    iteration=iteration + 1,
                    max_iterations=workflow.max_iterations,
                )
                try:
                    model = get_chat_model(spec.config.model).with_structured_output(route_model)
                    decision = await model.ainvoke(
                        [SystemMessage(content=spec.config.system_prompt), HumanMessage(content=human)]
                    )
                    next_agent = decision.next_agent
                    task = decision.task
                    reasoning = decision.reasoning
                except Exception as exc:
                    logger.exception("Supervisor routing failed, using fallback")
                    remaining = [s for s in workflow.specialists if s not in completed]
                    next_agent = remaining[0] if remaining else FINISH
                    task = (
                        specialist_specs[next_agent].config.description
                        if next_agent != FINISH
                        else "Compile the final answer from the findings gathered so far."
                    )
                    reasoning = f"Fallback routing after supervisor error: {_truncate(str(exc), 200)}"

            goto = workflow.finalizer if next_agent == FINISH else next_agent
            emit(AgentEvent(type=EventType.AGENT_COMPLETED, agent=name, summary=reasoning))
            emit(AgentEvent(
                type=EventType.HANDOFF,
                from_agent=name,
                to_agent=goto,
                task=task,
                reasoning=reasoning,
            ))

        return Command(goto=goto, update={"current_task": task, "iteration": iteration + 1})

    return supervisor


def make_specialist_node(spec: AgentSpec, agent, workflow: WorkflowConfig):
    name = spec.name

    async def specialist(state: dict) -> Command:
        writer = get_stream_writer()
        settings = get_settings()
        task = state.get("current_task") or spec.config.description

        with agent_event_scope(name, writer):
            emit(AgentEvent(type=EventType.AGENT_STARTED, agent=name, task=task))
            prompt = render(
                spec.config.task_prompt or DEFAULT_TASK_PROMPT,
                idea=state.get("idea", ""),
                task=task,
                context=_findings_digest(state.get("findings", {})),
            )
            try:
                result = await agent.ainvoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    config={"recursion_limit": settings.agent_recursion_limit},
                )
                findings_text = _text(result["messages"][-1].content).strip()
                emit(AgentEvent(
                    type=EventType.AGENT_COMPLETED,
                    agent=name,
                    summary=_truncate(findings_text, 400),
                ))
                update = {"findings": {name: findings_text}, "completed_agents": [name]}
            except Exception as exc:
                logger.exception("Specialist %s failed", name)
                emit(AgentEvent(type=EventType.AGENT_FAILED, agent=name, error=_truncate(str(exc), 300)))
                # Record the failure so the supervisor doesn't loop on this agent.
                update = {
                    "findings": {name: f"[{name} could not complete its task: {_truncate(str(exc), 200)}]"},
                    "completed_agents": [name],
                }

        return Command(goto=workflow.supervisor, update=update)

    return specialist


def make_finalizer_node(spec: AgentSpec, workflow: WorkflowConfig):
    name = spec.name

    async def finalizer(state: dict) -> dict:
        writer = get_stream_writer()

        with agent_event_scope(name, writer):
            emit(AgentEvent(
                type=EventType.AGENT_STARTED,
                agent=name,
                task="Writing the final response",
            ))
            human = render(
                spec.config.task_prompt or "",
                idea=state.get("idea", ""),
                request=state.get("request", ""),
                conversation=_conversation_digest(state.get("messages", [])),
                findings=_findings_full(state.get("findings", {})),
            )
            model = get_chat_model(spec.config.model)
            chunks: list[str] = []
            async for chunk in model.astream(
                [SystemMessage(content=spec.config.system_prompt), HumanMessage(content=human)]
            ):
                text = _text(chunk.content)
                if text:
                    chunks.append(text)
                    emit(AgentEvent(type=EventType.TOKEN, agent=name, content=text))

            report = "".join(chunks).strip()
            emit(AgentEvent(type=EventType.AGENT_COMPLETED, agent=name, summary=_truncate(report, 300)))
            emit(AgentEvent(type=EventType.MESSAGE, agent=name, content=report))

        return {"messages": [AIMessage(content=report)], "report": report}

    return finalizer
