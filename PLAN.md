# VinoBuzz AI Sommelier — Implementation Plan

## Overview

Multi-agent conversational wine recommendation system built with FastAPI + OpenAI Agents SDK.
Architecture modeled after sensei-server's BING_MDI mode: a Python orchestrator class (`SommelierMode`) coordinating specialized agents through dual-path routing — structured planner flow for specific requests, autonomous explorer flow for open-ended ones.

---

## Architecture

```
vinobuzz/
├── app/
│   ├── main.py                              # FastAPI app, CORS, lifespan
│   ├── settings.py                          # Env config (Pydantic BaseSettings)
│   ├── config/
│   │   └── sommelier.yaml                   # Agent configs (model, temperature, prompt)
│   ├── api/
│   │   └── routers/
│   │       └── sommelier.py                 # POST /sommelier/chat → SSE stream
│   ├── biz/
│   │   ├── agent/
│   │   │   └── sommelier/
│   │   │       ├── mode.py                  # SommelierMode — Python orchestrator (like BingMDIMode)
│   │   │       ├── agents/
│   │   │       │   ├── coordinator.py       # Routes: planner_flow vs explorer_flow
│   │   │       │   ├── preference_planner.py # Extracts structured prefs (like QueryPlanner)
│   │   │       │   ├── filter_builder.py    # Builds search filters (like QueryBuilder)
│   │   │       │   ├── generator.py         # Builds recommendation response (with handoff)
│   │   │       │   ├── query_refinement.py  # Retry: transforms failed queries (like QueryTransformation)
│   │   │       │   └── explorer.py          # Autonomous tool-enabled agent (like Analyzer)
│   │   │       ├── schemas/
│   │   │       │   ├── preference_plan.py   # PreferencePlan structured output
│   │   │       │   ├── wine_filter.py       # WineFilter structured output
│   │   │       │   └── recommendation.py    # Citation structures
│   │   │       └── utils/
│   │   │           └── citation.py          # Wine citation builder
│   │   └── tools/
│   │       ├── wine_db_tool.py              # Search/filter hardcoded inventory
│   │       └── web_search_tool.py           # Tavily web search (stubbed with wine_knowledge fallback)
│   ├── core/
│   │   ├── streaming.py                     # SSE events: EventType, EventStreamOutput, ContentType
│   │   ├── chat_interface.py                # OpenAI Agents SDK streaming wrapper
│   │   └── models.py                        # Pydantic request/response schemas
│   ├── data/
│   │   ├── wines.py                         # Hardcoded wine inventory (~30-40 wines)
│   │   └── wine_knowledge.py               # Pairing rules, region facts, grape descriptions
│   └── prompts/                             # System prompts (file-based, swappable like Langfuse)
│       ├── coordinator.md
│       ├── preference_planner.md
│       ├── filter_builder.md
│       ├── generator.md
│       ├── query_refinement.md
│       └── explorer.md
├── tests/
│   ├── test_sommelier_api.py
│   ├── test_preference_planner.py
│   ├── test_wine_db_tool.py
│   └── test_generator.py
├── pyproject.toml
├── Makefile
├── .env.example
└── README.md
```

---

## Dual-Path Flow (Modeled After BING_MDI)

