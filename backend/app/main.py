import datetime
import logging
import os
import time

from dotenv import load_dotenv

# Load backend/.env for local dev (the Agent Framework does not do this itself).
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import run_agent
from app.storage import store_interaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipeline.api")

app = FastAPI(title="Pipeline API")

# ALLOWED_ORIGINS is a comma-separated list of allowed origins.
# "*" (the default) opens CORS to everyone — fine to get started, tighten later.
_allowed = os.environ.get("ALLOWED_ORIGINS", "*")
_origins = [o.strip() for o in _allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    # Browsers reject "*" together with credentials, so only enable credentials
    # when the origin list is explicit.
    allow_credentials="*" not in _origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    """Health check — Cloud Run pings this to confirm the container is up."""
    return {"status": "ok"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI 👋"}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class Usage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ChatResponse(BaseModel):
    reply: str
    model: str
    usage: Usage
    latency_ms: float
    stored_path: str | None = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the model, persist the interaction, return the reply."""
    t0 = time.perf_counter()
    try:
        result = await run_agent(req.message)
    except Exception as exc:
        logger.exception("Agent call failed")
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input": req.message,
        "output": result["text"],
        "model": result["model"],
        "usage": {
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "total_tokens": result["total_tokens"],
        },
        "latency_ms": latency_ms,
    }
    # Best-effort persistence — never let a storage failure break the reply.
    stored_path = store_interaction(record)
    logger.info(
        "chat model=%s tokens=%s latency_ms=%s stored=%s",
        record["model"],
        record["usage"]["total_tokens"],
        latency_ms,
        stored_path,
    )

    return ChatResponse(
        reply=result["text"],
        model=result["model"],
        usage=Usage(
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            total_tokens=result["total_tokens"],
        ),
        latency_ms=latency_ms,
        stored_path=stored_path,
    )
