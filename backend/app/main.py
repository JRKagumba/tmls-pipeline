import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
