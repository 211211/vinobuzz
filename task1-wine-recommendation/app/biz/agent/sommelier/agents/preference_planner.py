from agents import Agent

from app.biz.agent.sommelier.schemas.preference_plan import PreferencePlan
from app.core.agent_config import get_agent_config, load_prompt


def create_preference_planner_agent() -> Agent:
    """Create the Preference Planner agent that extracts structured preferences."""
    cfg = get_agent_config("preference_planner")
    prompt = load_prompt(cfg.prompt_name)

    return Agent(
        name="PreferencePlanner",
        model=cfg.model,
        instructions=prompt,
        output_type=PreferencePlan,
    )
