# CLAUDE.md — Task 1: Conversational Wine Recommendation

## Project Overview

Multi-agent conversational wine recommendation system built with FastAPI + OpenAI Agents SDK + Azure OpenAI. Dual-path architecture: Planner flow (structured preferences) and Explorer flow (vague/open-ended requests).

## Quick Reference

```bash
# Dev server
make dev                 # http://localhost:8000

# Tests (89 tests, no LLM key needed)
make test                # or: pytest tests/ -v

# Lint & format
make lint && make format
```

## Architecture

```
User → POST /sommelier/chat → SommelierMode orchestrator
  ├─ Coordinator (gpt-4o-mini) → routes to:
  │   ├─ Planner Flow: PreferencePlanner ∥ FilterBuilder → wine_db_tool → Generator
  │   └─ Explorer Flow: Explorer agent (autonomous with tools)
  └─ SSE stream response with citations
```

**Key files:**
- `app/biz/agent/sommelier/mode.py` — Main orchestrator, all flow logic
- `app/biz/tools/wine_db_tool.py` — Pure Python search/filter/score (no LLM)
- `app/config/sommelier.yaml` — All agent models/temperatures in one place
- `app/prompts/*.md` — Agent system prompts (Markdown)

## Coding Conventions

- **Python 3.11+**, type hints everywhere
- **Pydantic v2** for all schemas (use `SettingsConfigDict`, not class-based `Config`)
- **Async-first**: all agent interactions are async, use `asyncio.TaskGroup` for parallelism
- **No LLM in tests**: mock `agents.Runner` for orchestrator tests, test deterministic logic directly
- Agent names in code must match `sommelier.yaml` keys exactly
- Prompt files must exist at `app/prompts/{prompt_name}.md` for every agent
- Wine SKUs follow format: `{COUNTRY_CODE}-{REGION_CODE}-{NUMBER}` (e.g., `FR-BDX-001`)
- Citations in LLM output use `[n](#SKU)` format — parsed by `utils/citation.py`

## Agent Configuration

All agents configured via `app/config/sommelier.yaml` with YAML anchors:
- `&model_heavy` (gpt-4o) — used by: PreferencePlanner, Generator, Explorer
- `&model_light` (gpt-4o-mini) — used by: Coordinator, FilterBuilder, QueryRefinement

Change model deployment names in 2 lines to swap all agents.

## Azure OpenAI Setup

The app uses `AsyncAzureOpenAI` client set via `set_default_openai_client()` at startup in `main.py`. Tracing is disabled (would 401 against Azure endpoint).

Required `.env` vars:
```
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

## Testing Strategy

**89 tests across 8 files — all run without LLM:**

| Test file | What it covers |
|---|---|
| `test_wine_db_tool.py` (22) | Search filtering, scoring, relaxation, formatting |
| `test_mode.py` (16) | Orchestrator: context building, text extraction, flow routing, error handling |
| `test_agent_config.py` (13) | Config loading, prompt file integrity |
| `test_sommelier_api.py` (9) | Input validation, SSE event formatting |
| `test_web_search_tool.py` (9) | Wine knowledge search |
| `test_schemas.py` (8) | Pydantic schema defaults, construction, serialization |
| `test_chat_interface.py` (6) | Retry logic: success, failure, max retries |
| `test_citation.py` (6) | Citation parsing, dedup, unknown SKU |

**For LLM integration testing:** use `postman/VinoBuzz_Sommelier.postman_collection.json` (11 requests, 4 scenarios).

## Common Tasks

### Adding a new wine to inventory
Edit `app/data/wines.py` → add dict to `WINE_INVENTORY` list. Required fields: `sku`, `name`, `type`, `grape`, `region`, `country`, `vintage`, `price_hkd`, `tasting_notes`, `occasions`, `body`, `sweetness`, `food_pairing`, `rating`, `in_stock`.

### Adding a new agent
1. Create agent function in `app/biz/agent/sommelier/agents/{name}.py`
2. Add prompt at `app/prompts/{name}.md`
3. Add config entry in `app/config/sommelier.yaml`
4. Wire into `mode.py` orchestrator
5. Add config test in `test_agent_config.py`

### Changing model deployment names
Edit `app/config/sommelier.yaml` — change `&model_heavy` and `&model_light` anchors only.

## Known Constraints

- Wine inventory is hardcoded (35 wines) — designed so `wine_db_tool` interface stays the same whether backed by list or Postgres
- Sessions are in-memory, lost on restart — designed for Redis swap
- `openai-agents` SDK v0.13.5: no `wait_for_completion()` on `RunResultStreaming` — consume `stream_events()` instead
- Tracing disabled because Azure OpenAI keys don't work with OpenAI's trace API

## Audit

See `AUDIT.md` for full requirement-to-implementation mapping with live test results.
