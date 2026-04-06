"""
VinoBuzz Wine Search & Recommendation API — Fixed Version

Original code had the following bugs:
  1. SQL Injection via f-string interpolation
  2. Database connections/cursors never closed (resource leak)
  3. Missing conn.commit() in recommend_wine (INSERT never persisted)
  4. `if budget_max:` is falsy for 0 — should use `is not None`
  5. Phantom read / TOCTOU race in recommend_wine — SELECT + INSERT not atomic

Missing feature added:
  - Wine SKU existence check before inserting a recommendation (with FOR SHARE lock)
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import psycopg2

router = APIRouter()

DB_CONFIG = {
    "host": "localhost",
    "database": "vinoseek",
    "user": "admin",
    "password": "password",
}


@router.get("/wines/search")
def search_wines(
    query: str,
    budget_max: Optional[int] = None,
    region: Optional[str] = None,
    limit: int = 10,
):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        # BUG FIX #1: Use parameterized queries instead of f-string interpolation
        # to prevent SQL injection attacks.
        sql = "SELECT sku, name, price, region FROM wines WHERE name LIKE %s"
        params: list = [f"%{query}%"]

        # BUG FIX #4: Use `is not None` instead of truthiness check.
        # `if budget_max:` would skip the filter when budget_max=0.
        if budget_max is not None:
            sql += " AND price <= %s"
            params.append(budget_max)

        if region is not None:
            sql += " AND region = %s"
            params.append(region)

        sql += " LIMIT %s"
        params.append(limit)

        cursor.execute(sql, params)
        results = cursor.fetchall()

        return {
            "wines": [
                {"sku": row[0], "name": row[1], "price": row[2], "region": row[3]}
                for row in results
            ]
        }
    finally:
        # BUG FIX #2: Always close cursor and connection to prevent resource leaks.
        cursor.close()
        conn.close()


@router.post("/wines/recommend")
def recommend_wine(user_id: int, wine_sku: str):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        # MISSING FEATURE: Validate that the wine SKU exists before saving.
        #
        # BUG FIX #5 (Concurrency / Phantom Read): Use SELECT ... FOR SHARE
        # to acquire a shared lock on the wine row. This prevents another
        # transaction from deleting or updating the row between our SELECT
        # and INSERT — a classic TOCTOU (Time-of-Check-to-Time-of-Use) race.
        # Without the lock, a concurrent DELETE could remove the wine after
        # we verify it exists but before we insert the recommendation,
        # creating an orphaned reference.
        cursor.execute("SELECT 1 FROM wines WHERE sku = %s FOR SHARE", (wine_sku,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Wine SKU not found")

        cursor.execute(
            "INSERT INTO recommendations (user_id, wine_sku, created_at) VALUES (%s, %s, NOW())",
            (user_id, wine_sku),
        )

        # BUG FIX #3: Commit the transaction so the INSERT is actually persisted.
        # Without this, the row is never saved — the implicit rollback on
        # connection close discards it.
        conn.commit()

        return {"status": "saved"}
    finally:
        # BUG FIX #2: Always close cursor and connection.
        cursor.close()
        conn.close()
