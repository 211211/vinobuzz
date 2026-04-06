import json
from enum import Enum
from typing import Any


class EventType(str, Enum):
    METADATA = "metadata"
    AGENT_UPDATED = "agent_updated"
    DATA = "data"
    DONE = "done"
    ERROR = "error"


class ContentType(str, Enum):
    THOUGHTS = "thoughts"
    FINAL_ANSWER = "final_answer"


def format_sse(event: EventType, data: dict[str, Any]) -> str:
    return f"event: {event.value}\ndata: {json.dumps(data)}\n\n"
