"""Tests for Pydantic schemas — validate structure and defaults."""

from app.biz.agent.sommelier.schemas.preference_plan import (
    GatheredPreferences,
    PreferencePlan,
)
from app.biz.agent.sommelier.schemas.wine_filter import WineFilter
from app.biz.agent.sommelier.schemas.recommendation import WineCitation


class TestGatheredPreferences:
    def test_defaults(self):
        prefs = GatheredPreferences()
        assert prefs.occasion is None
        assert prefs.budget_min is None
        assert prefs.budget_max is None
        assert prefs.wine_type is None
        assert prefs.region is None
        assert prefs.country is None
        assert prefs.grape is None
        assert prefs.taste_notes == []
        assert prefs.food_pairing is None
        assert prefs.quantity == 1

    def test_full_preferences(self):
        prefs = GatheredPreferences(
            occasion="business dinner",
            budget_min=300,
            budget_max=500,
            wine_type="red",
            region="Bordeaux",
            country="France",
            grape="Cabernet Sauvignon",
            taste_notes=["bold", "oaky"],
            food_pairing="steak",
            quantity=2,
        )
        assert prefs.occasion == "business dinner"
        assert prefs.budget_max == 500
        assert len(prefs.taste_notes) == 2


class TestPreferencePlan:
    def test_minimal(self):
        plan = PreferencePlan(
            justification="User wants red wine",
            preferences=GatheredPreferences(wine_type="red"),
            search_queries=["red wine"],
            confidence=0.5,
        )
        assert plan.confidence == 0.5
        assert plan.user_language == "en"
        assert plan.preferences.wine_type == "red"

    def test_high_confidence(self):
        plan = PreferencePlan(
            justification="Full preferences gathered",
            preferences=GatheredPreferences(
                wine_type="red",
                budget_max=500,
                country="France",
                occasion="business dinner",
            ),
            search_queries=["French red wine under 500"],
            confidence=0.9,
            user_language="ja",
        )
        assert plan.confidence == 0.9
        assert plan.user_language == "ja"


class TestWineFilter:
    def test_defaults(self):
        wf = WineFilter()
        assert wf.type_filter is None
        assert wf.budget_min is None
        assert wf.occasion_tags == []
        assert wf.exclude_skus == []

    def test_full_filter(self):
        wf = WineFilter(
            justification="User wants French red",
            type_filter="red",
            budget_max=500,
            country_filter="France",
            region_filter="Bordeaux",
            occasion_tags=["business dinner"],
            grape_filter="Cabernet Sauvignon",
            body_filter="full",
            sweetness_filter="dry",
            food_pairing_filter="steak",
        )
        assert wf.type_filter == "red"
        assert wf.country_filter == "France"
        assert "business dinner" in wf.occasion_tags


class TestWineCitation:
    def test_citation_fields(self):
        c = WineCitation(
            id="FR-BDX-001",
            name="Chateau Margaux 2018",
            type="red",
            region="Bordeaux",
            price_hkd=1800,
            match_reasons=["French red", "business dinner appropriate"],
        )
        assert c.id == "FR-BDX-001"
        assert c.price_hkd == 1800
        assert len(c.match_reasons) == 2

    def test_serialization(self):
        c = WineCitation(
            id="FR-BDX-001",
            name="Test Wine",
            type="red",
            region="Bordeaux",
            price_hkd=500,
            match_reasons=["good value"],
        )
        d = c.model_dump()
        assert d["id"] == "FR-BDX-001"
        assert isinstance(d["match_reasons"], list)
