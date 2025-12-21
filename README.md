# SmartSolve AI Dashboard

SmartSolve is an AI-powered productivity dashboard that integrates with Google Workspace (Gmail, Calendar, Tasks) to analyze your schedule, optimize your task list, and provide research-backed insights using Google's Generative AI Agent Kit.

---

## 🚀 Features
- **AI Agent Chat**: Interactive research and planning agent specialized in Google Workspace data.
- **Smart Insights**: Automated analysis of your upcoming events and tasks to suggest optimizations.
- **Priority Intelligence**: Automatic categorization of tasks into high, medium, and low priority.
- **Seamless Sync**: Direct integration with Google Tasks and Calendar APIs.
- **Modern UI**: Dark-mode optimized dashboard built with React and Tailwind CSS.

---

## 🛠️ Technology Stack
- **Frontend**: React, Vite, Tailwind CSS, Material Symbols.
- **Backend**: Python, FastAPI, Uvicorn.
- **AI Engine**: Google ADK (GenAI Agent Kit), Gemini LLM.
- **Database**: Google Firestore.
- **Infrastructure**: Google Cloud Platform (Cloud Run, Cloud Build).

---

## 🔑 Prerequisites & Configuration

### 1. Enable Google Cloud APIs
You must enable the following APIs in your [GCP Console](https://console.cloud.google.com/):
- `run.googleapis.com` (Cloud Run)
- `cloudbuild.googleapis.com` (Cloud Build)
- `firestore.googleapis.com` (Cloud Firestore)
- `gmail.googleapis.com` (Gmail API)
- `calendar-json.googleapis.com` (Calendar API)
- `tasks.googleapis.com` (Google Tasks API)
- `generativelanguage.googleapis.com` (Gemini API)

### 2. Required JSON Files
Place both files in the root directory:
- `client-secret.json`: OAuth 2.0 Desktop/Web client credentials.
- `firestore-key.json`: Service Account key for Firestore access.

---

## 💻 Local Setup

### Step 1: Clone the Repo
```bash
git clone <your-repo-url>
cd smartsolveagent
```

### Step 2: Set up Backend & Agent
```bash
# Install dependencies
pip install -r requirements.txt

# Start Agent Service (Port 8080)
python main.py

# Start Backend API (Port 5000)
python backend.py
```

### Step 3: Set up Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## ☁️ Google Cloud Deployment (Cloud Run)

The project is pre-configured with `cloudbuild.yaml` for a one-command deployment.

### Step 1: Deploy
Run from the root directory:
```powershell
gcloud builds submit --config cloudbuild.yaml . --project "YOUR_PROJECT_ID"
```

### Step 2: Finalize OAuth
After deployment finishes:
1.  Go to **Google Cloud Console > API & Services > Credentials**.
2.  Edit your OAuth 2.0 Client ID.
3.  Add the live Backend URL plus `/callback` to **Authorized redirect URIs**:
    `https://smartsolve-backend-xxxx-uc.a.run.app/callback`
4.  Save changes.

---

## 🐞 Troubleshooting
- **ReferenceError: API_URL is not defined**: This often happens if the frontend environment variables are not bundled correctly. Ensure `VITE_API_URL` is set in `.env.production` before building.
- **redirect_uri_mismatch**: Verify that the URL in your Google Console matches exactly what the Backend is sending (Check the Deployment Report for details).
- **ModuleNotFoundError: google.adk**: Ensure `google-adk` is installed in your python environment.

---

## 📝 Project History
For a detailed log of every error we faced and how we solved it (including CI/CD fixes), refer to [DEPLOYMENT_REPORT.md](./DEPLOYMENT_REPORT.md).