```
POST /sommelier/chat
  │
  ▼
┌──────────────────────────────────────────────────────────┐
│  SommelierMode.run()  (Python async generator)           │
│  - Init trace (request_id, session_id)                   │
│  - Limit message_history to last 20 messages             │
│  - Call Coordinator Agent                                │
└──────────────────────┬───────────────────────────────────┘
                       │
             ┌─────────┴──────────┐
             │                    │
             ▼                    ▼
      Planner Flow           Explorer Flow
   (user gave ≥1 hint:      (user is vague:
    type, budget, region,    "surprise me",
    occasion, food)          "pick something nice",
                             general wine questions)
             │                    │
             │                    ▼
             │              ┌──────────────┐
             │              │   Explorer   │  Tool-enabled autonomous agent
             │              │   Agent      │  - calls wine_db_tool.search()
             │              │   (gpt-4o)   │  - calls web_search_tool.search()
             │              │              │  Decides on its own when to search,
             │              │              │  what to ask, when to recommend.
             │              └──────┬───────┘
             │                     │
             ▼                     │
      ┌────────────────┐           │
      │ Preference     │─┐         │
      │ Planner        │ │         │
      │ (gpt-4o)       │ │parallel │
      ├────────────────┤ │ via     │
      │ Filter         │ │ asyncio │
      │ Builder        │ │TaskGroup│
      │ (gpt-4o-mini)  │─┘         │
      └───────┬────────┘           │
              │                    │
              ▼                    │
      ┌────────────────┐           │
      │ wine_db_tool   │           │
      │ .search()      │  (Python, │
      │ (no LLM)       │  no LLM)  │
      └───────┬────────┘           │
              │                    │
              ▼                    │
      ┌────────────────────┐       │
      │ Generator Agent    │       │
      │ (gpt-4o)           │       │
      │ with handoff tool: │       │
      │ handoff_to_refine  │       │
      └───┬──────────┬─────┘       │
          │      (insufficient     │
          │       context?)        │
          │          ▼             │
          │  ┌─────────────────┐   │
          │  │ Query Refinement│   │
          │  │ Agent           │   │
          │  │ (gpt-4o-mini)   │   │
          │  │ → 3-5 new       │   │
          │  │   queries       │   │
          │  │ → re-search     │   │
          │  │ → Generator     │   │
          │  │   (no handoff)  │   │
          │  └────────┬────────┘   │
          │           │            │
          ▼           ▼            ▼
      ┌────────────────────────────────┐
      │  Citation Builder              │
      │  [n](#wine_sku) → Citation obj │
      │  with wine details + match why │
      └───────────────┬────────────────┘
                      │
                      ▼
                 SSE Stream
      metadata → agent_updated → data → citations → done
```

---

## Agent Breakdown

### Coordinator Agent (`agents/coordinator.py`)

**Role:** Lightweight routing decision — does NOT generate user-facing content.

**Model:** `gpt-4o-mini` (cheap, fast)

**Input:** Full message history

**Tools (handoff functions):**
- `handoff_to_planner()` — user provided wine preferences
- `handoff_to_explorer()` — user is vague or asking general wine questions

**Prompt logic:**
- If message mentions ANY of: wine type, budget, region, occasion, food pairing, grape → `handoff_to_planner`
- If message is vague ("recommend something", "what's good?", "surprise me") → `handoff_to_explorer`
- If user asks general wine knowledge ("what's the difference between Pinot Noir and Cabernet?") → `handoff_to_explorer`
- Default to `handoff_to_planner` if ambiguous

**Streams:** Coordinator thinking/reasoning as `AGENT_UPDATED` events (not shown to user in final UI, but useful for debugging).

---

### Preference Planner Agent (`agents/preference_planner.py`)

**Role:** Extract structured preferences from conversation. Like BING_MDI's QueryPlanner.

**Model:** `gpt-4o` (needs good comprehension)

**Input:** Full message history

**Output type:** `PreferencePlan` (Pydantic structured output):
```python
class GatheredPreferences(BaseModel):
    occasion: Optional[str]         # "business dinner", "casual", "romantic", "celebration", "gift"
    budget_min: Optional[int]       # In HKD
    budget_max: Optional[int]       # In HKD
    wine_type: Optional[str]        # "red", "white", "sparkling", "rose"
    region: Optional[str]           # "France", "Italy", "Bordeaux", etc.
    country: Optional[str]          # Normalized country
    grape: Optional[str]            # "Cabernet Sauvignon", "Pinot Noir", etc.
    taste_notes: list[str]          # ["dry", "full-bodied", "fruity"]
    food_pairing: Optional[str]     # "steak", "seafood", "cheese"
    quantity: int = 1               # Bottles needed

class PreferencePlan(BaseModel):
    justification: str              # Why this plan
    preferences: GatheredPreferences
    search_queries: list[str]       # 1-3 decomposed search queries
    confidence: float               # 0.0-1.0 — how complete the preferences are
    user_language: str = "en"       # Language detection for response
```

**Key behaviors:**
- Extracts ALL preferences mentioned across full conversation history, not just latest message
- Decomposes complex requests: "Compare a Bordeaux and a Barolo under $500" → 2 search queries
- Detects currency and converts to HKD mentally
- Confidence < 0.4 with 0 search results will trigger Generator to ask follow-up

---

