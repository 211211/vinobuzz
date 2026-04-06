# Task 1 — Audit Checklist

This file maps every requirement from `requirement.md` (Task 1) to what was implemented, with pass/fail status and evidence.

**Last audited:** 2026-04-06
**Test result:** 89 passed in 0.70s
**Live test:** Both Planner and Explorer flows verified against Azure OpenAI

---

## Functional Requirements

### REQ-1: Engages the user in a short conversation to understand their needs

> "Engages the user in a short conversation to understand their needs (budget, occasion, wine type, regional preference)"

| Sub-requirement | Status | Evidence |
|---|---|---|
| Understands **budget** | PASS | `PreferencePlan.gathered.budget_min/max` extracted by preference_planner agent; `WineFilter.budget_min/max` used in search; `_score_wines()` applies budget scoring |
| Understands **occasion** | PASS | `PreferencePlan.gathered.occasion` extracted; `WineFilter.occasion_tags` filters wines; inventory has `occasions` field per wine |
| Understands **wine type** | PASS | `PreferencePlan.gathered.wine_type` extracted; `WineFilter.type_filter` hard-filters in search |
| Understands **regional preference** | PASS | `PreferencePlan.gathered.region/country` extracted; `WineFilter.region_filter/country_filter` used in search |
| **Multi-turn** conversation | PASS | `SommelierInput.message_history` accepts up to 20 messages; generator prompt instructs asking follow-ups when confidence < 0.4 |

**Test coverage:**
- `test_wine_db_tool.py::TestSearchWines::test_search_by_type_red/white/sparkling` — type filtering works
- `test_wine_db_tool.py::TestSearchWines::test_search_budget_max` — budget filtering works
- `test_wine_db_tool.py::TestSearchWines::test_search_by_country` — country filtering works
- `test_wine_db_tool.py::TestSearchWines::test_search_by_region` — region filtering works
- `test_wine_db_tool.py::TestSearchWines::test_search_by_occasion` — occasion filtering works
- `test_wine_db_tool.py::TestSearchWines::test_combined_filters` — realistic multi-filter scenario
- `test_sommelier_api.py::TestSommelierInput::test_history_limited_to_20` — conversation history capped
- `test_schemas.py::TestGatheredPreferences` — preference schema defaults and construction
- `test_schemas.py::TestWineFilter` — filter schema defaults and construction

---

### REQ-2: Makes a judgment call — when to recommend vs. ask a follow-up

> "Makes a judgment call — when does it have enough info to recommend vs. when should it ask a follow-up?"

| Sub-requirement | Status | Evidence |
|---|---|---|
| Confidence scoring | PASS | `PreferencePlan.confidence` (0.0–1.0) computed by preference_planner agent |
| Recommend when confident | PASS | Generator prompt: "If wines > 0 AND confidence >= 0.4 → recommend 1–3 wines" |
| Ask follow-up when not confident | PASS | Generator prompt: "If confidence < 0.4 → ask ONE targeted follow-up question" |
| Limit follow-ups | PASS | Generator prompt: "Never ask more than 3 follow-up questions total"; config `max_followup_questions: 3` |
| Dual-path routing | PASS | Coordinator routes specific requests → Planner flow, vague requests → Explorer flow |

**Test coverage:**
- `test_mode.py::TestSommelierModeRun::test_run_planner_flow_routing` — verifies Planner path executes when coordinator routes to it
- `test_mode.py::TestSommelierModeRun::test_run_explorer_flow_routing` — verifies Explorer path executes when coordinator routes to it
- `test_mode.py::TestBuildGeneratorContext` — verifies confidence is injected into generator context
- `test_schemas.py::TestPreferencePlan` — validates confidence field in plan schema

**Live verification:**
- Scenario 1 (specific request) → Coordinator routed to Planner → extracted `budget_max: 500, wine_type: red, country: France, occasion: business dinner` → returned 2 wines with citations ✅
- Scenario 2 (vague request) → Coordinator routed to Explorer → returned 3 diverse wines (red/white/sparkling) ✅

