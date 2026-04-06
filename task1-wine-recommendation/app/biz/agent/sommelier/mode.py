import asyncio
import logging
from typing import AsyncGenerator
from uuid import uuid4

from agents import Runner, ItemHelpers

from app.biz.agent.sommelier.agents.coordinator import create_coordinator_agent
from app.biz.agent.sommelier.agents.explorer import create_explorer_agent
from app.biz.agent.sommelier.agents.filter_builder import create_filter_builder_agent
from app.biz.agent.sommelier.agents.generator import (
    create_generator_agent,
    create_generator_no_handoff_agent,
)
from app.biz.agent.sommelier.agents.preference_planner import (
    create_preference_planner_agent,
)
from app.biz.agent.sommelier.agents.query_refinement import create_query_refinement_agent
from app.biz.agent.sommelier.schemas.preference_plan import PreferencePlan
from app.biz.agent.sommelier.schemas.wine_filter import WineFilter
from app.biz.agent.sommelier.utils.citation import parse_citations
from app.biz.tools.wine_db_tool import format_wine_context, search_wines
from app.core.chat_interface import run_agent
from app.core.streaming import ContentType, EventType, format_sse

logger = logging.getLogger(__name__)


class SommelierMode:
    """Orchestrator for the VinoBuzz AI Sommelier multi-agent workflow."""

    async def run(
        self, session_id: str, message_history: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        trace_id = str(uuid4())

        # Emit metadata
        yield format_sse(
            EventType.METADATA, {"session_id": session_id, "trace_id": trace_id}
        )

        try:
            # Step 1: Coordinator decides the flow
            yield format_sse(
                EventType.AGENT_UPDATED,
                {"agent": "coordinator", "content_type": ContentType.THOUGHTS.value},
            )

            explorer_agent = create_explorer_agent()
            # Create a lightweight planner placeholder for handoff detection
            planner_placeholder = create_preference_planner_agent()

            coordinator = create_coordinator_agent(
                planner_agent=planner_placeholder,
                explorer_agent=explorer_agent,
            )

            coord_result = await run_agent(coordinator, message_history)
            last_agent = coord_result.last_agent

            if last_agent.name == "Explorer":
                # Explorer flow — autonomous agent with tools
                async for event in self._explorer_flow(
                    explorer_agent, message_history, trace_id
                ):
                    yield event
            else:
                # Planner flow — structured extraction + search + generation
                async for event in self._planner_flow(message_history, trace_id):
                    yield event

        except Exception as e:
            logger.exception("SommelierMode error")
            yield format_sse(EventType.ERROR, {"message": str(e)})

        yield format_sse(EventType.DONE, {"message": "Stream completed"})

    async def _planner_flow(
        self, message_history: list[dict[str, str]], trace_id: str
    ) -> AsyncGenerator[str, None]:
        """Structured planner flow: extract prefs → build filters → search → generate."""

        # Step 2: Run PreferencePlanner and FilterBuilder in parallel
        yield format_sse(
            EventType.AGENT_UPDATED,
            {
                "agent": "preference_planner",
                "content_type": ContentType.THOUGHTS.value,
            },
        )

        planner_agent = create_preference_planner_agent()
        filter_agent = create_filter_builder_agent()

        async with asyncio.TaskGroup() as tg:
            planner_task = tg.create_task(run_agent(planner_agent, message_history))
            filter_task = tg.create_task(run_agent(filter_agent, message_history))

        planner_result = planner_task.result()
        filter_result = filter_task.result()

        preference_plan: PreferencePlan = planner_result.final_output
        wine_filter: WineFilter = filter_result.final_output

        # Step 3: Search wines using filters
        search_result = search_wines(
            type_filter=wine_filter.type_filter,
            budget_min=wine_filter.budget_min,
            budget_max=wine_filter.budget_max,
            country_filter=wine_filter.country_filter,
            region_filter=wine_filter.region_filter,
            occasion_tags=wine_filter.occasion_tags,
            grape_filter=wine_filter.grape_filter,
            body_filter=wine_filter.body_filter,
            sweetness_filter=wine_filter.sweetness_filter,
            food_pairing_filter=wine_filter.food_pairing_filter,
            exclude_skus=wine_filter.exclude_skus,
        )

        wines = search_result["wines"]
        wine_context = format_wine_context(wines)

        # Step 4: Build generator context and stream response
        yield format_sse(
            EventType.AGENT_UPDATED,
            {"agent": "generator", "content_type": ContentType.FINAL_ANSWER.value},
        )

        # Construct augmented system prompt with search results
        context_injection = self._build_generator_context(
            preference_plan, wine_context, search_result["relaxed"]
        )

        query_refinement_agent = create_query_refinement_agent()
        generator = create_generator_agent(query_refinement_agent)

        # Augmented message history with injected context
        augmented_messages = message_history.copy()
        augmented_messages.insert(
            0,
            {
                "role": "system",
                "content": generator.instructions + "\n\n" + context_injection,
            },
        )

        # Consume the generator stream to completion
        result = Runner.run_streamed(generator, input=augmented_messages)
        async for event in result.stream_events():
            pass

        # Check if generator handed off to query refinement
        if result.last_agent.name == "QueryRefinement":
            # Re-run with refined search
            async for event in self._refinement_flow(
                result, message_history, preference_plan, trace_id
            ):
                yield event
            return

        # Get the final text from result
        final_text = self._extract_final_text(result)
        if final_text:
            yield format_sse(EventType.DATA, {"content": final_text})

            # Parse citations
            citations = parse_citations(final_text)
            if citations:
                yield format_sse(
                    EventType.METADATA,
                    {
                        "citations": [c.model_dump() for c in citations],
                        "preferences_gathered": preference_plan.preferences.model_dump(),
                    },
                )

    async def _refinement_flow(
        self,
        refinement_result,
        message_history: list[dict[str, str]],
        original_plan: PreferencePlan,
        trace_id: str,
    ) -> AsyncGenerator[str, None]:
        """Handle query refinement: re-search with relaxed filters, then generate."""
        yield format_sse(
            EventType.AGENT_UPDATED,
            {
                "agent": "query_refinement",
                "content_type": ContentType.THOUGHTS.value,
            },
        )

        refinement = refinement_result.final_output
        relaxed = refinement.relaxed_filters

        if relaxed:
            search_result = search_wines(
                type_filter=relaxed.type_filter,
                budget_min=relaxed.budget_min,
                budget_max=relaxed.budget_max,
                country_filter=relaxed.country_filter,
                region_filter=relaxed.region_filter,
                occasion_tags=relaxed.occasion_tags,
                grape_filter=relaxed.grape_filter,
                body_filter=relaxed.body_filter,
                sweetness_filter=relaxed.sweetness_filter,
                food_pairing_filter=relaxed.food_pairing_filter,
                exclude_skus=relaxed.exclude_skus,
            )
        else:
            search_result = search_wines()

        wines = search_result["wines"]
        wine_context = format_wine_context(wines)

        yield format_sse(
            EventType.AGENT_UPDATED,
            {"agent": "generator", "content_type": ContentType.FINAL_ANSWER.value},
        )

        context_injection = self._build_generator_context(
            original_plan, wine_context, True
        )

        generator = create_generator_no_handoff_agent()
        augmented_messages = message_history.copy()
        augmented_messages.insert(
            0,
            {
                "role": "system",
                "content": generator.instructions + "\n\n" + context_injection,
            },
        )

        result = await run_agent(generator, augmented_messages)
        final_text = self._extract_final_text(result)

        if final_text:
            yield format_sse(EventType.DATA, {"content": final_text})
            citations = parse_citations(final_text)
            if citations:
                yield format_sse(
                    EventType.METADATA,
                    {
                        "citations": [c.model_dump() for c in citations],
                        "preferences_gathered": original_plan.preferences.model_dump(),
                    },
                )

    async def _explorer_flow(
        self,
        explorer_agent,
        message_history: list[dict[str, str]],
        trace_id: str,
    ) -> AsyncGenerator[str, None]:
        """Explorer flow: autonomous agent with tools."""
        yield format_sse(
            EventType.AGENT_UPDATED,
            {"agent": "explorer", "content_type": ContentType.FINAL_ANSWER.value},
        )

        result = Runner.run_streamed(explorer_agent, input=message_history)
        async for event in result.stream_events():
            pass  # Consume the stream to completion

        final_text = self._extract_final_text(result)
        if final_text:
            yield format_sse(EventType.DATA, {"content": final_text})
            citations = parse_citations(final_text)
            if citations:
                yield format_sse(
                    EventType.METADATA,
                    {"citations": [c.model_dump() for c in citations]},
                )

    def _build_generator_context(
        self,
        plan: PreferencePlan,
        wine_context: str,
        relaxed: bool,
    ) -> str:
        """Build context injection for generator system prompt."""
        prefs = plan.preferences
        parts = [
            "## User Preferences",
            f"Occasion: {prefs.occasion or 'Not specified'}",
            f"Budget: {'HK$' + str(prefs.budget_min) + '-' if prefs.budget_min else ''}{'HK$' + str(prefs.budget_max) if prefs.budget_max else 'Not specified'}",
            f"Wine type: {prefs.wine_type or 'Not specified'}",
            f"Region: {prefs.region or 'Not specified'}",
            f"Country: {prefs.country or 'Not specified'}",
            f"Grape: {prefs.grape or 'Not specified'}",
            f"Food pairing: {prefs.food_pairing or 'Not specified'}",
            f"Taste notes: {', '.join(prefs.taste_notes) if prefs.taste_notes else 'Not specified'}",
            f"Confidence: {plan.confidence}",
            "",
            "## Matching Wines",
            wine_context if wine_context else "No matching wines found.",
        ]

        if relaxed:
            parts.append(
                "\n**Note:** Search was relaxed beyond original criteria to find options."
            )

        return "\n".join(parts)

    def _extract_final_text(self, result) -> str:
        """Extract the final text output from a run result."""
        if hasattr(result, "final_output") and isinstance(result.final_output, str):
            return result.final_output
        # Try to get from new_items
        if hasattr(result, "new_items"):
            for item in reversed(result.new_items):
                if hasattr(item, "raw_item") and hasattr(item.raw_item, "content"):
                    for content_block in item.raw_item.content:
                        if hasattr(content_block, "text"):
                            return content_block.text
        # Fallback: try ItemHelpers
        try:
            text = ItemHelpers.text_message_output(result.new_items)
            if text:
                return text
        except Exception:
            pass
        return ""
