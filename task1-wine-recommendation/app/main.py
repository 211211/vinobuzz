from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncAzureOpenAI
from agents import set_default_openai_client, set_tracing_disabled

from app.api.routers.sommelier import router as sommelier_router
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Azure OpenAI client as the default for all agents
    client = AsyncAzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )
    set_default_openai_client(client)
    # Disable OpenAI tracing — it tries to send traces to api.openai.com
    # using the Azure key, which causes 401 errors (non-fatal but noisy).
    set_tracing_disabled(True)
    yield


app = FastAPI(
    title="VinoBuzz AI Sommelier",
    description="Multi-agent conversational wine recommendation system",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sommelier_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