### Filter Builder Agent (`agents/filter_builder.py`)

**Role:** Translate preferences into concrete search filters. Like BING_MDI's QueryBuilder.

**Model:** `gpt-4o-mini` (simple structured task)

**Input:** Message history + wine inventory field schema (type, region, country, price range, occasions)

**Output type:** `WineFilter` (Pydantic structured output):
```python
class WineFilter(BaseModel):
    justification: str
    type_filter: Optional[str]         # "red", "white", "sparkling", "rose"
    budget_min: Optional[int]          # HKD
    budget_max: Optional[int]          # HKD
    country_filter: Optional[str]
    region_filter: Optional[str]
    occasion_tags: list[str]           # Match against wine.occasions
    grape_filter: Optional[str]
    body_filter: Optional[str]         # "light", "medium", "full"
    sweetness_filter: Optional[str]    # "dry", "semi-sweet", "sweet"
    food_pairing_filter: Optional[str]
    exclude_skus: list[str]            # Previously recommended SKUs (avoid repeats)
```

**Key behaviors:**
- Maps user language to inventory field values (e.g., "something bold" → body="full")
- Tracks previously recommended SKUs from conversation to avoid repeats
- Runs in **parallel** with PreferencePlanner via `asyncio.TaskGroup()`

---

### Generator Agent (`agents/generator.py`)

**Role:** Build final user-facing response — either recommend wines or ask a follow-up. Like BING_MDI's Generator.

**Two modes (like BING_MDI):**

1. **With handoff** (`generator_with_handoff`) — first attempt
   - Model: `gpt-4o`
   - Tool: `handoff_to_query_refinement()` — if wine context is insufficient
   - Used in first pass of planner flow

2. **Without handoff** (`generator`) — after retry
   - Model: `gpt-4o`
   - No tools, must answer with whatever context is available
   - Used after QueryRefinement re-search

**Input construction (injected into system prompt):**
```markdown
## User Preferences
{preference_plan.preferences as YAML}
Confidence: {preference_plan.confidence}

## Matching Wines
<<<WINE>>>
SKU: FR-BDX-001
Name: Chateau Margaux 2018
Type: Red | Region: Bordeaux, France
Price: HK$1,800
Tasting: Elegant, dark fruit, silky tannins
Occasions: business dinner, celebration, gift
Food pairing: beef, lamb, aged cheese
Rating: 4.8/5
<<<END WINE>>>

<<<WINE>>>
...
<<<END WINE>>>

## Wine Knowledge Context (if available)
{web_search_results or hardcoded pairing tips}
```

**Prompt decision rules:**
- If matching wines > 0 AND confidence >= 0.4 → recommend 1-3 wines with `[n](#sku)` citations
- If matching wines == 0 AND confidence >= 0.6 → apologize, suggest adjusting criteria
- If confidence < 0.4 → ask ONE targeted follow-up question (most impactful missing field)
- Never ask more than 3 follow-ups across the conversation (count from history)
- If already asked 3 follow-ups → recommend with best available, even if imperfect

**Citation format in output:**
```
I'd recommend the **Chateau Leoville-Barton 2019** [1](#FR-BDX-005) — a classic
Saint-Julien that's perfect for business dinners. At HK$480, it's right in your budget.
```

**Streams:** Token-by-token via SSE `DATA` events.

---

### Query Refinement Agent (`agents/query_refinement.py`)

**Role:** Transform failed search queries when Generator hands off. Like BING_MDI's QueryTransformation.

**Model:** `gpt-4o-mini`

**Trigger:** Only when Generator calls `handoff_to_query_refinement()`

**Input:** Original PreferencePlan + original search results (empty or poor)

**Output:**
```python
class QueryRefinement(BaseModel):
    justification: str
    refined_queries: list[str]      # 3-5 alternative search queries
    relaxed_filters: WineFilter     # Loosened filters (wider budget, no region, etc.)
```

**Relaxation strategy:**
1. Remove region filter (keep country)
2. Expand budget by ±30%
3. Remove grape filter
4. Remove body/sweetness filters
5. If still nothing: remove all filters except type

**After refinement:** Re-runs `wine_db_tool.search()` → Generator (without handoff) answers with whatever is available.

---

### Explorer Agent (`agents/explorer.py`)

