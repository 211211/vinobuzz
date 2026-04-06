"""
Unit tests for the VinoBuzz wines API endpoints.

All tests mock psycopg2.connect so no real database is needed.
Run with: pytest -v
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException
from app.wines import search_wines, recommend_wine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_connect(fetchall_return=None, fetchone_return=None):
    """Create a mock psycopg2 connection + cursor."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = fetchall_return or []
    mock_cursor.fetchone.return_value = fetchone_return
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


# ---------------------------------------------------------------------------
# search_wines tests
# ---------------------------------------------------------------------------

class TestSearchWines:

    @patch("app.wines.psycopg2.connect")
    def test_basic_search_returns_formatted_results(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect(
            fetchall_return=[
                ("SKU001", "Chateau Margaux 2015", 4500, "Bordeaux"),
                ("SKU002", "Penfolds Bin 389", 350, "South Australia"),
            ]
        )
        mock_connect_fn.return_value = mock_conn

        result = search_wines(query="wine")

        assert len(result["wines"]) == 2
        assert result["wines"][0]["sku"] == "SKU001"
        assert result["wines"][1]["name"] == "Penfolds Bin 389"

    @patch("app.wines.psycopg2.connect")
    def test_uses_parameterized_query_not_fstring(self, mock_connect_fn):
        """Verify SQL injection is prevented — query must use %s placeholders."""
        mock_conn, mock_cursor = _mock_connect()
        mock_connect_fn.return_value = mock_conn

        search_wines(query="'; DROP TABLE wines; --")

        executed_sql = mock_cursor.execute.call_args[0][0]
        executed_params = mock_cursor.execute.call_args[0][1]

        # The SQL string must NOT contain the user input literally
        assert "DROP TABLE" not in executed_sql
        # The user input should be in the params tuple/list
        assert any("DROP TABLE" in str(p) for p in executed_params)

    @patch("app.wines.psycopg2.connect")
    def test_budget_filter_applied(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect()
        mock_connect_fn.return_value = mock_conn

        search_wines(query="red", budget_max=500)

        executed_sql = mock_cursor.execute.call_args[0][0]
        executed_params = mock_cursor.execute.call_args[0][1]

        assert "price <= %s" in executed_sql
        assert 500 in executed_params

    @patch("app.wines.psycopg2.connect")
    def test_budget_zero_is_not_skipped(self, mock_connect_fn):
        """budget_max=0 should still apply the filter (bug fix #4)."""
        mock_conn, mock_cursor = _mock_connect()
        mock_connect_fn.return_value = mock_conn

        search_wines(query="red", budget_max=0)

        executed_sql = mock_cursor.execute.call_args[0][0]
        executed_params = mock_cursor.execute.call_args[0][1]

        assert "price <= %s" in executed_sql
        assert 0 in executed_params

    @patch("app.wines.psycopg2.connect")
    def test_region_filter_applied(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect()
        mock_connect_fn.return_value = mock_conn

        search_wines(query="red", region="Bordeaux")

        executed_sql = mock_cursor.execute.call_args[0][0]
        executed_params = mock_cursor.execute.call_args[0][1]

        assert "region = %s" in executed_sql
        assert "Bordeaux" in executed_params

    @patch("app.wines.psycopg2.connect")
    def test_connection_closed_on_success(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect()
        mock_connect_fn.return_value = mock_conn

        search_wines(query="test")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.wines.psycopg2.connect")
    def test_connection_closed_on_error(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect()
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_connect_fn.return_value = mock_conn

        with pytest.raises(Exception, match="DB error"):
            search_wines(query="test")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.wines.psycopg2.connect")
    def test_limit_parameter_passed(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect()
        mock_connect_fn.return_value = mock_conn

        search_wines(query="red", limit=5)

        executed_params = mock_cursor.execute.call_args[0][1]
        assert 5 in executed_params


# ---------------------------------------------------------------------------
# recommend_wine tests
# ---------------------------------------------------------------------------

class TestRecommendWine:

    @patch("app.wines.psycopg2.connect")
    def test_recommend_existing_sku_succeeds(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect(fetchone_return=(1,))
        mock_connect_fn.return_value = mock_conn

        result = recommend_wine(user_id=1, wine_sku="SKU001")

        assert result == {"status": "saved"}
        mock_conn.commit.assert_called_once()

    @patch("app.wines.psycopg2.connect")
    def test_recommend_nonexistent_sku_returns_404(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect(fetchone_return=None)
        mock_connect_fn.return_value = mock_conn

        with pytest.raises(HTTPException) as exc_info:
            recommend_wine(user_id=1, wine_sku="FAKE_SKU")

        assert exc_info.value.status_code == 404
        assert "Wine SKU not found" in exc_info.value.detail
        # Should NOT have committed anything
        mock_conn.commit.assert_not_called()

    @patch("app.wines.psycopg2.connect")
    def test_recommend_closes_connection(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect(fetchone_return=(1,))
        mock_connect_fn.return_value = mock_conn

        recommend_wine(user_id=1, wine_sku="SKU001")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.wines.psycopg2.connect")
    def test_recommend_closes_connection_on_404(self, mock_connect_fn):
        mock_conn, mock_cursor = _mock_connect(fetchone_return=None)
        mock_connect_fn.return_value = mock_conn

        with pytest.raises(HTTPException):
            recommend_wine(user_id=1, wine_sku="FAKE_SKU")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.wines.psycopg2.connect")
    def test_recommend_uses_select_for_share_to_prevent_phantom_read(self, mock_connect_fn):
        """The SKU check must acquire a shared lock (FOR SHARE) to prevent
        a concurrent transaction from deleting the wine between the SELECT
        and the INSERT (TOCTOU race condition)."""
        mock_conn, mock_cursor = _mock_connect(fetchone_return=(1,))
        mock_connect_fn.return_value = mock_conn

        recommend_wine(user_id=1, wine_sku="SKU001")

        # First execute call should be the SELECT ... FOR SHARE
        first_call_sql = mock_cursor.execute.call_args_list[0][0][0]
        assert "FOR SHARE" in first_call_sql
