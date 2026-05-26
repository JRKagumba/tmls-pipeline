# CLAUDE.md

Guidance for Claude Code (and contributors) working in this repo.

## Working agreements (always apply)

- **Write everything in English.** All documentation, code comments, commit
  messages, and files must be in English — no exceptions.
- **Respond to the user in English.** Even when the user writes in French, reply
  in English.

---

## Project overview

**Pipeline** is an AI-first intake assistant for skilled-trades small businesses
(plumbing for the demo) — see `specifications/spec.md` for the full product spec
and `specifications/PROJECT_PLAN.md` for the epic-level build plan.

**Current state:** a minimal "hello world" two-service app whose only purpose is to
validate the local dev → GCP Cloud Run deployment loop, plus a thin chat slice
(`POST /api/chat` → OpenAI → GCS log). None of the product features from
`specifications/spec.md` (triage, scheduling, quoting, dashboard, etc.) are
implemented yet. The next steps build on top of this scaffold.

## Repo layout

```
backend/        FastAPI API (managed with uv)
  app/main.py     / (health) + /api/hello + POST /api/chat
  app/agent.py    OpenAI call via Microsoft Agent Framework (run_agent)
  app/storage.py  best-effort GCS writer for interaction logs (store_interaction)
  pyproject.toml, uv.lock, Dockerfile, .env.example
frontend/       Next.js App Router (TypeScript, standalone output)
  app/page.tsx       server component: reads API_URL at request time
  app/HelloClient.tsx client component: GET /api/hello
  app/ChatBox.tsx     client component: POST /api/chat (message box)
  package.json, package-lock.json, next.config.js, Dockerfile
specifications/  Product + design artifacts (no code)
  spec.md                       Product specification (target app)
  PROJECT_PLAN.md               Epic-level breakdown, owners, dependencies
  openapi.yaml                  Target REST API contract
  agent_design.mermaid          Agent orchestration diagram
  data_model.mermaid            Domain entities + relationships
  PIPELINE_flowchart_mermaid.md End-to-end flow diagram
hello_world-v2.md Spec for the current chat→OpenAI→GCS slice
deploy_prod.md    Production Cloud Run deployment (local dev → deploy → updates, incl. OpenAI/GCS)
deploy_test.md    Per-branch preview Cloud Run deployment (shared SA/secret/bucket, branch-suffixed service names)
local_setup.md    One-time machine setup + local run instructions
README.md         Short repo intro
```

Note: `specifications/` describes the *target* product. The code under
`backend/` and `frontend/` currently implements only the hello-world + chat
slice, so contracts (e.g. `openapi.yaml`) are aspirational until each endpoint
ships.

## Local development

Backend (terminal 1):
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
# http://localhost:8000/api/hello  ->  {"message":"Hello from FastAPI 👋"}
```

Frontend (terminal 2):
```bash
cd frontend
npm install
cp .env.local.example .env.local   # API_URL=http://localhost:8000
npm run dev
# http://localhost:3000  -> shows the message fetched from the backend
```

## Key conventions (preserve these)

- **Port 8080:** both Docker images listen on `0.0.0.0:8080`; Cloud Run injects
  `PORT`. Don't hardcode another port in the containers.
- **`API_URL` is a frontend *runtime* env var.** `app/page.tsx` sets
  `export const dynamic = "force-dynamic"` so the value is read per request — the
  deployed backend URL can change without rebuilding the frontend image.
- **Backend CORS** is driven by `ALLOWED_ORIGINS` (comma-separated list; default
  `*`). Tighten it to the frontend URL in production.
- **Lockfiles must stay committed:** `backend/uv.lock` and
  `frontend/package-lock.json`. Docker builds rely on `uv sync --frozen` and
  `npm ci`, which require them.
- **Next.js is pinned to `14.2.x`** (App Router, standalone). Don't bump to a
  major version without intent.
- **Never commit secrets.** `backend/.env`, `backend/secrets/`, and `*-key.json`
  are gitignored *and* `.dockerignore`'d. They hold the OpenAI key and the GCS
  service-account JSON key for **local dev only** — the cloud uses Secret Manager
  and the runtime service account instead.

## Chat feature env vars (`/api/chat`)

Set in `backend/.env` locally (gitignored; see `backend/.env.example`), or via
`--set-env-vars` / `--set-secrets` on Cloud Run. Locally the backend loads
`backend/.env` at startup via `load_dotenv()` in `app/main.py`; in the cloud the
same variables are injected and read by the same `os.getenv` calls (run uvicorn
from `backend/` so the file and relative key path resolve). The chat path:
`ChatBox` → `POST /api/chat` → `app.agent.run_agent` (OpenAI via Agent Framework) →
`app.storage.store_interaction` (GCS, best-effort) → reply + usage + latency.

- `OPENAI_API_KEY` (required), `OPENAI_MODEL` (default `gpt-4o-mini`).
- `GCS_BUCKET` (if unset, storage is skipped and chat still works), `GCS_PREFIX`
  (default `interactions`).
- `GOOGLE_APPLICATION_CREDENTIALS` — service-account key path, **local dev only**.
  On Cloud Run, grant the runtime service account `roles/storage.objectAdmin` on
  the bucket instead of shipping a key.
- Storage is non-fatal by design: a GCS failure must never break the reply.
  Full setup steps are in `local_setup.md` Part 2.

## Deployment

Cloud Run via `gcloud run deploy --source .` (build runs in Cloud Build). Full
commands for prod are in `deploy_prod.md`; per-branch preview deploys (own URL,
shared SA/secret/bucket, branch-suffixed service name and `GCS_PREFIX`) are in
`deploy_test.md`. Defaults: project `tmls-agentic-hackathon`, region
`northamerica-northeast2`. Deploy the **backend first** (to get its URL), then the
frontend with `API_URL` set to that URL.

Backend deploy specifics (see `deploy_prod.md` §2bis/§3a):
- `--service-account gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com` —
  GCS auth uses this identity via ADC; **no key file in the cloud** (don't set
  `GOOGLE_APPLICATION_CREDENTIALS`).
- `--set-secrets OPENAI_API_KEY=openai-api-key:latest` (Secret Manager) plus
  `--set-env-vars` for `OPENAI_MODEL` / `GCS_BUCKET` / `GCS_PREFIX`.
- That service account needs `roles/storage.objectAdmin` on `gs://tmls-pipeline`,
  or storage writes 403 (chat still works; interactions just aren't stored).
