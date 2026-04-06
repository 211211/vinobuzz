# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

VinoBuzz is an AI Engineering take-home assignment with three tasks:

- **task1-wine-recommendation/** — Multi-agent conversational wine recommendation system (FastAPI + OpenAI Agents SDK)
- **task2-openclaw-report/** — Research essay (no code)
- **task3-engineering/** — Bug fixes, missing feature, and tests for a legacy FastAPI wine API

## Commands

### Task 1: Wine Recommendation

```bash
cd task1-wine-recommendation
poetry install                    # Install dependencies
make dev                          # Run dev server (uvicorn, port 8000)
make test                         # pytest tests/ -v
make lint                         # ruff check app/ tests/
make format                       # ruff format app/ tests/
pytest tests/test_wine_db_tool.py -v -k "test_search"  # Single test
```

Requires `OPENAI_API_KEY` in `.env` (see `.env.example`).

### Task 3: Engineering

```bash
cd task3-engineering
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest -v               # Run all 13 tests
```

## Task 1 Architecture

### Dual-Path Agent Orchestration

The system routes through a **Coordinator** agent that picks one of two flows:

**Planner Flow** (specific requests like "red wine under $300 for steak dinner"):
1. **PreferencePlanner** + **FilterBuilder** run in parallel (`asyncio.TaskGroup`)
2. `wine_db_tool.search_wines()` executes (pure Python, no LLM call)
3. Results injected into **Generator** agent's system prompt
4. Generator recommends wines or hands off to **QueryRefinement** if results are insufficient

**Explorer Flow** (vague requests like "surprise me" or "what's good?"):
- Single autonomous **Explorer** agent with `wine_db_search` and `wine_knowledge_search` tools

### Key Design Decisions

- **Pre-computed context**: Search results are injected into prompts rather than having agents call tools at runtime — reduces latency and enables retries.
- **Graceful degradation**: When search returns < 3 results, filters are progressively relaxed (drop region → expand budget ±20% → drop grape/body/sweetness → keep only type).
- **Model config via YAML anchors**: `app/config/sommelier.yaml` defines `heavy` (gpt-4o) and `light` (gpt-4o-mini) anchors — change 2 lines to swap all models.
- **Structured outputs**: PreferencePlanner, FilterBuilder, and QueryRefinement return Pydantic models, not free text.

### Request Flow

```
POST /sommelier/chat → SSE stream
  Router (app/api/routers/sommelier.py)
  → SommelierMode.run() (app/biz/agent/sommelier/mode.py)
  → Coordinator → Planner or Explorer flow
  → SSE events: metadata → agent_updated → data (streaming) → metadata (citations) → done
```

### Data Layer

- `app/data/wines.py` — Hardcoded wine inventory (~35-40 wines with SKU, price, region, tasting notes, etc.)
- `app/data/wine_knowledge.py` — Pairing rules, region facts, grape profiles (used by Explorer's knowledge search tool)
- `app/biz/tools/wine_db_tool.py` — Fuzzy scoring search with weighted attributes and auto-relaxation
- `app/biz/tools/web_search_tool.py` — Searches hardcoded knowledge base (no external API calls)

### Agent Prompts

All agent instructions live as Markdown files in `app/prompts/`. Each corresponds to an agent in `app/biz/agent/sommelier/agents/`.

### Streaming Events

Uses SSE via `sse-starlette`. Event types: `metadata`, `agent_updated`, `data`, `done`, `error`. Content types: `thoughts` (debug) and `final_answer` (user-facing). Format helpers in `app/core/streaming.py`.

## Task 3 Architecture

`app/wines.py` — FastAPI endpoints for wine CRUD against PostgreSQL (psycopg2). Tests use `unittest.mock` to mock database connections. Key fixes include SQL injection prevention (parameterized queries), budget filter truthiness bug (`budget is not None`), and connection cleanup.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| AI/Agents | OpenAI Agents SDK (openai-agents v0.0.17) |
| LLM Models | gpt-4o (heavy), gpt-4o-mini (light) |
| Streaming | sse-starlette |
| Config | Pydantic Settings + YAML |
| Testing | pytest, pytest-asyncio |
| Linting | ruff |
| Python | 3.11+ |
