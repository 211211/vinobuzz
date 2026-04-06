"""Tests for wine_db_tool search, filter, scoring, and relaxation logic."""

from app.biz.tools.wine_db_tool import format_wine_context, search_wines


class TestSearchWines:
    def test_search_by_type_red(self):
        result = search_wines(type_filter="red")
        assert len(result["wines"]) > 0
        for wine in result["wines"]:
            assert wine["type"] == "red"

    def test_search_by_type_white(self):
        result = search_wines(type_filter="white")
        assert len(result["wines"]) > 0
        for wine in result["wines"]:
            assert wine["type"] == "white"

    def test_search_by_type_sparkling(self):
        result = search_wines(type_filter="sparkling")
        assert len(result["wines"]) > 0
        for wine in result["wines"]:
            assert wine["type"] == "sparkling"

    def test_search_budget_max(self):
        result = search_wines(type_filter="red", budget_max=300)
        for wine in result["wines"]:
            assert wine["price_hkd"] <= 300

    def test_search_budget_range(self):
        result = search_wines(budget_min=200, budget_max=500)
        assert len(result["wines"]) > 0

    def test_search_by_country(self):
        result = search_wines(country_filter="France")
        assert len(result["wines"]) > 0
        for wine in result["wines"]:
            assert wine["country"] == "France"

    def test_search_by_region(self):
        result = search_wines(region_filter="Bordeaux")
        assert len(result["wines"]) > 0
        for wine in result["wines"]:
            assert wine["region"] == "Bordeaux"

    def test_search_by_occasion(self):
        result = search_wines(occasion_tags=["business dinner"])
        assert len(result["wines"]) > 0
        for wine in result["wines"]:
            assert "business dinner" in wine["occasions"]

    def test_search_by_grape(self):
        result = search_wines(grape_filter="Pinot Noir")
        assert len(result["wines"]) > 0
        for wine in result["wines"]:
            assert "pinot noir" in wine["grape"].lower()

    def test_search_by_body(self):
        result = search_wines(body_filter="full")
        assert len(result["wines"]) > 0

    def test_search_by_sweetness(self):
        result = search_wines(sweetness_filter="dry")
        assert len(result["wines"]) > 0

    def test_search_by_food_pairing(self):
        result = search_wines(food_pairing_filter="beef")
        assert len(result["wines"]) > 0

    def test_search_free_text(self):
        result = search_wines(query="cherry elegant")
        assert len(result["wines"]) > 0

    def test_exclude_skus(self):
        result = search_wines(type_filter="red", exclude_skus=["FR-BDX-001", "FR-BDX-002"])
        for wine in result["wines"]:
            assert wine["sku"] not in ["FR-BDX-001", "FR-BDX-002"]

    def test_top_k_limit(self):
        result = search_wines(type_filter="red", top_k=3)
        assert len(result["wines"]) <= 3

    def test_combined_filters(self):
        """Test realistic scenario: French red under HK$500 for business dinner."""
        result = search_wines(
            type_filter="red",
            country_filter="France",
            budget_max=500,
            occasion_tags=["business dinner"],
        )
        assert len(result["wines"]) > 0
        for wine in result["wines"]:
            assert wine["type"] == "red"
            assert wine["country"] == "France"
            assert wine["price_hkd"] <= 500

    def test_relaxation_triggered(self):
        """Very restrictive filters should trigger relaxation."""
        result = search_wines(
            type_filter="red",
            region_filter="Champagne",
            budget_max=100,
        )
        # Should return results even if relaxed
        assert "relaxed" in result

    def test_scores_sorted_descending(self):
        result = search_wines(type_filter="red", budget_max=500)
        scores = [w["score"] for w in result["wines"]]
        assert scores == sorted(scores, reverse=True)

    def test_no_results_returns_empty(self):
        result = search_wines(type_filter="orange")
        assert result["wines"] == [] or result["relaxed"] is True

    def test_empty_search_returns_wines(self):
        """No filters should return top wines by rating."""
        result = search_wines()
        assert len(result["wines"]) > 0


class TestFormatWineContext:
    def test_format_single_wine(self):
        wines = [
            {
                "sku": "FR-BDX-001",
                "name": "Test Wine",
                "type": "red",
                "region": "Bordeaux",
                "country": "France",
                "price_hkd": 500,
                "grape": "Cabernet Sauvignon",
                "tasting_notes": "Bold and fruity",
                "occasions": ["casual"],
                "food_pairing": ["beef"],
                "rating": 4.5,
            }
        ]
        context = format_wine_context(wines)
        assert "<<<WINE>>>" in context
        assert "FR-BDX-001" in context
        assert "Test Wine" in context
        assert "<<<END WINE>>>" in context

    def test_format_empty_list(self):
        context = format_wine_context([])
        assert context == ""
