from agents import Agent, function_tool

from app.biz.tools.web_search_tool import search_wine_knowledge
from app.biz.tools.wine_db_tool import format_wine_context, search_wines
from app.core.agent_config import get_agent_config, load_prompt


@function_tool
def wine_db_search(
    query: str = "",
    type_filter: str = "",
    budget_max: int = 0,
    country_filter: str = "",
    region_filter: str = "",
    occasion_tags: str = "",
    grape_filter: str = "",
) -> str:
    """Search the VinoBuzz wine inventory with filters.

    Args:
        query: Free-text search query (wine name, grape, tasting notes)
        type_filter: Wine type — "red", "white", "sparkling", or "rose"
        budget_max: Maximum price in HKD (0 means no limit)
        country_filter: Country name e.g. "France", "Italy"
        region_filter: Region name e.g. "Bordeaux", "Tuscany"
        occasion_tags: Comma-separated occasions e.g. "business dinner,celebration"
        grape_filter: Grape variety e.g. "Cabernet Sauvignon"
    """
    result = search_wines(
        query=query or None,
        type_filter=type_filter or None,
        budget_max=budget_max or None,
        country_filter=country_filter or None,
        region_filter=region_filter or None,
        occasion_tags=[t.strip() for t in occasion_tags.split(",") if t.strip()]
        if occasion_tags
        else [],
        grape_filter=grape_filter or None,
    )
    wines = result["wines"]
    if not wines:
        return "No wines found matching those criteria."
    context = format_wine_context(wines)
    suffix = " (Note: search was relaxed to find more options)" if result["relaxed"] else ""
    return f"Found {len(wines)} wines:{suffix}\n\n{context}"


@function_tool
def wine_knowledge_search(query: str) -> str:
    """Search wine knowledge base for pairing rules, region facts, and grape profiles.

    Args:
        query: What to look up — a region, grape, food, or wine topic
    """
    return search_wine_knowledge(query)


def create_explorer_agent() -> Agent:
    """Create the Explorer agent for open-ended/vague requests."""
    cfg = get_agent_config("explorer")
    prompt = load_prompt(cfg.prompt_name)

    return Agent(
        name="Explorer",
        model=cfg.model,
        instructions=prompt,
        tools=[wine_db_search, wine_knowledge_search],
    )
