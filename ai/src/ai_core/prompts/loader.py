"""YAML prompt/config loading.

All agent behavior lives in YAML files, not code:

    prompts/agents/<name>.yaml      — one file per agent (role, prompts, tools)
    prompts/workflows/<name>.yaml   — workflow wiring and instructions

Adding a new agent = add a YAML file and list it in the workflow's
``specialists``. No Python changes required.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

PROMPTS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = PROMPTS_DIR / "agents"
WORKFLOWS_DIR = PROMPTS_DIR / "workflows"


class ModelOverride(BaseModel):
    """Optional per-agent model override; unset fields fall back to AISettings."""

    name: str | None = None  # "provider:model" or "openrouter:provider/model"
    temperature: float | None = None
    max_tokens: int | None = None


class AgentPromptConfig(BaseModel):
    name: str
    display_name: str
    description: str
    system_prompt: str
    task_prompt: str | None = None
    tools: list[str] = Field(default_factory=list)
    model: ModelOverride | None = None


class WorkflowConfig(BaseModel):
    name: str
    display_name: str
    description: str
    supervisor: str
    specialists: list[str]
    finalizer: str
    max_iterations: int = 10


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Prompt config not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Prompt config must be a YAML mapping: {path}")
    return data


@lru_cache
def load_agent_config(name: str) -> AgentPromptConfig:
    return AgentPromptConfig.model_validate(_read_yaml(AGENTS_DIR / f"{name}.yaml"))


@lru_cache
def load_workflow_config(name: str) -> WorkflowConfig:
    return WorkflowConfig.model_validate(_read_yaml(WORKFLOWS_DIR / f"{name}.yaml"))


def list_agent_names() -> list[str]:
    return sorted(p.stem for p in AGENTS_DIR.glob("*.yaml"))


class _SafeDict(dict):
    """Leave unknown {placeholders} untouched instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render(template: str, **variables: Any) -> str:
    """Fill ``{placeholder}`` variables in a YAML prompt template."""
    return template.format_map(_SafeDict(**variables))
