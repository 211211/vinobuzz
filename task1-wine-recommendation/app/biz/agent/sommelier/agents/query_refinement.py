from typing import Optional

from agents import Agent
from pydantic import BaseModel

from app.biz.agent.sommelier.schemas.wine_filter import WineFilter
from app.core.agent_config import get_agent_config, load_prompt


class QueryRefinement(BaseModel):
    justification: str
    refined_queries: list[str]
    relaxed_filters: Optional[WineFilter] = None


def create_query_refinement_agent() -> Agent:
    """Create the Query Refinement agent for transforming failed searches."""
    cfg = get_agent_config("query_refinement")
    prompt = load_prompt(cfg.prompt_name)

    return Agent(
        name="QueryRefinement",
        model=cfg.model,
        instructions=prompt,
        output_type=QueryRefinement,
    )
