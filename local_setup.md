# Local setup — what to install on your machine

This covers the **one-time setup** to run the "hello world" backend + frontend
locally. Deployment to Cloud Run is covered separately in [`deploy.md`](./deploy.md).

> ✅ When this repo was generated, all the tools below were already detected on
> this machine, and both services were smoke-tested successfully. This file is
> the reference for a fresh machine (or a teammate).

---

## 1. Tools to install (once)

| Tool | Why | Install |
|---|---|---|
| **uv** | Python dependency/venv manager for the backend | `brew install uv` — or https://docs.astral.sh/uv/ |
| **Node 18+** & **npm** | Runs/builds the Next.js frontend | `brew install node` — or https://nodejs.org |
| **gcloud CLI** | Deploy to Cloud Run (only needed when you deploy) | https://cloud.google.com/sdk/docs/install |
| **Docker Desktop** | *Optional* — test the container images locally | https://www.docker.com/products/docker-desktop |

Check everything is available:

```bash
uv --version
node --version    # must be >= 18
npm --version
gcloud --version
```

---

## 2. Backend — FastAPI (terminal 1)

```bash
cd backend
uv sync                       # creates .venv + uv.lock from pyproject.toml
uv run uvicorn app.main:app --reload --port 8000
```

Verify:

- http://localhost:8000/api/hello → `{"message":"Hello from FastAPI 👋"}`
- http://localhost:8000/ → `{"status":"ok"}` (health check)

> `uv.lock` is committed and is **required** by the Docker build (`uv sync --frozen`).
> Re-run `uv sync` only when dependencies change.

---

## 3. Frontend — Next.js (terminal 2)

```bash
cd frontend
npm install                       # installs deps + creates package-lock.json
cp .env.local.example .env.local  # sets API_URL=http://localhost:8000
npm run dev
```

Open **http://localhost:3000** — the page should display **“Hello from FastAPI 👋”**
fetched live from the backend.

> `package-lock.json` is committed and is **required** by the Docker build (`npm ci`).
> Run `npm install` again only when dependencies change.

---

## 4. How the two talk to each other

```
Browser ──> frontend (Next.js, :3000 local / :8080 on Cloud Run)
   │           └─ reads API_URL at runtime, hands it to the page
   └────────> backend  (FastAPI, :8000 local / :8080 on Cloud Run)   [direct fetch + CORS]
```

- **`API_URL`** (frontend) — where the browser sends its API calls. Locally it's
  `http://localhost:8000` via `.env.local`. It's a **runtime** variable, so the
  deployed backend URL is set at deploy time without rebuilding.
- **`ALLOWED_ORIGINS`** (backend) — comma-separated CORS allow-list. Defaults to
  `*` (open) so local dev just works; lock it to the frontend URL in production.

---

## 5. (Optional) Test the Docker images locally

Only needed if you want to reproduce the Cloud Run containers on your machine
(requires Docker Desktop running). Both images listen on port **8080**.

```bash
# Backend
cd backend
docker build -t backend-local .
docker run --rm -p 8080:8080 backend-local
# -> http://localhost:8080/api/hello

# Frontend (pointing at the local backend)
cd ../frontend
docker build -t frontend-local .
docker run --rm -p 3000:8080 -e API_URL="http://localhost:8080" frontend-local
# -> http://localhost:3000
```

---

## 6. Next step → deployment

Everything for the Cloud Run deployment (auth, enabling APIs, `gcloud run deploy`)
is in [`deploy.md`](./deploy.md). The two lockfiles created above
(`backend/uv.lock`, `frontend/package-lock.json`) **must be committed** — the
Docker builds depend on them.
