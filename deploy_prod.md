# DEPLOY — operations (run manually)

All the CLI commands for: local dev → first deployment → updates.
The code is already generated; this file only covers the **operations side**.

> Convention: region `northamerica-northeast2`, project `tmls-agentic-hackathon`.
> Adapt if needed.

---

## 0. Prerequisites (once per machine)

- **Docker Desktop** installed (handy for testing images locally; not required to
  deploy, since the build runs in the cloud).
- **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
- **Node 18+** for the frontend, **[uv](https://docs.astral.sh/uv/)** (manages Python) for the backend.

```bash
# Authentication + default project
gcloud auth login
gcloud config set project tmls-agentic-hackathon
gcloud config set run/region northamerica-northeast2

# Enable the required APIs (Cloud Run, Cloud Build, Artifact Registry,
# Secret Manager for the OpenAI key)
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

---

## 1. Local dev (test the loop without Docker)

### Backend (terminal 1) — managed with `uv`
```bash
cd backend
uv sync                       # creates .venv + generates uv.lock from pyproject.toml

cp .env.example .env          # then fill in the values (see below)
uv run uvicorn app.main:app --reload --port 8000
# -> http://localhost:8000/api/hello
# -> POST http://localhost:8000/api/chat  {"message":"..."}
```

Fill `backend/.env` with:
```
OPENAI_API_KEY=sk-...                     # your OpenAI key
OPENAI_MODEL=gpt-4o-mini                  # optional (default)
GCS_BUCKET=tmls-pipeline                  # bucket for interaction logs
GCS_PREFIX=interactions
GOOGLE_APPLICATION_CREDENTIALS=secrets/<your-key>.json   # local only
```

> 🔒 `.env` and the service-account JSON key (`backend/secrets/…json`) are
> **local only** and gitignored — never commit them. On Cloud Run we use a
> different mechanism (see §2bis). If `GCS_BUCKET` is empty, chat still works,
> interactions just aren't stored.

> ℹ️ **How `.env` is used (the mechanism):** at startup `app/main.py` calls
> `load_dotenv()`, which reads `backend/.env` into the process environment. The
> code then reads the values with `os.getenv` — `app/agent.py` uses
> `OPENAI_API_KEY` / `OPENAI_MODEL`, and `app/storage.py` uses `GCS_BUCKET` /
> `GCS_PREFIX` / `GOOGLE_APPLICATION_CREDENTIALS`. There is no other config file.
> - `load_dotenv()` looks in the **current directory**, so run uvicorn **from
>   `backend/`**; that also makes the relative `GOOGLE_APPLICATION_CREDENTIALS=secrets/…json`
>   path resolve correctly.
> - **On Cloud Run there is no `.env`** — `load_dotenv()` simply finds nothing, and
>   the values injected via `--set-env-vars` / `--set-secrets` (§3a) are read by the
>   exact same `os.getenv` calls. So local and cloud share one code path; only the
>   source of the variables differs.

> ℹ️ **`uv sync`** aligns `.venv` with `pyproject.toml`/`uv.lock`: it resolves the
> deps, (re)generates `uv.lock`, and installs exactly those versions into `.venv`.
> Run it:
> - **the first time** (creates `.venv` + `uv.lock`, required by the Dockerfile's `uv sync --frozen`);
> - **whenever you change a dependency** (or after a `git pull` that changes `uv.lock`).
>
> Day to day you don't need to rerun it: `uv run …` re-syncs the environment
> before running the command. Running it for nothing is harmless (near-instant).
> Commit `pyproject.toml` **and** `uv.lock`.

### Frontend (terminal 2)
```bash
cd frontend
npm install              # also generates package-lock.json (required for the Docker build)
cp .env.local.example .env.local   # API_URL=http://localhost:8000
npm run dev
# -> http://localhost:3000  (should show "Hello from FastAPI 👋")
```

> ⚠️ Run `npm install` **at least once**: it creates `package-lock.json`,
> required by the Dockerfile's `npm ci`. Commit this file.

---

## 2. (Optional) Test the Docker images locally

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

## 2bis. OpenAI + GCS configuration (one-time)

The backend needs an OpenAI key and write access to the GCS bucket. In the cloud
we **do not** ship the `.env` or the JSON key — the OpenAI key comes from Secret
Manager and GCS auth comes from the Cloud Run **runtime service account**.

We reuse the existing service account
`gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com`.

**1) OpenAI key — create the secret in the GCP Console (manual).**
In the console → **Secret Manager** → *Create secret* named **`openai-api-key`**,
and add your OpenAI key as a **secret version** (manage the value and rotations
there). The deploy references it by name in §3a via `--set-secrets` — no key value
ever lives in the script.

```bash
# 2) Let the runtime service account READ that secret
#    (or grant it on the secret's "Permissions" tab in the console)
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3) Let the runtime service account WRITE objects to the bucket
#    (required for storage to work — locally AND on Cloud Run)
gcloud storage buckets add-iam-policy-binding gs://tmls-pipeline \
  --member="serviceAccount:gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

> 💡 On Cloud Run, **don't** set `GOOGLE_APPLICATION_CREDENTIALS` and don't ship the
> key file. Deploying with `--service-account gcs-pipeline@…` makes the storage
> client authenticate as that account automatically (ADC). The same account is
> used locally (via the JSON key) and in the cloud (via the attached identity).

