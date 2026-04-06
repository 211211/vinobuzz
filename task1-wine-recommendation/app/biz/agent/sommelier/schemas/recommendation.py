from typing import Optional

from pydantic import BaseModel

from app.biz.agent.sommelier.schemas.preference_plan import GatheredPreferences


class WineCitation(BaseModel):
    id: str
    name: str
    type: str
    region: str
    price_hkd: int
    match_reasons: list[str] = []


class SommelierMetadata(BaseModel):
    session_id: str
    trace_id: str
    citations: list[WineCitation] = []
    preferences_gathered: Optional[GatheredPreferences] = None
