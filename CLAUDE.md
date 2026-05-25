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
(plumbing for the demo) — see `spec.md` for the full product spec.

**Current state:** a minimal "hello world" two-service app whose only purpose is to
validate the local dev → GCP Cloud Run deployment loop. None of the product
features from `spec.md` are implemented yet. The next steps build on top of this
scaffold.

## Repo layout

```
backend/        FastAPI API (managed with uv)
  app/main.py     /api/hello (returns the hello message) + / (health check)
  pyproject.toml, uv.lock, Dockerfile
frontend/       Next.js App Router (TypeScript, standalone output)
  app/page.tsx       server component: reads API_URL at request time
  app/HelloClient.tsx client component: fetches the backend from the browser
  package.json, package-lock.json, next.config.js, Dockerfile
spec.md         Product specification (target app)
deploy.md       Cloud Run deployment commands (FR)
local_setup.md  One-time machine setup + local run instructions
```

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

## Deployment

Cloud Run via `gcloud run deploy --source .` (build runs in Cloud Build). Full
commands are in `deploy.md`. Defaults: project `tmls-agentic-hackathon`, region
`northamerica-northeast2`. Deploy the **backend first** (to get its URL), then the
frontend with `API_URL` set to that URL.
