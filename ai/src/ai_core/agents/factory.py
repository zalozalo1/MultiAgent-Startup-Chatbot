"""Build runnable agents from YAML specs.

Specialists are standard LangChain 1.x tool-calling agents (`create_agent`),
each with its own model, system prompt and instrumented tools. The returned
object is a compiled LangGraph that the workflow invokes as a sub-agent.
"""

from langchain.agents import create_agent

from ai_core.agents.registry import AgentSpec
from ai_core.models.factory import get_chat_model
from ai_core.tools.registry import get_tools


def build_specialist_agent(spec: AgentSpec):
    model = get_chat_model(spec.config.model)
    tools = get_tools(spec.config.tools)
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=spec.config.system_prompt,
    )
