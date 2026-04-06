# Task 3 — AI-Assisted Engineering

## Overview

This task takes a buggy Python FastAPI endpoint for wine search and recommendations, identifies and fixes all bugs, adds a missing feature, and provides comprehensive unit tests.

## Original Code

The original code had two endpoints:

- `GET /wines/search` — search wines by name, with optional budget and region filters
- `POST /wines/recommend` — save a wine recommendation for a user

## Part A — Bugs Found & Fixed

### Bug 1: SQL Injection (Critical)

**Original:**
```python
sql = f"SELECT sku, name, price, region FROM wines WHERE name LIKE '%{query}%'"
sql += f" AND price <= {budget_max}"
sql += f" AND region = '{region}'"
```

User input was interpolated directly into SQL via f-strings. An attacker could inject arbitrary SQL — e.g., `query = "'; DROP TABLE wines; --"`.

**Fix:** Replaced with parameterized queries using `%s` placeholders, passing values as a list to `cursor.execute()`:
```python
sql = "SELECT sku, name, price, region FROM wines WHERE name LIKE %s"
params = [f"%{query}%"]
cursor.execute(sql, params)
```

### Bug 2: Database Connections Never Closed

**Original:** Both endpoints opened a connection and cursor but never closed them. Over time this exhausts the connection pool, causing the application to hang.

**Fix:** Wrapped all database operations in `try/finally` blocks to guarantee cleanup:
```python
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
try:
    # ... database operations ...
finally:
    cursor.close()
    conn.close()
```

### Bug 3: Missing `conn.commit()` in `recommend_wine`

**Original:** The INSERT statement executed but the transaction was never committed. When the connection was garbage-collected, the transaction was implicitly rolled back — **no recommendation was ever actually saved**.

**Fix:** Added `conn.commit()` after the INSERT:
```python
cursor.execute("INSERT INTO recommendations ...", (user_id, wine_sku))
conn.commit()
```

### Bug 4 (Minor): Truthiness Check on `budget_max`

**Original:**
```python
if budget_max:
    sql += f" AND price <= {budget_max}"
```

`if budget_max:` evaluates to `False` when `budget_max=0`. While a zero budget is unlikely in practice, it's semantically incorrect.

**Fix:** Changed to explicit `None` check:
```python
if budget_max is not None:
    sql += " AND price <= %s"
    params.append(budget_max)
```

### Bug 5: Phantom Read / TOCTOU Race Condition

**Original:** Even with the SKU check added (Part B), the `SELECT` and `INSERT` are two separate statements. Between them, a concurrent transaction could `DELETE` the wine row — creating an orphaned recommendation.

