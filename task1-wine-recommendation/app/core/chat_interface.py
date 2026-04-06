import asyncio
from typing import Any

from agents import Agent, Runner, ItemHelpers, RunResultStreaming


async def run_agent_streamed(
    agent: Agent,
    input_messages: list[dict[str, str]],
    context: Any = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> RunResultStreaming:
    """Run an agent with streaming, with retry logic."""
    last_error = None
    for attempt in range(max_retries):
        try:
            result = Runner.run_streamed(
                agent,
                input=input_messages,
                context=context,
            )
            return result
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
    raise last_error


async def run_agent(
    agent: Agent,
    input_messages: list[dict[str, str]],
    context: Any = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> Any:
    """Run an agent (non-streamed) and return the final output."""
    last_error = None
    for attempt in range(max_retries):
        try:
            result = await Runner.run(
                agent,
                input=input_messages,
                context=context,
            )
            return result
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
    raise last_error
