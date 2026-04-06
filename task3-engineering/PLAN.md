# Task 3 — AI-Assisted Engineering: Plan

## Part A — Bugs Found

### Bug 1: SQL Injection Vulnerability (Critical)
**Location:** `search_wines` and `recommend_wine` — lines using f-strings to build SQL.

```python
sql = f"SELECT ... WHERE name LIKE '%{query}%'"
sql += f" AND price <= {budget_max}"
sql += f" AND region = '{region}'"
```

**Problem:** User input is interpolated directly into SQL strings. An attacker can inject arbitrary SQL (e.g., `query = "'; DROP TABLE wines; --"`).

**Fix:** Use parameterized queries with `%s` placeholders and pass values as a tuple to `cursor.execute()`. Build the WHERE clause dynamically with a params list.

---

### Bug 2: Database Connection & Cursor Never Closed
**Location:** Both endpoints.

**Problem:** `conn` and `cursor` are opened but never closed. This leaks database connections and will eventually exhaust the connection pool, causing the application to hang or crash.

**Fix:** Use `try/finally` blocks (or context managers) to guarantee `cursor.close()` and `conn.close()` are called, even on exceptions.

---

### Bug 3: Missing `conn.commit()` in `recommend_wine`
**Location:** `recommend_wine` endpoint.

**Problem:** After `cursor.execute(INSERT ...)`, the transaction is never committed. The row is inserted within a transaction that is implicitly rolled back when the connection is garbage-collected, so **no recommendation is ever actually saved**.

**Fix:** Call `conn.commit()` after the INSERT.

---

### Bug 4 (Minor): `if budget_max:` is falsy for `0`
**Location:** `search_wines`, budget filter condition.

**Problem:** `if budget_max:` evaluates to `False` when `budget_max=0`. While unlikely in production (budget of $0), it's semantically wrong. The correct check is `if budget_max is not None:`.

**Fix:** Use `is not None` checks for optional parameters.

---

### Bug 5: Phantom Read / TOCTOU Race in `recommend_wine`
**Location:** `recommend_wine` endpoint — the SKU existence check + INSERT sequence.

**Problem:** Even after adding the SKU validation (Part B), there is a concurrency issue: between the `SELECT` that checks if the wine exists and the `INSERT` that saves the recommendation, another transaction could `DELETE` the wine. This is a classic Time-of-Check-to-Time-of-Use (TOCTOU) race condition / phantom read.

**Fix:** Use `SELECT ... FOR SHARE` to acquire a shared row-level lock on the wine. This prevents concurrent `DELETE` or `UPDATE` on that row until our transaction commits, ensuring the wine still exists when we insert the recommendation.

---

## Part B — Missing Feature: Wine SKU Validation

**Location:** `recommend_wine` endpoint.

**Problem:** The endpoint blindly inserts a recommendation without verifying the wine SKU exists. This can create orphaned references.

**Fix:** Before inserting, query `SELECT 1 FROM wines WHERE sku = %s`. If no row is returned, raise `HTTPException(status_code=404, detail="Wine SKU not found")`.

---

## Part C — Test Strategy

**Framework:** `pytest` with `unittest.mock` for mocking `psycopg2.connect`.

**Approach:** Unit tests that mock the database layer so no real Postgres is needed. Tests will verify:

1. **`search_wines`** — basic query returns formatted results
2. **`search_wines`** — SQL injection is prevented (parameterized queries used)
3. **`search_wines`** — optional filters (`budget_max`, `region`) are applied correctly
4. **`search_wines`** — connection is always closed (even on error)
5. **`recommend_wine`** — happy path with existing SKU commits and returns success
6. **`recommend_wine`** — non-existent SKU returns 404
7. **`recommend_wine`** — connection is always closed

**How to run:**
```bash
cd task3-engineering
pip install -r requirements.txt
pytest -v
```

---

## File Structure

```
task3-engineering/
├── PLAN.md              # This file
├── requirements.txt     # Dependencies
├── app/
│   ├── __init__.py
│   └── wines.py         # Fixed endpoint code
└── tests/
    ├── __init__.py
    └── test_wines.py    # Unit tests
```

---

## Part D — Reflection

Documented in the test file header and below after implementation.
