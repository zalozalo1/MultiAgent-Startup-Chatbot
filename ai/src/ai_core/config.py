"""Configuration for the AI engine, read from environment variables / .env.

All knobs use the ``AI_`` prefix (e.g. ``AI_MODEL=openai:gpt-5-mini``) except
provider API keys, which follow each provider's own convention
(``OPENAI_API_KEY``, ``ANTHROPIC_API_KEY``, ``OPENROUTER_API_KEY``,
``TAVILY_API_KEY``).
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to ai/.env so config resolves the same no matter which
# directory the app is launched from. ``load_dotenv`` populates os.environ,
# which is how provider SDKs (GOOGLE_API_KEY, OPENAI_API_KEY, ...) find their
# keys — pydantic-settings alone only reads declared fields, not the SDK keys.
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_",
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Default chat model. Direct LangChain providers use "provider:model",
    # e.g. "openai:gpt-5-mini". OpenRouter uses
    # "openrouter:provider/model", e.g. "openrouter:openai/gpt-5-mini".
    # Per-agent overrides live in the agent YAML files under prompts/agents/.
    model: str = "google_genai:gemini-2.5-flash"

    # Short-term memory (LangGraph checkpointer). "memory" keeps thread state
    # in-process; "postgres" persists it across restarts.
    checkpointer: Literal["memory", "postgres"] = "memory"
    checkpointer_postgres_url: str | None = None

    # Web search: "auto" uses Tavily when TAVILY_API_KEY is set, otherwise
    # falls back to DuckDuckGo (no key required).
    search_provider: Literal["auto", "duckduckgo", "tavily"] = "auto"
    max_search_results: int = 6

    tavily_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TAVILY_API_KEY", "AI_TAVILY_API_KEY"),
    )
    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "AI_OPENROUTER_API_KEY"),
    )

    # Safety valve for the per-specialist ReAct loop.
    agent_recursion_limit: int = 25


@lru_cache
def get_settings() -> AISettings:
    return AISettings()
