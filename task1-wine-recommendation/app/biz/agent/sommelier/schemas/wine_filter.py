from typing import Optional

from pydantic import BaseModel


class WineFilter(BaseModel):
    justification: str = ""
    type_filter: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    country_filter: Optional[str] = None
    region_filter: Optional[str] = None
    occasion_tags: list[str] = []
    grape_filter: Optional[str] = None
    body_filter: Optional[str] = None
    sweetness_filter: Optional[str] = None
    food_pairing_filter: Optional[str] = None
    exclude_skus: list[str] = []
