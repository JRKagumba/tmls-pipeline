# Local setup — what to install on your machine

This covers the **one-time setup** to run the "hello world" backend + frontend
locally. Deployment to Cloud Run is covered separately in
[`deploy_prod.md`](./deploy_prod.md) (production) and
[`deploy_test.md`](./deploy_test.md) (per-branch preview).

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
is in [`deploy_prod.md`](./deploy_prod.md); per-branch preview deploys are in
[`deploy_test.md`](./deploy_test.md). The two lockfiles created above
(`backend/uv.lock`, `frontend/package-lock.json`) **must be committed** — the
Docker builds depend on them.

---

# Part 2 — OpenAI chat + GCS storage (hello_world-v2)

The chat feature adds two things you must configure: an **OpenAI API key** and a
**GCS bucket** (with a service-account key for local dev). All of it goes into
`backend/.env` — copy the template first:

```bash
cd backend
cp .env.example .env        # .env is gitignored
uv sync                     # installs the new deps (agent-framework-openai, google-cloud-storage)
```

### 6.1 OpenAI — what you need

1. Go to <https://platform.openai.com> → **API keys** → create a key (`sk-…`).
2. Put it in `backend/.env`:
   ```
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini      # optional; this is the default
   ```
That's the only OpenAI requirement. (Make sure the account has billing/credits.)

### 6.2 GCS bucket + service-account key — where to put it

The bucket (`gs://tmls-pipeline`) and service account
(`gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com`) already exist
and are IAM-bound — see `deploy_prod.md` §2bis. You do **not** need to run any
`gcloud storage` / `gcloud iam` commands. For local dev:

1. **Ask Emeric** for the JSON key for the `gcs-pipeline` service account
   (shared via a secure channel — never paste it in chat or commit it).
2. Save it as `backend/secrets/gcs-key.json` (create the folder if missing —
   `backend/secrets/` and `*-key.json` are already gitignored *and*
   `.dockerignore`'d).
3. Add to `backend/.env`:
   ```
   GCS_BUCKET=tmls-pipeline
   GCS_PREFIX=interactions
   GOOGLE_APPLICATION_CREDENTIALS=secrets/gcs-key.json
   ```

> 🔒 **Never commit the key.** If `GCS_BUCKET` is left empty, the chat still
> works — interactions just aren't stored.

### 6.3 Run it

```bash
# Backend (from backend/, with .env filled in)
uv run uvicorn app.main:app --reload --port 8000

# Test the endpoint
curl -X POST http://localhost:8000/api/chat \
  -H 'content-type: application/json' \
  -d '{"message":"hello"}'
# -> {"reply":"…","model":"gpt-4o-mini","usage":{…},"latency_ms":…,"stored_path":"gs://tmls-pipeline/…"}

# See stored interactions
gcloud storage ls gs://tmls-pipeline/interactions/
```

Then the frontend (`npm run dev`) shows an **“Ask the model”** box under the hello
message; type a question and press Enter.

### 6.4 On Cloud Run (no key file)

Don't ship the JSON key to Cloud Run. The deploy uses the runtime service
account (`gcs-pipeline@…`) for GCS auth via ADC, and Secret Manager
(`--set-secrets OPENAI_API_KEY=openai-api-key:latest`) for the OpenAI key —
see [`deploy_prod.md`](./deploy_prod.md) §3a for the exact `gcloud run deploy`
command.
