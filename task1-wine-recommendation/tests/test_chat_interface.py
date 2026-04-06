"""Tests for chat_interface retry logic — mocks the agents SDK."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.chat_interface import run_agent, run_agent_streamed


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.name = "TestAgent"
    return agent


class TestRunAgent:
    @pytest.mark.asyncio
    async def test_success_first_attempt(self, mock_agent):
        mock_result = MagicMock()
        mock_result.final_output = "test output"

        with patch("app.core.chat_interface.Runner") as MockRunner:
            MockRunner.run = AsyncMock(return_value=mock_result)

            result = await run_agent(
                mock_agent,
                [{"role": "user", "content": "hello"}],
            )

            assert result.final_output == "test output"
            assert MockRunner.run.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure(self, mock_agent):
        mock_result = MagicMock()

        with patch("app.core.chat_interface.Runner") as MockRunner:
            MockRunner.run = AsyncMock(
                side_effect=[Exception("fail 1"), Exception("fail 2"), mock_result]
            )

            result = await run_agent(
                mock_agent,
                [{"role": "user", "content": "hello"}],
                max_retries=3,
                retry_delay=0.01,
            )

            assert result == mock_result
            assert MockRunner.run.call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self, mock_agent):
        with patch("app.core.chat_interface.Runner") as MockRunner:
            MockRunner.run = AsyncMock(side_effect=Exception("persistent failure"))

            with pytest.raises(Exception, match="persistent failure"):
                await run_agent(
                    mock_agent,
                    [{"role": "user", "content": "hello"}],
                    max_retries=2,
                    retry_delay=0.01,
                )

            assert MockRunner.run.call_count == 2

    @pytest.mark.asyncio
    async def test_passes_context(self, mock_agent):
        mock_result = MagicMock()
        context = {"session_id": "abc"}

        with patch("app.core.chat_interface.Runner") as MockRunner:
            MockRunner.run = AsyncMock(return_value=mock_result)

            await run_agent(
                mock_agent,
                [{"role": "user", "content": "hello"}],
                context=context,
            )

            call_kwargs = MockRunner.run.call_args
            assert call_kwargs.kwargs.get("context") == context or (
                len(call_kwargs.args) > 2 and call_kwargs.args[2] == context
            )


class TestRunAgentStreamed:
    @pytest.mark.asyncio
    async def test_success_first_attempt(self, mock_agent):
        mock_result = MagicMock()

        with patch("app.core.chat_interface.Runner") as MockRunner:
            MockRunner.run_streamed = MagicMock(return_value=mock_result)

            result = await run_agent_streamed(
                mock_agent,
                [{"role": "user", "content": "hello"}],
            )

            assert result == mock_result
            assert MockRunner.run_streamed.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure(self, mock_agent):
        mock_result = MagicMock()

        with patch("app.core.chat_interface.Runner") as MockRunner:
            MockRunner.run_streamed = MagicMock(
                side_effect=[Exception("fail"), mock_result]
            )

            result = await run_agent_streamed(
                mock_agent,
                [{"role": "user", "content": "hello"}],
                max_retries=2,
                retry_delay=0.01,
            )

            assert result == mock_result
            assert MockRunner.run_streamed.call_count == 2
