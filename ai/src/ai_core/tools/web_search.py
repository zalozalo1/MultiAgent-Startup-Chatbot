"""Web search tool.

Uses Tavily when an API key is configured (higher quality, built for LLMs),
otherwise falls back to DuckDuckGo via ``ddgs`` which needs no API key, so the
project works out of the box.
"""

import asyncio
import logging

from langchain_core.tools import StructuredTool

from ai_core.config import get_settings

logger = logging.getLogger(__name__)


def _format_results(results: list[dict]) -> str:
    if not results:
        return "No results found. Try a different query."
    lines = []
    for i, r in enumerate(results, start=1):
        title = r.get("title") or "Untitled"
        url = r.get("href") or r.get("url") or ""
        body = (r.get("body") or r.get("content") or "").strip()
        lines.append(f"{i}. {title}\n   URL: {url}\n   {body}")
    return "\n\n".join(lines)


def _duckduckgo_search(query: str, max_results: int) -> list[dict]:
    from ddgs import DDGS

    with DDGS() as ddg:
        return list(ddg.text(query, max_results=max_results))


async def _tavily_search(query: str, max_results: int) -> list[dict]:
    from langchain_tavily import TavilySearch

    tavily = TavilySearch(max_results=max_results)
    response = await tavily.ainvoke({"query": query})
    if isinstance(response, dict):
        return response.get("results", [])
    return []


async def web_search(query: str) -> str:
    """Search the web for current information: market data, trends,
    competitors, pricing, news and statistics. Input should be a focused
    search query."""
    settings = get_settings()
    use_tavily = settings.search_provider == "tavily" or (
        settings.search_provider == "auto" and settings.tavily_api_key
    )
    try:
        if use_tavily:
            results = await _tavily_search(query, settings.max_search_results)
        else:
            results = await asyncio.to_thread(
                _duckduckgo_search, query, settings.max_search_results
            )
        return _format_results(results)
    except Exception as exc:  # never crash an agent because search hiccuped
        logger.warning("web_search failed for %r: %s", query, exc)
        return f"Search failed ({exc}). Proceed with your own knowledge and note the limitation."


def make_web_search_tool() -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=web_search,
        name="web_search",
        description=(
            "Search the web for current information: market data, trends, "
            "competitors, pricing, news and statistics. "
            "Input should be a focused search query."
        ),
    )