**Role:** Autonomous tool-enabled agent for vague or open-ended requests. Like BING_MDI's Analyzer.

**Model:** `gpt-4o`

**When used:** Coordinator routes here when user doesn't provide specific wine preferences.

**Tools available:**
- `wine_db_search(query, filters)` — searches hardcoded inventory
- `web_search(query)` — Tavily search for wine knowledge (stubbed initially with wine_knowledge.py)

**Async architecture (mirroring BING_MDI Analyzer):**
- Runs in background `asyncio.Task`
- Uses `asyncio.Queue` for streaming events to SSE response
- `asyncio.Lock` protects shared state during concurrent tool calls

**Key behaviors:**
- Makes its own decisions: search first? ask user? recommend directly?
- Can call tools multiple times in a single turn
- Tracks tool call count (max 5 per turn to prevent runaway)
- Produces citations using same `[n](#sku)` format

**Example scenarios:**
- "Surprise me" → searches for highest-rated wines → recommends top 3
- "What's the difference between Burgundy and Bordeaux?" → uses wine_knowledge → explains with example wines from inventory
- "Something for tonight, nothing fancy" → infers casual occasion → searches casual + budget-friendly → recommends

---

## Data Layer

### Hardcoded Wine Inventory (`data/wines.py`)

~30-40 wines covering variety across:
- **Types:** Red, White, Sparkling, Rose
- **Regions:** France (Bordeaux, Burgundy, Champagne, Loire, Rhone), Italy (Tuscany, Piedmont, Veneto), Spain (Rioja, Priorat), Australia (Barossa, McLaren Vale), Chile (Maipo), New Zealand (Marlborough), USA (Napa, Sonoma), Argentina (Mendoza), Portugal (Douro)
- **Price range:** HK$80 — HK$2,000
- **Occasions:** casual, business dinner, romantic, celebration, gift, everyday

```python
WINE_INVENTORY = [
    {
        "sku": "FR-BDX-001",
        "name": "Chateau Margaux 2018",
        "type": "red",
        "grape": "Cabernet Sauvignon blend",
        "region": "Bordeaux",
        "country": "France",
        "vintage": 2018,
        "price_hkd": 1800,
        "tasting_notes": "Elegant, dark fruit, silky tannins, long finish",
        "occasions": ["business dinner", "celebration", "gift"],
        "body": "full",
        "sweetness": "dry",
        "food_pairing": ["beef", "lamb", "aged cheese"],
        "rating": 4.8,
        "in_stock": True
    },
    # ... 30+ more wines
]
```

### Hardcoded Wine Knowledge (`data/wine_knowledge.py`)

Pairing rules, region facts, grape descriptions. Used by Explorer Agent and as web_search_tool fallback.

```python
PAIRING_RULES = {
    "steak": {"grapes": ["Cabernet Sauvignon", "Malbec", "Syrah"], "why": "Bold tannins cut through fat"},
    "seafood": {"grapes": ["Sauvignon Blanc", "Chablis", "Albarino"], "why": "Crisp acidity complements delicate flavors"},
    "business_dinner": {"tip": "Choose recognizable labels; Bordeaux and Burgundy signal sophistication"},
    "cheese": {"grapes": ["Port", "Sauternes", "Riesling"], "why": "Sweet wines contrast salty cheese"},
    # ...
}

REGION_FACTS = {
    "Bordeaux": "Known for structured reds. Left bank = Cabernet dominant. Right bank = Merlot dominant.",
    "Burgundy": "Home of Pinot Noir and Chardonnay. Terroir-driven, village-level classifications.",
    "Champagne": "Only sparkling wine from this region can be called Champagne. Methode traditionelle.",
    # ...
}

GRAPE_PROFILES = {
    "Cabernet Sauvignon": {"body": "full", "taste": "blackcurrant, cedar, tobacco", "pairs_with": ["beef", "lamb"]},
    "Pinot Noir": {"body": "light-medium", "taste": "cherry, earth, mushroom", "pairs_with": ["duck", "salmon"]},
    # ...
}
```

---

## wine_db_tool — Search Logic (`tools/wine_db_tool.py`)

Pure Python, no LLM. Mirrors how BING_MDI's RetrievalAgent calls BingMDISearchClient.

