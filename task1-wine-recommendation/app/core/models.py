from uuid import uuid4
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SommelierInput(BaseModel):
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    message_history: list[dict[str, str]]

    @field_validator("message_history")
    @classmethod
    def limit_history(cls, v):
        return v[-20:]


class StreamEvent(BaseModel):
    event: str
    data: dict
