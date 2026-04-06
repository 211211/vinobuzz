VinoBuzz — AI Engineer Take Home Assignment
VinoBuzz — AI Engineer Take Home Assignment
Position: AI Engineer + Full Stack Developer
Submission: Share your work via a GitHub repo or Google Drive link, plus any live demos if applicable.

About VinoBuzz
VinoBuzz is a Hong Kong-based wine AI platform. Our flagship product, VinoBuzz, is an AI-powered wine recommendation engine serving retailers and consumers. Key facts about our stack:
•	AI Layer: FastGPT for conversational AI workflows
•	Backend: Python (FastAPI), PostgreSQL
•	Frontend: React Native
•	Team: ~5 people, engineering-driven
•	Core challenge: Helping users find the right wine through natural language — balancing budget, occasion, taste preference, and inventory

Task 1 — Conversational Wine Recommendation Workflow
Background
VinoBuzz's AI sommelier helps users find wines through a multi-turn conversation. A typical session might look like:
User: "I'm looking for a red wine for a business dinner."
AI: "What's your budget per bottle, and do you have any regional preferences?"
User: "Around HK$500, preferably French." >
Your Task
Design and build a conversational AI workflow (using any platform of your choice — FastGPT, Dify, LangChain, custom code, or anything else) that:
1.	Engages the user in a short conversation to understand their needs (budget, occasion, wine type, regional preference)
2.	Makes a judgment call — when does it have enough info to recommend vs. when should it ask a follow-up?
3.	Returns 1–3 wine recommendations with a brief explanation for each
You can use any wine data you like (invent it, use a public dataset, or hardcode a small inventory). The focus is on workflow design, not real inventory.
Deliverables
•	Screenshot(s) or diagram of your workflow
•	A short conversation demo (screenshots or exported transcript) showing at least 2 different user scenarios
•	A brief written explanation (max 300 words): Why did you design it this way? What trade-offs did you make?

Task 2 — OpenClaw Research Essay
Background
OpenClaw is an AI agent platform that connects large language models to tools, data sources, and communication channels. It can be used to build personal AI assistants, internal operations tools, or customer-facing automations.
Your task is to evaluate its potential relevance to a company like VinoBuzz.
Your Task
Write an evaluation report covering three sections:
Section A — What is OpenClaw?
In your own words, describe what OpenClaw is, what it can do, and how it works architecturally. Do not copy from documentation — we want to understand how you internalize and explain a new tool.
Section B — Potential Applications for VinoBuzz
Identify at least **3 concrete use cases** where OpenClaw could create value for a company like VinoBuzz. Be specific — "automate workflows" is not a use case. "An AI assistant that monitors Jira tickets, sends daily PM reports to Lark, and flags blocked issues" is.
Section C — Risks and Limitations
What are the real risks of adopting OpenClaw in a production / internal operations context? Consider: data security, vendor dependency, cost at scale, reliability, and team adoption. Be honest — if you think the risks outweigh the benefits, say so and explain why.
Deliverables
•	A written report in English
•	Quality over quantity

Task 3 — AI-Assisted Engineering
Background
As an AI Engineer, you'll be expected to use AI tools as part of your daily engineering workflow — not just build AI features, but use AI to build faster and better.
Your Task
Below is a simplified version of a Python FastAPI endpoint from our codebase. It has at least 2 bugs and is missing one feature.
Python
from fastapi import APIRouter, HTTPException
from typing import Optional
import psycopg2

router = APIRouter()

DB_CONFIG = {
    "host": "localhost",
    "database": "vinoseek",
    "user": "admin",
    "password": "password"
}

@router.get("/wines/search")
def search_wines(
    query: str,
    budget_max: Optional[int] = None,
    region: Optional[str] = None,
    limit: int = 10
):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    sql = f"SELECT sku, name, price, region FROM wines WHERE name LIKE '%{query}%'"
    
    if budget_max:
        sql += f" AND price <= {budget_max}"
    
    if region:
        sql += f" AND region = '{region}'"
    
    sql += f" LIMIT {limit}"
    
    cursor.execute(sql)
    results = cursor.fetchall()
    
    return {"wines": results}


@router.post("/wines/recommend")
def recommend_wine(user_id: int, wine_sku: str):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO recommendations (user_id, wine_sku, created_at) VALUES (%s, %s, NOW())",
        (user_id, wine_sku)
    )
    
    return {"status": "saved"}
Part A — Fix the bugs
Find and fix all bugs. Add comments explaining what was wrong and why it matters.
Part B — Add a missing feature
The recommend_wine endpoint saves a recommendation but never checks if the wine SKU actually exists in the database. Add that validation — if the SKU doesn't exist, return an appropriate error.
Part C — Write a test
Write at least one unit or integration test for the search_wines endpoint. Use any testing framework you prefer (pytest, unittest, etc.).
Part D — Reflection (required)
In 100–200 words: Which AI tools did you use for this task? How did you use them? Was there anything the AI got wrong or couldn't handle well?

Evaluation Criteria (Overall)
Area	Weight
Task 1: Workflow design quality and reasoning	35%
Task 2: Research depth and business thinking	35%
Task 3: Engineering correctness + AI tool usage	20%
Communication clarity (written explanations)	10%
We're not looking for perfection. We're looking for clear thinking, good judgment, and the ability to learn and adapt quickly.

Questions?
If anything is unclear, email us at it@vino-intel.com. We'd rather you ask than guess.
Good luck.
