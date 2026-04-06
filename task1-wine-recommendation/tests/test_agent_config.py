"""Tests for agent configuration loading."""

from app.core.agent_config import get_agent_config, load_prompt


class TestGetAgentConfig:
    def test_coordinator_config(self):
        cfg = get_agent_config("coordinator")
        assert cfg.model == "gpt-4o-mini"
        assert cfg.temperature == 0.1
        assert cfg.prompt_name == "coordinator"

    def test_preference_planner_config(self):
        cfg = get_agent_config("preference_planner")
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.1

    def test_generator_config(self):
        cfg = get_agent_config("generator")
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.7

    def test_explorer_config(self):
        cfg = get_agent_config("explorer")
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.7

    def test_filter_builder_config(self):
        cfg = get_agent_config("filter_builder")
        assert cfg.model == "gpt-4o-mini"
        assert cfg.temperature == 0.1

    def test_query_refinement_config(self):
        cfg = get_agent_config("query_refinement")
        assert cfg.model == "gpt-4o-mini"
        assert cfg.temperature == 0.3


class TestLoadPrompt:
    def test_coordinator_prompt_loads(self):
        prompt = load_prompt("coordinator")
        assert len(prompt) > 0
        assert "planner" in prompt.lower() or "explorer" in prompt.lower()

    def test_generator_prompt_loads(self):
        prompt = load_prompt("generator")
        assert len(prompt) > 0
        assert "wine" in prompt.lower() or "recommend" in prompt.lower()

    def test_preference_planner_prompt_loads(self):
        prompt = load_prompt("preference_planner")
        assert len(prompt) > 0

    def test_explorer_prompt_loads(self):
        prompt = load_prompt("explorer")
        assert len(prompt) > 0

    def test_filter_builder_prompt_loads(self):
        prompt = load_prompt("filter_builder")
        assert len(prompt) > 0

    def test_query_refinement_prompt_loads(self):
        prompt = load_prompt("query_refinement")
        assert len(prompt) > 0

    def test_all_agents_have_matching_prompts(self):
        """Every agent in config must have a loadable prompt file."""
        from app.settings import get_sommelier_config

        config = get_sommelier_config()
        for agent_name, agent_cfg in config["agents"].items():
            prompt = load_prompt(agent_cfg["prompt"])
            assert len(prompt) > 0, f"Empty prompt for agent: {agent_name}"