---

### REQ-3: Returns 1–3 wine recommendations with a brief explanation

> "Returns 1–3 wine recommendations with a brief explanation for each"

| Sub-requirement | Status | Evidence |
|---|---|---|
| 1–3 recommendations | PASS | Scenario 1 returned 2 wines, Scenario 2 returned 3 wines — both within spec |
| Brief explanation per wine | PASS | Each wine had 1–2 sentence explanation (e.g., "A classic Bordeaux from Saint-Julien, offering bold blackcurrant and cedar notes") |
| Citation format for traceability | PASS | `[n](#SKU)` format in generator output; `parse_citations()` extracts structured `WineCitation` objects |
| Wine data with meaningful fields | PASS | 35-wine inventory in `wines.py` with sku, name, type, grape, region, country, vintage, price_hkd, tasting_notes, occasions, body, sweetness, food_pairing, rating |

**Test coverage:**
- `test_citation.py::TestParseCitations` — 6 tests: single/multiple citations, dedup, unknown SKU, field validation
- `test_mode.py::TestExtractFinalText` — 4 tests: text extraction from various result formats

**Live verification:**
- Planner flow returned: Chateau Leoville-Barton 2019 [1](#FR-BDX-002) @ HK$480, Chateau Sociando-Mallet 2018 [2](#FR-BDX-003) @ HK$320 ✅
- Explorer flow returned: Antinori Tignanello 2019 [1](#IT-TUS-001), Kistler Chardonnay [2](#US-SON-001), Veuve Clicquot [3](#FR-CHP-002) ✅
- All citations parsed into structured metadata with id, name, type, region, price_hkd ✅

---

### REQ-4: Wine data

> "You can use any wine data you like (invent it, use a public dataset, or hardcode a small inventory)"

| Sub-requirement | Status | Evidence |
|---|---|---|
| Wine inventory exists | PASS | `app/data/wines.py` — 35 wines hardcoded |
| Diverse wine regions | PASS | France, Italy, Spain, USA, Australia, New Zealand, Chile, Argentina, South Africa, Germany, Japan, Portugal |
| Realistic pricing (HKD) | PASS | Prices range from HK$120 to HK$3,800 |
| Wine knowledge base | PASS | `app/data/wine_knowledge.py` — pairing rules, region facts, grape profiles |

**Test coverage:**
- `test_web_search_tool.py` — 9 tests: pairing lookup, region facts, grape profiles, case insensitivity, combined queries

---

## Deliverables

### DEL-1: Screenshot(s) or diagram of workflow

| Sub-requirement | Status | Evidence |
|---|---|---|
| Workflow diagram | PASS | `README.md` contains Mermaid flowchart of dual-path architecture (Coordinator → Planner/Explorer paths) |
| Agent summary table | PASS | `README.md` has agent table with model, temperature, and role for each agent |

---

### DEL-2: Conversation demo showing at least 2 different user scenarios

| Sub-requirement | Status | Evidence |
|---|---|---|
| At least 2 demo scenarios | PASS | `README.md` has 2 scripted demos + Postman collection with 11 requests across 4 scenarios |
| Different user intents | PASS | Scenario 1: specific (Planner) + Scenario 2: vague (Explorer) — both verified live |

**Live conversation transcripts (2026-04-06):**

**Scenario 1 — Planner Flow (specific request):**
```
Request: "I need a red wine for a business dinner, budget around HK$500, preferably French"
Flow:    Coordinator → PreferencePlanner ∥ FilterBuilder → wine_db_tool → Generator

Response: 2 recommendations with citations:
  1. Chateau Leoville-Barton 2019 [1](#FR-BDX-002) — HK$480, Bordeaux
  2. Chateau Sociando-Mallet 2018 [2](#FR-BDX-003) — HK$320, Bordeaux

Metadata: preferences_gathered = {occasion: "business dinner", budget_max: 500, wine_type: "red", country: "France"}
```

**Scenario 2 — Explorer Flow (vague request):**
```
Request: "Surprise me with something interesting for tonight"
Flow:    Coordinator → Explorer (autonomous with tools)

Response: 3 recommendations spanning red/white/sparkling:
  1. Antinori Tignanello 2019 [1](#IT-TUS-001) — HK$980, Tuscany
  2. Kistler Sonoma Coast Chardonnay 2021 [2](#US-SON-001) — HK$550, Sonoma
  3. Veuve Clicquot Yellow Label Brut NV [3](#FR-CHP-002) — HK$420, Champagne
```

---

### DEL-3: Written explanation (max 300 words)

| Sub-requirement | Status | Evidence |
|---|---|---|
| Design rationale | PASS | `README.md` "Design Rationale" section covers: dual-path architecture, Python orchestration, context injection, hardcoded inventory |
| Trade-offs discussed | PASS | `README.md` "Trade-offs" section exists |
| Under 300 words | PASS | Design rationale section is ~270 words |

---

## Architecture Quality (Beyond Requirements)

These aren't explicitly required but demonstrate engineering quality:

| Aspect | Status | Evidence |
|---|---|---|
| Streaming responses (SSE) | PASS | `streaming.py` + `EventSourceResponse` in router — real-time UX |
| Error handling | PASS | `mode.py` wraps agent runs in try/except, yields error SSE events |
| Retry with exponential backoff | PASS | `chat_interface.py` retries agent calls up to 3 times |
| Progressive filter relaxation | PASS | `wine_db_tool._relax_and_search()` — 4-step relaxation strategy |
| Parallel agent execution | PASS | `mode.py._planner_flow()` runs PreferencePlanner + FilterBuilder concurrently via `asyncio.TaskGroup` |
| Configurable agents (YAML) | PASS | `sommelier.yaml` — model/temperature per agent, search params, conversation limits |
| Separation of concerns | PASS | Clean layering: api → biz/agent → tools → data |
| Test suite | PASS | 8 test files, 89 tests covering all deterministic logic |
| Postman collection | PASS | `postman/VinoBuzz_Sommelier.postman_collection.json` — 11 requests, 4 scenarios |

---

## Test Execution

Run all tests to verify:

```bash
cd task1-wine-recommendation
pip install -e ".[dev]"   # or: poetry install
pip install pytest-asyncio  # required for async tests
pytest -v
```

### Expected Results

| Test File | Tests | What it covers |
|---|---|---|
| `test_wine_db_tool.py` | 22 | Search filtering, scoring, relaxation, formatting |
| `test_sommelier_api.py` | 9 | Input validation, SSE event formatting |
| `test_citation.py` | 6 | Citation parsing, deduplication, unknown SKU handling |
| `test_mode.py` | 16 | Orchestrator: context building, text extraction, flow routing, error handling |
| `test_chat_interface.py` | 6 | Retry logic: success, retry-on-failure, max retries, context passthrough |
| `test_schemas.py` | 8 | Pydantic schemas: defaults, construction, serialization |
| `test_agent_config.py` | 13 | Config loading: model/temperature per agent, prompt files, integrity |
| `test_web_search_tool.py` | 9 | Knowledge search: pairings, regions, grapes, fallback |
| **Total** | **89** | All deterministic logic — no LLM API key required |

**Last run:** 89 passed in 0.70s ✅

---

## Gaps & Recommendations

| Gap | Severity | Status |
|---|---|---|
| ~~No integration test with real LLM~~ | ~~Low~~ | RESOLVED — live-tested both flows against Azure OpenAI |
| ~~Demo transcripts may be missing~~ | ~~Medium~~ | RESOLVED — live transcripts captured above, Postman collection added |
| ~~Orchestrator untested~~ | ~~Medium~~ | RESOLVED — `test_mode.py` covers context building, text extraction, flow routing, error handling |
| ~~Retry logic untested~~ | ~~Medium~~ | RESOLVED — `test_chat_interface.py` covers retry behavior |
| No load/concurrency testing | Low | Not required for take-home, but worth noting for production readiness |
