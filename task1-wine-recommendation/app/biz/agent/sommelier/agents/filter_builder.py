from agents import Agent

from app.biz.agent.sommelier.schemas.wine_filter import WineFilter
from app.core.agent_config import get_agent_config, load_prompt


def create_filter_builder_agent() -> Agent:
    """Create the Filter Builder agent that produces search filters."""
    cfg = get_agent_config("filter_builder")
    prompt = load_prompt(cfg.prompt_name)

    return Agent(
        name="FilterBuilder",
        model=cfg.model,
        instructions=prompt,
        output_type=WineFilter,
    )
