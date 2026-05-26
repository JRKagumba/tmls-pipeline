# Deploy a branch (preview / test) — Cloud Run

Use this when you want to validate a branch on a **dedicated** Cloud Run URL
without overwriting the prod services (`backend`, `frontend`). Each branch gets
its own pair of services suffixed by the branch name.

Production deploys live in [`deploy_prod.md`](./deploy_prod.md).

## What's shared with prod (don't recreate)

Branch deploys **reuse** the existing infrastructure — nothing new to provision:

- Service account `gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com`
- Secret Manager secret `openai-api-key`
- Bucket `gs://tmls-pipeline` (logs are namespaced by branch via `GCS_PREFIX`)
- Project `tmls-agentic-hackathon`, region `northamerica-northeast2`

What changes per branch: only the Cloud Run service names and `GCS_PREFIX`.

## Prerequisites

- **Install gcloud** — https://docs.cloud.google.com/sdk/gcloud
- **Your Google account must be on the project**
  `tmls-agentic-hackathon` — ask Emeric to add you.
- `gcloud` authenticated and pointing at project `tmls-agentic-hackathon`
  (`gcloud config set project tmls-agentic-hackathon`).
- IAM on your user account:
  - `roles/run.developer` on the project (to deploy Cloud Run services).
  - `roles/iam.serviceAccountUser` on
    `gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com` (so the
    `--service-account` flag is allowed). Without this, the deploy fails with
    a confusing IAM error.
- Same APIs enabled as prod (Cloud Run, Cloud Build, Artifact Registry, Secret
  Manager) — already on for this project.

## 1. Compute the branch suffix

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
echo "$BRANCH"
```

> Cloud Run service-name constraints: must start with a letter, can't end with
> `-`, and the **full** name (`backend-test-<branch>`) must fit in 49 chars.
> Typical branch names like `feat-foo` / `fix-bug-42` are fine. If yours
> starts with a digit or is very long, rename the branch or set `BRANCH`
> manually to something shorter.

## 2. Deploy the branch backend

```bash
gcloud run deploy backend-test-$BRANCH \
  --source ./backend \
  --region northamerica-northeast2 \
  --allow-unauthenticated \
  --service-account gcs-pipeline@tmls-agentic-hackathon.iam.gserviceaccount.com \
  --set-env-vars ALLOWED_ORIGINS="*",OPENAI_MODEL=gpt-4o-mini,GCS_BUCKET=tmls-pipeline,GCS_PREFIX=test/$BRANCH/interactions \
  --set-secrets OPENAI_API_KEY=openai-api-key:latest
```

👉 **Note the printed URL**, e.g.
`https://backend-test-feat-foo-689084127939.northamerica-northeast2.run.app` —
you'll paste it into the frontend deploy below.

Why these flags:
- `--allow-unauthenticated` — matches prod so the browser (and the paired
  frontend) can call the API without IAM tokens.
- `--service-account gcs-pipeline@…` — same identity as prod; gives GCS access
  via ADC without shipping a key.
- `--set-secrets OPENAI_API_KEY=openai-api-key:latest` — shared Secret Manager
  secret, no per-branch secret to manage.
- `GCS_PREFIX=test/$BRANCH/interactions` — keeps test logs out of prod's tree
  (`storage.py` reads this env var; default is `interactions`).
- `ALLOWED_ORIGINS="*"` — open CORS for preview convenience.

## 3. Deploy the branch frontend (paired with the branch backend)

```bash
BACKEND_URL=$(gcloud run services describe backend-test-$BRANCH \
  --region northamerica-northeast2 --format='value(status.url)')

gcloud run deploy frontend-test-$BRANCH \
  --source ./frontend \
  --region northamerica-northeast2 \
  --allow-unauthenticated \
  --set-env-vars API_URL="$BACKEND_URL"
```

👉 Open the printed frontend URL in a browser — the "Hello" message and the
chat box should both hit your branch backend.

## 4. Smoke-test

```bash
# Hit the branch backend directly
curl -X POST "$BACKEND_URL/api/chat" \
  -H 'content-type: application/json' \
  -d '{"message":"hello from branch"}'
# Expect: "stored_path":"gs://tmls-pipeline/test/<branch>/interactions/…"

# Confirm logs landed in the branch-scoped prefix
gcloud storage ls "gs://tmls-pipeline/test/$BRANCH/"
```

## 5. Re-deploy after a change

Just re-run the §2 (and §3, if frontend changed) command. Env vars and secrets
already set on the service are preserved when you omit `--set-env-vars` /
`--set-secrets`, but re-listing them is harmless and keeps the command
self-contained.

## 6. Cleanup (do this when the PR merges)

Branch services keep billing until deleted.

```bash
# List all test services across branches
gcloud run services list --region northamerica-northeast2 \
  --filter="metadata.name~-test-"

# Delete the current branch's pair
gcloud run services delete backend-test-$BRANCH  --region northamerica-northeast2 --quiet
gcloud run services delete frontend-test-$BRANCH --region northamerica-northeast2 --quiet

# (Optional) drop the branch's GCS logs
gcloud storage rm -r "gs://tmls-pipeline/test/$BRANCH/"
```

> 🧹 **Delete your branch deploy when the PR merges.** They accumulate
> silently and each one runs cold-start traffic on its own URL.