```python
def search_wines(
    query: Optional[str] = None,           # Free-text fuzzy match on name/grape/tasting_notes
    type_filter: Optional[str] = None,
    budget_min: Optional[int] = None,
    budget_max: Optional[int] = None,
    country_filter: Optional[str] = None,
    region_filter: Optional[str] = None,
    occasion_tags: list[str] = [],
    grape_filter: Optional[str] = None,
    body_filter: Optional[str] = None,
    sweetness_filter: Optional[str] = None,
    food_pairing_filter: Optional[str] = None,
    exclude_skus: list[str] = [],
    top_k: int = 5
) -> list[dict]:
    """
    Filter + rank wines from WINE_INVENTORY.

    Scoring:
    - Exact type match: +10
    - Price within budget: +8
    - Region/country match: +6
    - Occasion match: +5 per matching tag
    - Grape match: +4
    - Body/sweetness match: +3
    - Food pairing match: +3
    - Free-text fuzzy match: +2 per keyword hit
    - In stock bonus: +1

    Returns top_k wines sorted by score descending.
    """
```

**Relaxation built-in:** If strict filter returns < 3 results, automatically relax in order:
1. Drop region (keep country)
2. Expand budget by ±20%
3. Drop grape/body/sweetness filters
4. Flag `relaxed: True` in results so Generator can mention it

---

## Schemas

### Input (`core/models.py`)

```python
class SommelierInput(BaseModel):
    """Mirrors sensei-server's BingQueryInput pattern."""
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    message_history: list[dict[str, str]]  # [{"role": "user", "content": "..."}]

    @field_validator("message_history")
    def limit_history(cls, v):
        return v[-20:]  # Keep last 20 messages (like BING_MDI's 30)
```

### Citations (`schemas/recommendation.py`)

```python
class WineCitation(BaseModel):
    """Mirrors BING_MDI's Citation structure."""
    id: str             # Wine SKU
    name: str           # Wine name
    type: str           # red/white/etc.
    region: str
    price_hkd: int
    match_reasons: list[str]  # ["Within budget", "French as requested", "Good for business dinners"]

class SommelierMetadata(BaseModel):
    session_id: str
    trace_id: str
    citations: list[WineCitation] = []
    preferences_gathered: Optional[GatheredPreferences] = None
```

---

## SSE Event Flow (`core/streaming.py`)

Identical to sensei-server's event system:

```python
class EventType(str, Enum):
    METADATA = "metadata"            # trace_id, session_id, citations
    AGENT_UPDATED = "agent_updated"  # Which agent is active
    DATA = "data"                    # Streaming answer content
    DONE = "done"                    # Stream complete
    ERROR = "error"                  # Error message

class ContentType(str, Enum):
    THOUGHTS = "thoughts"            # Agent reasoning (debug)
    FINAL_ANSWER = "final_answer"    # User-facing content
```

**Event sequence for a planner flow turn:**
```
event: metadata
data: {"session_id": "abc-123", "trace_id": "xyz-456"}

event: agent_updated
data: {"agent": "coordinator", "content_type": "thoughts"}

event: agent_updated
data: {"agent": "preference_planner", "content_type": "thoughts"}

event: agent_updated
data: {"agent": "generator", "content_type": "final_answer"}

event: data
data: {"content": "Based on your preferences, here are my top picks:\n\n"}

event: data
data: {"content": "**Chateau Leoville-Barton 2019** [1](#FR-BDX-005) — ..."}

event: metadata
data: {"citations": [{"id": "FR-BDX-005", "name": "Chateau Leoville-Barton 2019", ...}]}

event: done
data: {"message": "Stream completed"}
```

---

## Config (`config/sommelier.yaml`)

All agent models are defined here — swap from gpt-4o to gpt-5.1 (or any model) by changing one line per agent. No code changes needed.

