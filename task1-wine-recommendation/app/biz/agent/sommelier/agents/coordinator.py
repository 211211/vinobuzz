from agents import Agent, handoff

from app.core.agent_config import get_agent_config, load_prompt


def create_coordinator_agent(planner_agent: Agent, explorer_agent: Agent) -> Agent:
    """Create the Coordinator agent that routes to planner or explorer flow."""
    cfg = get_agent_config("coordinator")
    prompt = load_prompt(cfg.prompt_name)

    return Agent(
        name="Coordinator",
        model=cfg.model,
        instructions=prompt,
        handoffs=[
            handoff(agent=planner_agent, tool_name_override="handoff_to_planner"),
            handoff(agent=explorer_agent, tool_name_override="handoff_to_explorer"),
        ],
    )
