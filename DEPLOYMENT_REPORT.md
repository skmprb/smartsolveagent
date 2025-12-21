# Deployment Report: SmartSolve on GCP

This document summarizes the steps, commands, and troubleshooting history for deploying the SmartSolve application to Google Cloud Platform.

## 1. Deployment Commands (Step-by-Step)

### Phase 1: Environment Setup
1.  **Authentication**:
    ```bash
    gcloud auth login
    gcloud config set project [PROJECT_ID]
    ```
2.  **Enable APIs**:
    ```bash
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com firestore.googleapis.com
    ```

### Phase 2: Deployment via Cloud Build
I used `cloudbuild.yaml` to orchestrate building Docker images and deploying them to Cloud Run in one go.

**Command used**:
```powershell
gcloud builds submit --config cloudbuild.yaml . --project "gen-lang-client-0005433326"
```

### Phase 3: IAM Access (Initial Fix for 403s)
Initially, I manually granted public access to the services:
```bash
gcloud run services add-iam-policy-binding smartsolve-frontend --member="allUsers" --role="roles/run.invoker" --region=us-central1
```
*(Note: Later deployments included the `--allow-unauthenticated` flag in `cloudbuild.yaml` to handle this automatically.)*

---

## 2. Blockers, Errors, and Solutions

| Error / Blocker | Context | Solution |
| :--- | :--- | :--- |
| **ModuleNotFoundError: No module named 'google.adk'** | Agent service failed to start. | Added `google-adk` to `requirements.txt`. |
| **Docker CMD failure** | `python -m google.adk.agents.server` failed. | Updated `Dockerfile.agent` to copy `main.py` and use `python main.py` as the entrypoint. |
| **npm install exit 127** | Frontend build failed in Docker. | Removed `--only=production` from `npm ci`. Vite/Tailwind dev dependencies are required for the `npm run build` step. |
| **403 Forbidden** | Frontend was inaccessible after deployment. | Added `run.invoker` IAM policy for `allUsers` to all services. |
| **Nginx Proxy Failure** | `proxy_pass http://backend-service:8080` failed. | Commented out the `/api` block in `nginx.conf` and moved API routing to environmental variables. |
| **redirect_uri_mismatch** | Google Login failed with 400 error. | 1. Updated `client-secret.json`. 2. Refactored `backend.py` to use dynamic `REDIRECT_URI` env var. 3. Updated Cloud Console logic. |
| **Refusal to connect (Localhost Fetch)** | Frontend tried calling `localhost:5000`. | Refactored JS to use `import.meta.env.VITE_API_URL`. |
| **ReferenceError: API_URL is not defined** | App crashed on "Solve" tab. | Fixed JS scoping: Moved the `API_URL` constant from local function scopes to component-level scope. |

---

## 3. Key Files Modified

| File | Purpose |
| :--- | :--- |
| `cloudbuild.yaml` | Orchestrates build/deploy, injects production URLs. |
| `backend.py` | Updated for dynamic URLs and Agent communication. |
| `Dockerfile.agent` | Fixed entrypoint and file copying. |
| `requirements.txt` | Added `google-adk`. |
| `nginx.conf` | Cleaned up invalid proxy directives. |
| `frontend/src/...` | Refactored components for dynamic API URLs. |
| `frontend/.env.production` | Stores the live Backend link for the Vite build. |

---

## 4. Final Environment Variables
Injected via `cloudbuild.yaml` to **SmartSolve Backend**:
- `AGENT_URL`: `https://smartsolve-agent-j4czxf7gdq-uc.a.run.app`
- `REDIRECT_URI`: `https://smartsolve-backend-j4czxf7gdq-uc.a.run.app/callback`
- `FRONTEND_URL`: `https://smartsolve-frontend-j4czxf7gdq-uc.a.run.app`
