"""Agent specs: YAML config resolved into runtime metadata."""

from dataclasses import dataclass, field

from ai_core.prompts.loader import AgentPromptConfig, load_agent_config
from ai_core.schemas.events import AgentInfo


@dataclass(frozen=True)
class AgentSpec:
    config: AgentPromptConfig

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            name=self.config.name,
            display_name=self.config.display_name,
            description=self.config.description,
            tools=list(self.config.tools),
        )


def load_agent_spec(name: str) -> AgentSpec:
    return AgentSpec(config=load_agent_config(name))