```yaml
# Model aliases — change these to swap the entire system to a new model family.
# Agents reference these via YAML anchors so you update in ONE place.
model_defaults:
  heavy: &model_heavy gpt-4o          # For agents needing strong comprehension (swap to gpt-5.1)
  light: &model_light gpt-4o-mini     # For cheap/fast routing tasks (swap to gpt-5.1-mini)

agents:
  coordinator:
    model: *model_light
    temperature: 0.1
    prompt: coordinator

  preference_planner:
    model: *model_heavy
    temperature: 0.1
    prompt: preference_planner

  filter_builder:
    model: *model_light
    temperature: 0.1
    prompt: filter_builder

  generator_with_handoff:
    model: *model_heavy
    temperature: 0.7
    prompt: generator

  generator:
    model: *model_heavy
    temperature: 0.7
    prompt: generator

  query_refinement:
    model: *model_light
    temperature: 0.3
    prompt: query_refinement

  explorer:
    model: *model_heavy
    temperature: 0.7
    prompt: explorer

search:
  top_k: 5
  relaxation_budget_percent: 20
  max_tool_calls_per_turn: 5

conversation:
  max_history: 20
  max_followup_questions: 3
```

**To swap to GPT-5 family:** Change 2 lines:
```yaml
model_defaults:
  heavy: &model_heavy gpt-5.1
  light: &model_light gpt-5.1-mini
```

All agents pick up the new model via YAML anchors. Individual agents can still override if needed (e.g., keep generator on gpt-5.1 while coordinator stays on gpt-4o-mini).

---

## API Design

### `POST /sommelier/chat`

**Request:**
```json
{
  "session_id": "optional-uuid",
  "message_history": [
    {"role": "user", "content": "I need a wine for a business dinner"},
    {"role": "assistant", "content": "Great choice! What's your budget per bottle, and do you have a regional preference?"},
    {"role": "user", "content": "Around HK$500, French if possible"}
  ]
}
```

**Response:** `text/event-stream` (SSE)

### `GET /health`

Returns `{"status": "ok"}`.

---

## Conversation Memory

In-memory dict keyed by `session_id`. LangChain `ConversationBufferWindowMemory` for interface compatibility — swap to Redis/Cosmos later.

```python
from langchain.memory import ConversationBufferWindowMemory

sessions: dict[str, ConversationBufferWindowMemory] = {}

def get_or_create_memory(session_id: str) -> ConversationBufferWindowMemory:
    if session_id not in sessions:
        sessions[session_id] = ConversationBufferWindowMemory(
            k=20, return_messages=True, memory_key="chat_history"
        )
    return sessions[session_id]
```

---

## Key Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.30.0"}
openai-agents = "^0.0.17"          # OpenAI Agents SDK (same as sensei-server)
openai = "^1.50.0"
langchain-core = "^0.3.0"          # Memory + base abstractions
langchain-openai = "^0.3.0"        # OpenAI chat model wrapper
sse-starlette = "^2.0.0"           # SSE responses
pydantic = "^2.8.0"
pydantic-settings = "^2.5.0"
python-dotenv = "^1.0.0"
pyyaml = "^6.0.0"                  # Config loading
tavily-python = "^0.5.0"           # Web search (optional, stubbed initially)

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.24.0"
httpx = "^0.27.0"                  # For TestClient
ruff = "^0.8.0"                    # Linting + formatting
```

---

## Makefile

```makefile
dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/

format:
	ruff format app/ tests/