This is a classic [Time-of-Check-to-Time-of-Use (TOCTOU)](https://en.wikipedia.org/wiki/Time-of-check_to_time-of-use) race condition.

**Fix:** Use `SELECT ... FOR SHARE` to acquire a shared row-level lock:
```python
cursor.execute("SELECT 1 FROM wines WHERE sku = %s FOR SHARE", (wine_sku,))
```

`FOR SHARE` prevents any concurrent transaction from deleting or updating the locked row until our transaction commits. This guarantees the wine still exists when the INSERT runs.

> **Why `FOR SHARE` and not `FOR UPDATE`?** We only need to prevent the row from being deleted/modified — we don't need to modify it ourselves. `FOR SHARE` allows other readers but blocks writers, which is the minimum lock level needed.

---

## Part B — Missing Feature: Wine SKU Validation

The `recommend_wine` endpoint saved recommendations without checking if the wine SKU actually existed. This could create orphaned references in the database.

**Fix:** Added a lookup query before the INSERT:
```python
cursor.execute("SELECT 1 FROM wines WHERE sku = %s", (wine_sku,))
if cursor.fetchone() is None:
    raise HTTPException(status_code=404, detail="Wine SKU not found")
```

## Part C — Tests

13 unit tests using `pytest` with `unittest.mock` — no real database required.

### Test Coverage

| Endpoint | Test | What it verifies |
|---|---|---|
| `search_wines` | `test_basic_search_returns_formatted_results` | Returns properly structured dict with wine fields |
| `search_wines` | `test_uses_parameterized_query_not_fstring` | SQL injection payload stays in params, not in the SQL string |
| `search_wines` | `test_budget_filter_applied` | `budget_max` adds a `price <= %s` clause |
| `search_wines` | `test_budget_zero_is_not_skipped` | `budget_max=0` still applies the filter (bug #4 regression) |
| `search_wines` | `test_region_filter_applied` | `region` adds a `region = %s` clause |
| `search_wines` | `test_connection_closed_on_success` | Cursor and connection are closed after normal execution |
| `search_wines` | `test_connection_closed_on_error` | Cursor and connection are closed even when an exception occurs |
| `search_wines` | `test_limit_parameter_passed` | `limit` value appears in query params |
| `recommend_wine` | `test_recommend_existing_sku_succeeds` | Valid SKU returns `{"status": "saved"}` and commits |
| `recommend_wine` | `test_recommend_nonexistent_sku_returns_404` | Invalid SKU raises HTTP 404, does not commit |
| `recommend_wine` | `test_recommend_closes_connection` | Connection cleaned up on success |
| `recommend_wine` | `test_recommend_closes_connection_on_404` | Connection cleaned up on 404 error path |
| `recommend_wine` | `test_recommend_uses_select_for_share_to_prevent_phantom_read` | SKU check uses `FOR SHARE` lock to prevent TOCTOU race |

### Running the Tests

```bash
cd task3-engineering

# Create a virtual environment (recommended — avoids global package conflicts)
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run tests
.venv/bin/pytest -v
```

Expected output:
```
tests/test_wines.py::TestSearchWines::test_basic_search_returns_formatted_results PASSED
tests/test_wines.py::TestSearchWines::test_uses_parameterized_query_not_fstring PASSED
tests/test_wines.py::TestSearchWines::test_budget_filter_applied PASSED
tests/test_wines.py::TestSearchWines::test_budget_zero_is_not_skipped PASSED
tests/test_wines.py::TestSearchWines::test_region_filter_applied PASSED
tests/test_wines.py::TestSearchWines::test_connection_closed_on_success PASSED
tests/test_wines.py::TestSearchWines::test_connection_closed_on_error PASSED
tests/test_wines.py::TestSearchWines::test_limit_parameter_passed PASSED
tests/test_wines.py::TestRecommendWine::test_recommend_existing_sku_succeeds PASSED
tests/test_wines.py::TestRecommendWine::test_recommend_nonexistent_sku_returns_404 PASSED
tests/test_wines.py::TestRecommendWine::test_recommend_closes_connection PASSED
tests/test_wines.py::TestRecommendWine::test_recommend_closes_connection_on_404 PASSED
tests/test_wines.py::TestRecommendWine::test_recommend_uses_select_for_share_to_prevent_phantom_read PASSED

13 passed
```

## Part D — Reflection

I used **Claude Code** (Anthropic's CLI agent) as my primary AI tool for this task. My workflow:

1. I fed the original buggy code to Claude Code and asked it to identify bugs and generate a fix plan.
2. Claude Code identified the initial four bugs and the missing feature correctly on the first pass. It generated the fixed code with inline comments explaining each change, and wrote unit tests covering both happy paths and edge cases (SQL injection, `budget_max=0`, connection cleanup on errors).
3. I then prompted Claude Code about concurrency — specifically the phantom read / TOCTOU risk in the `recommend_wine` endpoint. This led to adding `SELECT ... FOR SHARE` as a pessimistic lock, plus a dedicated test to verify the lock is present.
4. I further discussed alternative locking strategies (optimistic locking via FK constraints, distributed locks via Redis) with Claude Code. While these weren't implemented in code, the discussion is documented in the Appendix to demonstrate understanding of concurrency trade-offs.
5. The tests mock `psycopg2.connect` so no real database is needed — this makes them fast, portable, and CI-friendly.

**What worked well:** Claude Code correctly prioritized the SQL injection as the most critical bug and understood the subtle `if budget_max:` truthiness issue. It also caught the missing `conn.commit()` — a bug that would silently lose data with no error message, which is particularly dangerous in production.

**What needed human judgment:** The concurrency bug (phantom read) was something I raised myself — Claude Code's initial pass focused on the more obvious bugs and didn't flag the TOCTOU race. This is a good example of where human expertise in database concurrency adds value on top of AI-generated fixes. Choosing between `FOR SHARE`, FK constraints, and distributed locks also required architectural judgment about VinoBuzz's deployment model (single Postgres vs. microservices).

## Appendix — Alternative Concurrency Strategies

We chose `SELECT ... FOR SHARE` (pessimistic row-level locking) for the SKU validation. Here's how it compares to two other common approaches:

### Strategy 1: Pessimistic Locking — `SELECT ... FOR SHARE` (Current Implementation)

```python
cursor.execute("SELECT 1 FROM wines WHERE sku = %s FOR SHARE", (wine_sku,))
if cursor.fetchone() is None:
    raise HTTPException(status_code=404, detail="Wine SKU not found")
cursor.execute("INSERT INTO recommendations ...", (user_id, wine_sku))
conn.commit()
```

**How it works:** Acquires a shared row-level lock on the wine row. Other transactions can still read it, but cannot `DELETE` or `UPDATE` it until we commit.

| Pros | Cons |
|---|---|
| Simple, single-database solution | Holds a lock for the duration of the transaction — can cause contention under high write throughput |
| Guaranteed consistency within a single Postgres instance | Not applicable if wines and recommendations live in different databases |
| No extra infrastructure needed | Lock escalation risk if many rows are locked simultaneously |

**Best for:** Monolithic apps with a single Postgres database (like this codebase).

---

### Strategy 2: Optimistic Locking — Foreign Key Constraint + Catch IntegrityError

```python
try:
    cursor.execute(
        "INSERT INTO recommendations (user_id, wine_sku, created_at) VALUES (%s, %s, NOW())",
        (user_id, wine_sku),
    )
    conn.commit()
except psycopg2.errors.ForeignKeyViolation:
    conn.rollback()
    raise HTTPException(status_code=404, detail="Wine SKU not found")
```

**How it works:** Instead of checking first, just attempt the INSERT. If `recommendations.wine_sku` has a foreign key constraint referencing `wines.sku`, the database itself rejects the insert when the SKU doesn't exist. No explicit locking needed.

**Prerequisite:** The schema must have `FOREIGN KEY (wine_sku) REFERENCES wines(sku)`.

| Pros | Cons |
|---|---|
| No locks held — maximum concurrency | Requires FK constraint in schema (not always feasible with legacy DBs) |
| The database enforces integrity atomically | Error handling is less explicit — you're catching exceptions instead of checking upfront |
| "Ask forgiveness, not permission" — faster in the happy path (one query instead of two) | The error message from the DB is generic — you need to parse or map it to a user-friendly 404 |
| Zero TOCTOU risk — the check and write are a single atomic operation inside the DB engine | Rollback cost on failure (though negligible for single-row inserts) |

**Best for:** Well-designed schemas where FK constraints are already in place. This is arguably the most correct approach for a single-database system.

---

### Strategy 3: Distributed Lock (Redis)

```python
import redis

redis_client = redis.Redis(host="localhost", port=6379)

def recommend_wine(user_id: int, wine_sku: str):
    lock = redis_client.lock(f"wine:{wine_sku}:recommend", timeout=5)
    if not lock.acquire(blocking_timeout=3):
        raise HTTPException(status_code=409, detail="Resource busy, try again")
    try:
        # Check + Insert as before (no FOR SHARE needed — Redis lock serializes access)
        cursor.execute("SELECT 1 FROM wines WHERE sku = %s", (wine_sku,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Wine SKU not found")
        cursor.execute("INSERT INTO recommendations ...", (user_id, wine_sku))
        conn.commit()
    finally:
        lock.release()
```

**How it works:** Before touching the database, acquire a named lock in Redis keyed by wine SKU. Only one process can hold the lock at a time, serializing all recommend operations for the same SKU.

| Pros | Cons |
|---|---|
| Works across multiple services, databases, or even data centers | Adds Redis as an infrastructure dependency |
| No database-level locking — avoids DB contention entirely | Lock expiry is tricky: too short = premature release; too long = blocking on crashes |
| Can protect non-database resources too (APIs, file systems, etc.) | Not atomic with the DB transaction — if the app crashes after INSERT but before `lock.release()`, the lock may linger until TTL |
| Fine-grained: lock per SKU, not per table | Network partition between app and Redis can cause split-brain (two holders) |

**Best for:** Microservice architectures where wines and recommendations live in different services/databases, or when you need to coordinate across non-DB resources.

---

### Which Should You Pick?

| Scenario | Recommended Strategy |
|---|---|
| Single Postgres DB, schema under your control | **Optimistic (FK constraint)** — simplest, most correct |
| Single Postgres DB, can't modify schema | **Pessimistic (`FOR SHARE`)** — what we implemented |
| Multiple services / databases | **Distributed lock (Redis)** — only option that works cross-service |
| Read-heavy, write-rare workload | Any of the three — contention is negligible |
| High write throughput on same SKUs | **Optimistic (FK)** or **Distributed lock** — avoid holding DB row locks |

## File Structure

```
task3-engineering/
├── README.md            # This file — full explanation of the work
├── PLAN.md              # Initial analysis and fix plan
├── requirements.txt     # Python dependencies
├── app/
│   ├── __init__.py
│   └── wines.py         # Fixed endpoint code (with inline comments)
└── tests/
    ├── __init__.py
    └── test_wines.py    # 13 unit tests
```
