# DEPLOY — opérations (à exécuter manuellement)

Toutes les commandes CLI pour : dev local → premier déploiement → mises à jour.
Le code est déjà généré ; ce fichier ne couvre que le **volet opérations**.

> Convention : on suppose la région `europe-west1`. Adapte si besoin.
> Remplace `YOUR_PROJECT_ID` par l'ID de ton projet GCP.

---

## 0. Prérequis (une seule fois sur ta machine)

- **Docker Desktop** installé (utile pour tester les images en local ; pas obligatoire
  pour déployer car le build se fait dans le cloud).
- **gcloud CLI** installé : https://cloud.google.com/sdk/docs/install
- **Node 18+** pour le frontend, **[uv](https://docs.astral.sh/uv/)** (gère Python) pour le backend.

```bash
# Authentification + projet par défaut
gcloud auth login
gcloud config set project tmls-agentic-hackathon
gcloud config set run/region northamerica-northeast2

# Activer les APIs nécessaires (Cloud Run, Cloud Build, Artifact Registry)
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

---

## 1. Dev local (tester la boucle sans Docker)

### Backend (terminal 1) — géré avec `uv`
```bash
cd backend
uv sync                       # crée .venv + génère uv.lock à partir de pyproject.toml
uv run uvicorn app.main:app --reload --port 8000
# -> http://localhost:8000/api/hello
```

> ℹ️ **`uv sync`** aligne `.venv` sur `pyproject.toml`/`uv.lock` : il résout les deps,
> (re)génère `uv.lock` et installe exactement ces versions dans `.venv`. À lancer :
> - **la 1ʳᵉ fois** (crée `.venv` + `uv.lock`, requis par le `uv sync --frozen` du Dockerfile) ;
> - **quand tu modifies une dépendance** (ou après un `git pull` qui change `uv.lock`).
>
> Au quotidien, pas besoin de le relancer : `uv run …` re-synchronise l'environnement
> avant d'exécuter la commande. Le relancer pour rien est inoffensif (quasi-instantané).
> Commit `pyproject.toml` **et** `uv.lock`.

### Frontend (terminal 2)
```bash
cd frontend
npm install              # génère aussi package-lock.json (requis pour le build Docker)
cp .env.local.example .env.local   # API_URL=http://localhost:8000
npm run dev
# -> http://localhost:3000  (doit afficher "Hello from FastAPI 👋")
```

> ⚠️ Lance `npm install` **au moins une fois** : il crée `package-lock.json`,
> indispensable au `npm ci` du Dockerfile. Commit ce fichier.

---

## 2. (Optionnel) Tester les images Docker en local

```bash
# Backend
cd backend
docker build -t backend-local .
docker run --rm -p 8080:8080 backend-local
# -> http://localhost:8080/api/hello

# Frontend (pointant vers le backend local)
cd ../frontend
docker build -t frontend-local .
docker run --rm -p 3000:8080 -e API_URL="http://localhost:8080" frontend-local
# -> http://localhost:3000
```

---

## 3. Premier déploiement sur Cloud Run

`gcloud run deploy --source .` détecte le `Dockerfile` présent, fait le build via
Cloud Build, pousse l'image dans Artifact Registry, puis déploie. (Le dépôt
Artifact Registry `cloud-run-source-deploy` est créé automatiquement à la 1re fois.)

### 3a. Déployer le backend
```bash
cd backend
gcloud run deploy backend \
  --source . \
  --region northamerica-northeast2 \
  --allow-unauthenticated \
  --set-env-vars ALLOWED_ORIGINS="*"
```
👉 **Note l'URL affichée**, ex. `https://backend-689084127939.northamerica-northeast2.run.app`

> `ALLOWED_ORIGINS="*"` ouvre le CORS pour démarrer. On le restreindra à l'étape 4.

### 3b. Déployer le frontend (avec l'URL du backend)
```bash
cd ../frontend
npm install   # si pas déjà fait : garantit package-lock.json
gcloud run deploy frontend \
  --source . \
  --region northamerica-northeast2 \
  --allow-unauthenticated \
  --set-env-vars API_URL="https://backend-689084127939.northamerica-northeast2.run.app"
```
👉 **Note l'URL du frontend**, ex. `https://frontend-689084127939.northamerica-northeast2.run.app`
Ouvre-la dans le navigateur : la page doit afficher la réponse du backend. ✅

---

## 4. (Recommandé) Restreindre le CORS au frontend

Une fois l'URL du frontend connue, remplace le `*` :
```bash
gcloud run services update backend \
  --region northamerica-northeast2 \
  --set-env-vars ALLOWED_ORIGINS="https://frontend-689084127939.northamerica-northeast2.run.app"
```

---

## 5. Mises à jour (redéploiement)

Après chaque modif de code, relance simplement le `deploy` du service concerné :

```bash
# Backend modifié
cd backend && gcloud run deploy backend --source . --region northamerica-northeast2

# Frontend modifié
cd frontend && gcloud run deploy frontend --source . --region northamerica-northeast2
```
Les variables d'env déjà définies sont conservées (pas besoin de re-passer
`--set-env-vars` si elles ne changent pas).

---

## 6. Commandes utiles

```bash
# Lister les services et leurs URLs
gcloud run services list --region northamerica-northeast2

# Voir les logs (live)
gcloud run services logs tail backend  --region northamerica-northeast2
gcloud run services logs tail frontend --region northamerica-northeast2

# Décrire un service (env vars, image, révision active)
gcloud run services describe backend --region northamerica-northeast2

# Supprimer un service
gcloud run services delete backend  --region northamerica-northeast2
gcloud run services delete frontend --region northamerica-northeast2
```

---

## Récap des points Docker / Cloud Run importants

| Sujet | Ce qu'il faut retenir |
|---|---|
| **Port** | Cloud Run injecte `PORT` (8080). Les deux containers écoutent sur `0.0.0.0:8080`. |
| **Backend** | `uvicorn` lancé en forme *shell* pour substituer `${PORT}`. `/` sert de health check. |
| **Deps backend** | Gérées par **uv** : `pyproject.toml` + `uv.lock`. Build image via `uv sync --frozen` (binaire `uv` copié depuis l'image officielle astral). |
| **Frontend** | Build Next.js `output: "standalone"` → image légère lançant `node server.js`. |
| **API_URL** | Variable **runtime** (pas `NEXT_PUBLIC_`), donc modifiable sans rebuild. |
| **CORS** | Géré côté FastAPI via `ALLOWED_ORIGINS`. `*` pour démarrer, puis URL du frontend. |
| **Lockfiles** | Backend : `uv sync` crée `uv.lock` (requis par `uv sync --frozen`). Frontend : `npm install` crée `package-lock.json` (requis par `npm ci`). À committer tous les deux. |
| **Build** | `--source .` ⇒ build dans Cloud Build à partir du `Dockerfile`. Pas de Docker local requis pour déployer. |
| **Ordre** | Déployer le **backend d'abord** (pour avoir son URL), puis le frontend. |