```

---

## Execution Steps

### Phase 1: Foundation
- [ ] Initialize project (pyproject.toml, directory structure, .env.example)
- [ ] Create `settings.py` with OpenAI API key + YAML config loader
- [ ] Create `config/sommelier.yaml` with model_defaults (YAML anchors for easy model swap) + agent definitions
- [ ] Create `core/agent_config.py` — `AgentConfig` dataclass loaded from YAML, used by all agent factories: `get_agent_config(agent_name) -> AgentConfig(model, temperature, prompt_name)`
- [ ] Create `main.py` with FastAPI app, CORS, health check
- [ ] Create `core/models.py` with SommelierInput + response schemas
- [ ] Create `core/streaming.py` with EventType, EventStreamOutput, ContentType

### Phase 2: Data Layer
- [ ] Create `data/wines.py` with 30-40 hardcoded wines (diverse types, regions, prices)
- [ ] Create `data/wine_knowledge.py` with pairing rules + region facts + grape profiles
- [ ] Create `biz/tools/wine_db_tool.py` with search/filter/scoring/relaxation logic
- [ ] Create `biz/tools/web_search_tool.py` (stubbed with wine_knowledge.py fallback)

### Phase 3: Schemas
- [ ] Create `schemas/preference_plan.py` — PreferencePlan, GatheredPreferences
- [ ] Create `schemas/wine_filter.py` — WineFilter
- [ ] Create `schemas/recommendation.py` — WineCitation, SommelierMetadata

### Phase 4: Prompts
- [ ] Write `prompts/coordinator.md` — routing rules
- [ ] Write `prompts/preference_planner.md` — preference extraction rules
- [ ] Write `prompts/filter_builder.md` — filter construction rules
- [ ] Write `prompts/generator.md` — recommend-vs-ask rules, citation format
- [ ] Write `prompts/query_refinement.md` — relaxation strategy
- [ ] Write `prompts/explorer.md` — autonomous exploration rules

### Phase 5: Agents
- [ ] Create `agents/coordinator.py` — handoff_to_planner / handoff_to_explorer
- [ ] Create `agents/preference_planner.py` — structured output PreferencePlan
- [ ] Create `agents/filter_builder.py` — structured output WineFilter
- [ ] Create `agents/generator.py` — with_handoff and without_handoff variants
- [ ] Create `agents/query_refinement.py` — query transformation + filter relaxation
- [ ] Create `agents/explorer.py` — autonomous agent with tool calls + asyncio.Queue streaming

### Phase 6: Orchestrator + API
- [ ] Create `core/chat_interface.py` — OpenAI Agents SDK streaming wrapper with retry (3 attempts, 1s backoff)
- [ ] Create `biz/agent/sommelier/mode.py` — SommelierMode class with planner_flow() and explorer_flow()
- [ ] Create `biz/agent/sommelier/utils/citation.py` — parse [n](#sku) → WineCitation objects
- [ ] Create `api/routers/sommelier.py` — POST /sommelier/chat → SommelierMode.run() → EventSourceResponse

### Phase 7: Tests
- [ ] Test wine_db_tool: filtering, scoring, relaxation logic
- [ ] Test preference_planner: structured output extraction from various inputs
- [ ] Test generator: recommend vs ask decision boundary
- [ ] Test API endpoint: SSE event format, error handling
- [ ] Test citation parsing: [n](#sku) → WineCitation

### Phase 8: Demo + Docs
- [ ] Run demo scenario 1: Specific user ("Red, French, HK$500, business dinner") → Planner flow → immediate recommendation
- [ ] Run demo scenario 2: Vague user ("Surprise me, something for tonight") → Explorer flow → autonomous recommendation
- [ ] Capture conversation transcripts
- [ ] Create workflow diagram (Mermaid)
- [ ] Write 300-word design rationale
- [ ] Write README with setup + run instructions

---

## Design Rationale (Draft — 300 words)

**Why dual-path multi-agent architecture?**

Wine recommendation has two fundamentally different user modes: users who know what they want ("French red, $500, business dinner") and users who don't ("surprise me"). A single-path system forces compromise — either too many questions for specific users or too few for vague ones. Our dual-path design (Planner Flow vs Explorer Flow) handles both optimally, inspired by production patterns in enterprise document search systems.

**Why a Python orchestrator, not an LLM orchestrator?**

The routing decision (structured vs autonomous) is deterministic enough for a lightweight Coordinator Agent. But the flow execution — parallel agent calls, retry logic, citation building — is pure Python in `SommelierMode.run()`. This keeps latency low (no extra LLM calls for plumbing) and makes the system testable and debuggable.

**Why pre-compute context, then inject?**

Rather than having the Generator Agent call search tools at runtime, we run PreferencePlanner + FilterBuilder → search → inject results into Generator's system prompt. This mirrors production RAG patterns: the Generator sees pre-retrieved context and focuses purely on response quality. It also enables the retry path — if context is insufficient, QueryRefinement transforms queries and re-searches before a second Generator pass.

**Why hardcoded inventory?**

The assignment says "the focus is on workflow design, not real inventory." Our `wine_db_tool` has the same interface whether backed by a Python list or PostgreSQL — the search/filter/score logic is identical. The hardcoded data lets us demo without infrastructure dependencies.

**Trade-offs:**
- 2-3 LLM calls per turn adds ~2-3s latency vs single-call — acceptable for recommendation quality
- Dual-path means more code than single-agent — but each path is independently testable
- In-memory sessions lost on restart — intentional for take-home simplicity, designed for Redis swap
