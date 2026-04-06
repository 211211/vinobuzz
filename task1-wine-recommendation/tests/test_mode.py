"""Tests for SommelierMode orchestrator — mocks all LLM calls."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.biz.agent.sommelier.mode import SommelierMode
from app.biz.agent.sommelier.schemas.preference_plan import (
    GatheredPreferences,
    PreferencePlan,
)
from app.biz.agent.sommelier.schemas.wine_filter import WineFilter


def _make_plan(wine_type="red", budget_max=500, country="France", confidence=0.8):
    return PreferencePlan(
        justification="test",
        preferences=GatheredPreferences(
            wine_type=wine_type, budget_max=budget_max, country=country
        ),
        search_queries=["French red wine"],
        confidence=confidence,
    )


def _make_filter(type_filter="red", budget_max=500, country_filter="France"):
    return WineFilter(
        justification="test",
        type_filter=type_filter,
        budget_max=budget_max,
        country_filter=country_filter,
    )


class TestBuildGeneratorContext:
    def setup_method(self):
        self.mode = SommelierMode()

    def test_includes_preferences(self):
        plan = _make_plan()
        ctx = self.mode._build_generator_context(plan, "some wines", False)

        assert "## User Preferences" in ctx
        assert "red" in ctx
        assert "HK$500" in ctx
        assert "France" in ctx
        assert "0.8" in ctx

    def test_includes_wine_context(self):
        plan = _make_plan()
        ctx = self.mode._build_generator_context(plan, "<<<WINE>>>\nTest Wine", False)
        assert "<<<WINE>>>" in ctx
        assert "Test Wine" in ctx

    def test_no_wines_shows_message(self):
        plan = _make_plan()
        ctx = self.mode._build_generator_context(plan, "", False)
        assert "No matching wines found." in ctx

    def test_relaxed_flag_adds_note(self):
        plan = _make_plan()
        ctx = self.mode._build_generator_context(plan, "some wines", True)
        assert "relaxed" in ctx.lower()

    def test_not_relaxed_no_note(self):
        plan = _make_plan()
        ctx = self.mode._build_generator_context(plan, "some wines", False)
        assert "relaxed beyond" not in ctx.lower()

    def test_optional_fields_show_not_specified(self):
        plan = PreferencePlan(
            justification="test",
            preferences=GatheredPreferences(),
            search_queries=[],
            confidence=0.2,
        )
        ctx = self.mode._build_generator_context(plan, "", False)
        assert "Not specified" in ctx

    def test_budget_range_format(self):
        plan = PreferencePlan(
            justification="test",
            preferences=GatheredPreferences(budget_min=200, budget_max=500),
            search_queries=[],
            confidence=0.7,
        )
        ctx = self.mode._build_generator_context(plan, "", False)
        assert "HK$200-" in ctx
        assert "HK$500" in ctx

    def test_taste_notes_joined(self):
        plan = PreferencePlan(
            justification="test",
            preferences=GatheredPreferences(taste_notes=["bold", "oaky", "fruity"]),
            search_queries=[],
            confidence=0.5,
        )
        ctx = self.mode._build_generator_context(plan, "", False)
        assert "bold, oaky, fruity" in ctx


class TestExtractFinalText:
    def setup_method(self):
        self.mode = SommelierMode()

    def test_from_final_output_string(self):
        result = MagicMock()
        result.final_output = "Here are my recommendations..."
        assert self.mode._extract_final_text(result) == "Here are my recommendations..."

    def test_from_new_items(self):
        content_block = MagicMock()
        content_block.text = "Wine text from items"

        raw_item = MagicMock()
        raw_item.content = [content_block]

        item = MagicMock()
        item.raw_item = raw_item

        result = MagicMock()
        result.final_output = None  # Not a string
        result.new_items = [item]

        assert self.mode._extract_final_text(result) == "Wine text from items"

    def test_empty_result(self):
        result = MagicMock()
        result.final_output = None
        result.new_items = []

        with patch("app.biz.agent.sommelier.mode.ItemHelpers") as MockHelpers:
            MockHelpers.text_message_output.return_value = ""
            assert self.mode._extract_final_text(result) == ""

    def test_final_output_non_string_falls_through(self):
        """When final_output is a structured object (not str), should try new_items."""
        result = MagicMock()
        result.final_output = {"some": "dict"}  # Not a string

        content_block = MagicMock()
        content_block.text = "Fallback text"
        raw_item = MagicMock()
        raw_item.content = [content_block]
        item = MagicMock()
        item.raw_item = raw_item
        result.new_items = [item]

        assert self.mode._extract_final_text(result) == "Fallback text"


class TestSommelierModeRun:
    """Integration-level tests for the orchestrator run() — mocks all agent calls."""

    @pytest.mark.asyncio
    async def test_run_emits_metadata_and_done(self):
        """Every run should start with metadata and end with done, even on error."""
        mode = SommelierMode()
        messages = [{"role": "user", "content": "hello"}]

        events = []
        with patch(
            "app.biz.agent.sommelier.mode.run_agent",
            new_callable=AsyncMock,
            side_effect=Exception("LLM unavailable"),
        ):
            async for event in mode.run("test-session", messages):
                events.append(event)

        # Parse events
        parsed = []
        for e in events:
            for line in e.strip().split("\n"):
                if line.startswith("event:"):
                    parsed.append(line.split("event: ")[1])

        assert parsed[0] == "metadata"
        assert parsed[-1] == "done"
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_run_explorer_flow_routing(self):
        """When coordinator routes to Explorer, the explorer flow should execute."""
        mode = SommelierMode()
        messages = [{"role": "user", "content": "surprise me"}]

        # Mock coordinator returning Explorer agent
        coord_result = MagicMock()
        coord_result.last_agent = MagicMock()
        coord_result.last_agent.name = "Explorer"

        # Mock the streamed result for explorer
        mock_stream_result = MagicMock()
        mock_stream_result.final_output = "Try this amazing wine!"
        mock_stream_result.new_items = []

        async def mock_stream_events():
            return
            yield  # make it an async generator

        mock_stream_result.stream_events = mock_stream_events

        events = []
        with (
            patch(
                "app.biz.agent.sommelier.mode.run_agent",
                new_callable=AsyncMock,
                return_value=coord_result,
            ),
            patch(
                "app.biz.agent.sommelier.mode.Runner"
            ) as MockRunner,
        ):
            MockRunner.run_streamed.return_value = mock_stream_result

            async for event in mode.run("test-session", messages):
                events.append(event)

        # Should have explorer agent_updated event
        all_text = "".join(events)
        assert "explorer" in all_text
        assert "Try this amazing wine!" in all_text

    @pytest.mark.asyncio
    async def test_run_planner_flow_routing(self):
        """When coordinator routes to Planner, the planner flow should execute."""
        mode = SommelierMode()
        messages = [{"role": "user", "content": "French red wine under 500"}]

        # Mock coordinator returning Planner agent
        coord_result = MagicMock()
        coord_result.last_agent = MagicMock()
        coord_result.last_agent.name = "PreferencePlanner"

        # Mock planner and filter results
        planner_result = MagicMock()
        planner_result.final_output = _make_plan()

        filter_result = MagicMock()
        filter_result.final_output = _make_filter()

        # Mock generator streamed result
        gen_stream = MagicMock()
        gen_stream.last_agent = MagicMock()
        gen_stream.last_agent.name = "Generator"
        gen_stream.final_output = (
            "I recommend **Chateau Margaux** [1](#FR-BDX-001) — excellent choice."
        )
        gen_stream.new_items = []

        async def mock_stream_events():
            return
            yield

        gen_stream.stream_events = mock_stream_events

        events = []
        with (
            patch(
                "app.biz.agent.sommelier.mode.run_agent",
                new_callable=AsyncMock,
                side_effect=[coord_result, planner_result, filter_result],
            ),
            patch("app.biz.agent.sommelier.mode.Runner") as MockRunner,
        ):
            MockRunner.run_streamed.return_value = gen_stream

            async for event in mode.run("test-session", messages):
                events.append(event)

        all_text = "".join(events)
        assert "preference_planner" in all_text
        assert "generator" in all_text
        assert "Chateau Margaux" in all_text
        assert "FR-BDX-001" in all_text

    @pytest.mark.asyncio
    async def test_error_yields_error_event_and_done(self):
        """Exceptions during flow should yield an error event, then done."""
        mode = SommelierMode()
        messages = [{"role": "user", "content": "test"}]

        events = []
        with patch(
            "app.biz.agent.sommelier.mode.run_agent",
            new_callable=AsyncMock,
            side_effect=RuntimeError("something broke"),
        ):
            async for event in mode.run("sess", messages):
                events.append(event)

        all_text = "".join(events)
        assert "error" in all_text
        assert "something broke" in all_text
        assert '"message": "Stream completed"' in all_text
