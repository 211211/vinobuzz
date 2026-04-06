from dataclasses import dataclass
from pathlib import Path

from app.settings import get_sommelier_config


@dataclass
class AgentConfig:
    model: str
    temperature: float
    prompt_name: str


def get_agent_config(agent_name: str) -> AgentConfig:
    config = get_sommelier_config()
    agent_cfg = config["agents"][agent_name]
    return AgentConfig(
        model=agent_cfg["model"],
        temperature=agent_cfg["temperature"],
        prompt_name=agent_cfg["prompt"],
    )


def load_prompt(prompt_name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.md"
    return prompt_path.read_text()
