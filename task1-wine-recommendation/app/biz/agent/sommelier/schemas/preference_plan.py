from typing import Optional

from pydantic import BaseModel


class GatheredPreferences(BaseModel):
    occasion: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    wine_type: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    grape: Optional[str] = None
    taste_notes: list[str] = []
    food_pairing: Optional[str] = None
    quantity: int = 1


class PreferencePlan(BaseModel):
    justification: str
    preferences: GatheredPreferences
    search_queries: list[str]
    confidence: float
    user_language: str = "en"
