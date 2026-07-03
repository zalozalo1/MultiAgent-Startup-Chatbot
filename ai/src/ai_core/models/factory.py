"""Chat model factory.

Central place to resolve which LLM an agent uses. Direct providers use
``provider:model`` strings (e.g. ``openai:gpt-5-mini``), while OpenRouter uses
``openrouter:provider/model`` (e.g. ``openrouter:openai/gpt-5-mini``).
"""

from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ai_core.config import get_settings
from ai_core.prompts.loader import ModelOverride

OPENROUTER_PREFIX = "openrouter:"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _build_openrouter_model(
    spec: str,
    params: dict[str, Any],
) -> BaseChatModel:
    settings = get_settings()
    model = spec.removeprefix(OPENROUTER_PREFIX).strip()
    if not model:
        raise ValueError(
            "OpenRouter model must use 'openrouter:provider/model', "
            "for example 'openrouter:openai/gpt-5-mini'."
        )
    if not settings.openrouter_api_key:
        raise ValueError(
            "AI_MODEL=openrouter:... requires OPENROUTER_API_KEY "
            "(or AI_OPENROUTER_API_KEY)."
        )

    return ChatOpenAI(
        model=model,
        api_key=settings.openrouter_api_key,
        base_url=OPENROUTER_BASE_URL,
        **params,
    )


def get_chat_model(override: ModelOverride | None = None, **kwargs: Any) -> BaseChatModel:
    """Build a chat model from settings plus an optional per-agent override."""
    settings = get_settings()
    spec = settings.model
    params: dict[str, Any] = {}

    if override is not None:
        if override.name:
            spec = override.name
        if override.temperature is not None:
            params["temperature"] = override.temperature
        if override.max_tokens is not None:
            params["max_tokens"] = override.max_tokens

    params.update(kwargs)
    if spec.startswith(OPENROUTER_PREFIX):
        return _build_openrouter_model(spec, params)

    return init_chat_model(spec, **params)
