"""Tests for web_search_tool (wine knowledge search)."""

from app.biz.tools.web_search_tool import search_wine_knowledge


class TestSearchWineKnowledge:
    def test_pairing_beef(self):
        result = search_wine_knowledge("What wine goes with beef?")
        assert "beef" in result.lower() or "Pairing" in result

    def test_pairing_seafood(self):
        result = search_wine_knowledge("seafood")
        assert "seafood" in result.lower() or "Pairing" in result

    def test_region_bordeaux(self):
        result = search_wine_knowledge("Tell me about Bordeaux")
        assert "Bordeaux" in result

    def test_region_burgundy(self):
        result = search_wine_knowledge("What is Burgundy known for?")
        assert "Burgundy" in result

    def test_grape_cabernet_sauvignon(self):
        result = search_wine_knowledge("Cabernet Sauvignon")
        assert "Cabernet Sauvignon" in result
        assert "Body:" in result
        assert "Pairs with:" in result

    def test_grape_pinot_noir(self):
        result = search_wine_knowledge("Pinot Noir")
        assert "Pinot Noir" in result

    def test_no_results(self):
        result = search_wine_knowledge("quantum computing")
        assert "No specific wine knowledge found" in result

    def test_case_insensitive(self):
        result = search_wine_knowledge("BORDEAUX")
        assert "Bordeaux" in result

    def test_combined_query_grape_and_region(self):
        result = search_wine_knowledge("Pinot Noir from Burgundy")
        assert "Pinot Noir" in result
        assert "Burgundy" in result
