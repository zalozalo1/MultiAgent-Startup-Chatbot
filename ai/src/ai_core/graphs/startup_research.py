"""Startup research workflow graph.

Topology (wiring comes from prompts/workflows/startup_research.yaml):

    START -> intake -> supervisor <-> [specialists...] -> report_writer -> END

The supervisor dispatches one specialist at a time via Command(goto=...),
reviews what comes back, and eventually routes to the finalizer, which writes
the final report (or answers a follow-up question from existing findings).
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_core.agents.factory import build_specialist_agent
from ai_core.agents.registry import load_agent_spec
from ai_core.graphs.nodes import (
    make_finalizer_node,
    make_intake_node,
    make_specialist_node,
    make_supervisor_node,
)
from ai_core.graphs.state import ResearchState
from ai_core.prompts.loader import load_workflow_config


def build_startup_research_graph(
    checkpointer: BaseCheckpointSaver | None = None,
    workflow_name: str = "startup_research",
) -> CompiledStateGraph:
    workflow = load_workflow_config(workflow_name)

    supervisor_spec = load_agent_spec(workflow.supervisor)
    finalizer_spec = load_agent_spec(workflow.finalizer)
    specialist_specs = {name: load_agent_spec(name) for name in workflow.specialists}
    specialist_agents = {
        name: build_specialist_agent(spec) for name, spec in specialist_specs.items()
    }

    builder = StateGraph(ResearchState)
    builder.add_node(
        "intake",
        make_intake_node(workflow, supervisor_spec, specialist_specs, finalizer_spec),
    )
    builder.add_node(
        workflow.supervisor,
        make_supervisor_node(workflow, supervisor_spec, specialist_specs),
        destinations=(*workflow.specialists, workflow.finalizer),
    )
    for name, spec in specialist_specs.items():
        builder.add_node(
            name,
            make_specialist_node(spec, specialist_agents[name], workflow),
            destinations=(workflow.supervisor,),
        )
    builder.add_node(workflow.finalizer, make_finalizer_node(finalizer_spec, workflow))

    builder.add_edge(START, "intake")
    builder.add_edge("intake", workflow.supervisor)
    builder.add_edge(workflow.finalizer, END)

    return builder.compile(checkpointer=checkpointer)
