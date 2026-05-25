# tmls-pipeline

Fullstack "hello world" webapp to validate the dev → deployment loop on **Google Cloud Run**.

* **`backend/`** — **FastAPI** Python API (`/api/hello` endpoint).
* **`frontend/`** — **Next.js / React** (App Router) that calls the backend.

## Architecture

Two independent Cloud Run services:

```
Browser    ──> frontend (Next.js, Cloud Run :8080)
   │              └─ renders page, injects API_URL (runtime)
   └──────────> backend  (FastAPI, Cloud Run :8080)   [direct call + CORS]

```

The backend URL is passed to the frontend via the `API_URL` **runtime** environment variable
(read on the Next server-side then passed to the client component) — no need to rebuild
when the backend URL changes.

## Getting Started

See **[DEPLOY.md](https://www.google.com/search?q=./DEPLOY.md)** for all commands (local dev + Cloud Run deployment).