---

## 3. First deployment to Cloud Run

`gcloud run deploy --source .` detects the `Dockerfile`, builds via Cloud Build,
pushes the image to Artifact Registry, then deploys. (The Artifact Registry repo
`cloud-run-source-deploy` is created automatically the first time.)

### 3a. Deploy the backend
```bash
cd backend
gcloud run deploy backend \
  --source . \
  --region northamerica-northeast2 \
  --allow-unauthenticated \
  --service-account gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com \
  --set-env-vars ALLOWED_ORIGINS="*",OPENAI_MODEL=gpt-4o-mini,GCS_BUCKET=tmls-pipeline,GCS_PREFIX=interactions \
  --set-secrets OPENAI_API_KEY=openai-api-key:latest
```
👉 **Note the printed URL**, e.g. `https://backend-689084127939.northamerica-northeast2.run.app`

> `ALLOWED_ORIGINS="*"` opens CORS to get started; we restrict it in §4.
> No `GOOGLE_APPLICATION_CREDENTIALS` here — GCS auth comes from `--service-account`.

### 3b. Deploy the frontend (with the backend URL)
```bash
cd ../frontend
npm install   # if not already done: guarantees package-lock.json
gcloud run deploy frontend \
  --source . \
  --region northamerica-northeast2 \
  --allow-unauthenticated \
  --set-env-vars API_URL="https://backend-689084127939.northamerica-northeast2.run.app"
```
👉 **Note the frontend URL**, e.g. `https://frontend-689084127939.northamerica-northeast2.run.app`
Open it in the browser: the page should show the backend's response. ✅

---

## 4. (Recommended) Restrict CORS to the frontend

Once the frontend URL is known, replace the `*`:
```bash
gcloud run services update backend \
  --region northamerica-northeast2 \
  --set-env-vars ALLOWED_ORIGINS="https://frontend-689084127939.northamerica-northeast2.run.app"
```

> ⚠️ `--set-env-vars` **replaces** the whole env-var set. Re-list the others
> (`OPENAI_MODEL`, `GCS_BUCKET`, `GCS_PREFIX`) in the same command, or use
> `--update-env-vars ALLOWED_ORIGINS=…` to change just this one. Secrets set with
> `--set-secrets` are preserved.

---

## 5. Updates (redeploy)

After each code change, just rerun the `deploy` for the affected service:

```bash
# Backend changed
cd backend && gcloud run deploy backend --source . --region northamerica-northeast2

# Frontend changed
cd frontend && gcloud run deploy frontend --source . --region northamerica-northeast2
```
Env vars, secrets, and the service account already set are preserved (no need to
re-pass `--set-env-vars` / `--set-secrets` / `--service-account` unless they change).

---

## 6. Useful commands

```bash
# List services and their URLs
gcloud run services list --region northamerica-northeast2

# View logs (live)
gcloud run services logs tail backend  --region northamerica-northeast2
gcloud run services logs tail frontend --region northamerica-northeast2

# Describe a service (env vars, image, active revision)
gcloud run services describe backend --region northamerica-northeast2

# Confirm interactions are being written to the bucket
gcloud storage ls gs://tmls-pipeline/interactions/

# Delete a service
gcloud run services delete backend  --region northamerica-northeast2
gcloud run services delete frontend --region northamerica-northeast2
```

---

## Recap of the important Docker / Cloud Run points

| Topic | What to remember |
|---|---|
| **Port** | Cloud Run injects `PORT` (8080). Both containers listen on `0.0.0.0:8080`. |
| **Backend** | `uvicorn` launched in *shell* form to substitute `${PORT}`. `/` is the health check. |
| **Backend deps** | Managed by **uv**: `pyproject.toml` + `uv.lock`. Image built via `uv sync --frozen` (the `uv` binary is copied from the official Astral image). |
| **Frontend** | Next.js `output: "standalone"` build → lightweight image running `node server.js`. |
| **API_URL** | **Runtime** variable (not `NEXT_PUBLIC_`), so it can change without a rebuild. |
| **CORS** | Handled in FastAPI via `ALLOWED_ORIGINS`. `*` to start, then the frontend URL. |
| **Secrets / env** | Local: `backend/.env` (gitignored). Cloud: `--set-env-vars` for plain values; the OpenAI key lives in a Secret Manager secret (`openai-api-key`) created/managed in the **console**, and the deploy only references it by name via `--set-secrets OPENAI_API_KEY=openai-api-key:latest`. |
| **GCS auth** | Local: JSON key via `GOOGLE_APPLICATION_CREDENTIALS`. Cloud: **no key file** — deploy with `--service-account gcs-pipeline@…`; the client uses ADC. |
| **GCS IAM** | The service account needs `roles/storage.objectAdmin` on `gs://tmls-pipeline` (storage fails with 403 otherwise). |
| **Lockfiles** | Backend: `uv sync` creates `uv.lock` (required by `uv sync --frozen`). Frontend: `npm install` creates `package-lock.json` (required by `npm ci`). Commit both. |
| **Build** | `--source .` ⇒ build in Cloud Build from the `Dockerfile`. No local Docker required to deploy. |
| **Order** | Deploy the **backend first** (to get its URL), then the frontend. |
