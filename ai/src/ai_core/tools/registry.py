"""Tool registry with event instrumentation.

Agents reference tools by name in their YAML config. Every tool handed to an
agent is wrapped so it emits tool_started / tool_completed / tool_failed
events to the live stream — new tools get real-time UI visibility for free.

To add a tool: write a factory returning a StructuredTool (with an async
``coroutine``), then register it here or call ``register_tool`` at import time.
"""

import asyncio
from typing import Callable

from langchain_core.tools import StructuredTool

from ai_core.streaming.context import (
    emit_tool_completed,
    emit_tool_failed,
    emit_tool_started,
)
from ai_core.tools.calculator import make_calculator_tool
from ai_core.tools.web_search import make_web_search_tool

_FACTORIES: dict[str, Callable[[], StructuredTool]] = {
    "web_search": make_web_search_tool,
    "calculator": make_calculator_tool,
}


def register_tool(name: str, factory: Callable[[], StructuredTool]) -> None:
    _FACTORIES[name] = factory


def _instrument(tool: StructuredTool) -> StructuredTool:
    """Wrap a tool so every invocation is reported to the event stream."""
    run_async = tool.coroutine
    run_sync = tool.func

    async def traced(**kwargs) -> object:
        emit_tool_started(tool.name, kwargs)
        try:
            if run_async is not None:
                result = await run_async(**kwargs)
            else:
                result = await asyncio.to_thread(run_sync, **kwargs)
        except Exception as exc:
            emit_tool_failed(tool.name, exc)
            raise
        emit_tool_completed(tool.name, result)
        return result

    return StructuredTool(
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
        coroutine=traced,
    )


def get_tools(names: list[str]) -> list[StructuredTool]:
    tools = []
    for name in names:
        factory = _FACTORIES.get(name)
        if factory is None:
            known = ", ".join(sorted(_FACTORIES))
            raise KeyError(f"Unknown tool '{name}'. Registered tools: {known}")
        tools.append(_instrument(factory()))
    return tools
