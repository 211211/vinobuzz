from agents import Agent, handoff

from app.core.agent_config import get_agent_config, load_prompt


def create_generator_agent(query_refinement_agent: Agent) -> Agent:
    """Create the Generator agent WITH handoff to query refinement (first pass)."""
    cfg = get_agent_config("generator_with_handoff")
    prompt = load_prompt(cfg.prompt_name)

    return Agent(
        name="Generator",
        model=cfg.model,
        instructions=prompt,
        handoffs=[
            handoff(
                agent=query_refinement_agent,
                tool_name_override="handoff_to_query_refinement",
            ),
        ],
    )


def create_generator_no_handoff_agent() -> Agent:
    """Create the Generator agent WITHOUT handoff (second pass after refinement)."""
    cfg = get_agent_config("generator")
    prompt = load_prompt(cfg.prompt_name)

    return Agent(
        name="Generator",
        model=cfg.model,
        instructions=prompt,
    )
