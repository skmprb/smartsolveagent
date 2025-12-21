from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from token_vault import TokenVault
import uuid
import os
from dotenv import load_dotenv
import uvicorn
import requests
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Allow HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
vault = TokenVault()

# Session storage
user_sessions = {}

REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

def create_flow():
    return google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "client-secret.json",
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email", 
            "openid", 
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/tasks",
            "https://www.googleapis.com/auth/contacts.readonly"
        ],
        redirect_uri=REDIRECT_URI
    )

@app.get('/auth')
def auth():
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline", 
        include_granted_scopes="false",  # Don't include previous scopes
        prompt="consent"  # Force re-consent when scopes change
    )
    return RedirectResponse(url=authorization_url)

@app.get('/health')
def health():
    return {"status": "OK"}

@app.get('/callback')
def callback(request: Request):
    try:
        flow = create_flow()
        # Disable scope validation to handle Google's inconsistent scope returns
        flow._state = None
        flow.fetch_token(authorization_response=str(request.url))
        
        # Get user info to use email as key
        credentials = flow.credentials
        user_info_service = build("oauth2", "v2", credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        user_email = user_info.get('email')
        
        # Store tokens using email as key
        vault.store_token(user_email, flow.credentials)
        
        # Redirect back to frontend with email (updated for dynamic URL)
        return RedirectResponse(url=f"{FRONTEND_URL}?user_email={user_email}")
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.get('/token/{user_email}')
def get_token(user_email: str):
    credentials = vault.get_token(user_email)
    if credentials:
        return {"access_token": credentials.token}
    raise HTTPException(status_code=404, detail="Token not found")

@app.get('/priority_tasks/{user_email}')
def get_priority_tasks(user_email: str):
    try:
        from google.cloud import firestore
        db = firestore.Client(database='smartsolve')
        doc_ref = db.collection('priority_tasks').document(user_email)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            return {"tasks": data.get("tasks", [])}
        else:
            return {"tasks": []}
    except Exception as e:
        return {"error": f"Failed to fetch priority tasks: {str(e)}"}

class CreateSessionRequest(BaseModel):
    user_email: str

class ChatRequest(BaseModel):
    message: str
    user_email: str
    history: List[Dict[str, str]] = []
    session_id: str = None

class OptimizeRequest(BaseModel):
    tasks: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    user_email: str

@app.post('/create_session')
def create_session(request: CreateSessionRequest):
    session_id = str(uuid.uuid4())
    user_sessions[request.user_email] = session_id
    
    # Create session with ADK agent
    agent_url = os.getenv("AGENT_URL", "http://localhost:8080")
    try:
        response = requests.post(
            f"{agent_url}/apps/smartsolve/users/{request.user_email}/sessions/{session_id}",
            json={},
            timeout=10
        )
        if response.status_code == 200:
            return {"session_id": session_id}
        else:
            return {"error": f"Failed to create ADK session: {response.status_code}"}
    except Exception as e:
        return {"error": f"ADK connection error: {str(e)}"}

@app.post('/chat')
def chat(request: ChatRequest):
    try:
        # Get or create session
        session_id = request.session_id or user_sessions.get(request.user_email)
        if not session_id:
            session_id = str(uuid.uuid4())
            user_sessions[request.user_email] = session_id
        
        # Send message to ADK agent using /run endpoint
        agent_url = os.getenv("AGENT_URL", "http://localhost:8080")
        response = requests.post(
            f"{agent_url}/run",
            json={
                "appName": "smartsolve",
                "userId": request.user_email,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": request.message}]
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            events = response.json()
            # Extract text from the last model response
            for event in reversed(events):
                if event.get("content", {}).get("role") == "model":
                    parts = event.get("content", {}).get("parts", [])
                    for part in parts:
                        if "text" in part:
                            return {"content": part["text"]}
            return {"content": "No response from agent"}
        else:
            return {"error": f"ADK request failed: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Chat error: {str(e)}"}

@app.post('/optimize')
def optimize(request: OptimizeRequest):
    try:
        # Get or create session
        session_id = user_sessions.get(request.user_email)
        if not session_id:
            session_id = str(uuid.uuid4())
            user_sessions[request.user_email] = session_id
            
            # Create session with ADK
            agent_url = os.getenv("AGENT_URL", "http://localhost:8080")
            requests.post(
                f"{agent_url}/apps/smartsolve/users/{request.user_email}/sessions/{session_id}",
                json={},
                timeout=10
            )
        
        # Send optimization request to ADK agent
        optimize_message = f"Analyze and optimize this schedule: Tasks: {request.tasks}, Events: {request.events}"
        agent_url = os.getenv("AGENT_URL", "http://localhost:8080")
        response = requests.post(
            f"{agent_url}/run",
            json={
                "appName": "smartsolve",
                "userId": request.user_email,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": optimize_message}]
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            events = response.json()
            # Extract text from the last model response
            for event in reversed(events):
                if event.get("content", {}).get("role") == "model":
                    parts = event.get("content", {}).get("parts", [])
                    for part in parts:
                        if "text" in part:
                            return {
                                "message": part["text"],
                                "type": "Optimization Suggestion"
                            }
            return {
                "message": "No optimization available",
                "type": "Optimization Suggestion"
            }
        else:
            return {"error": f"ADK request failed: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"Optimization error: {str(e)}"}

if __name__ == '__main__':
    uvicorn.run("backend:app", host="0.0.0.0", port=5000, reload=True)