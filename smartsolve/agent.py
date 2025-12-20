from google.adk.agents.llm_agent import Agent
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import requests
import json
from datetime import datetime

def get_user_token(user_id: str) -> str:
    """Retrieve user's Google OAuth token from token vault."""
    try:
        response = requests.get(f"http://localhost:5000/token/{user_id}")
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    except:
        return None

def get_gmail_messages(user_id: str, query: str = "", max_results: int = 10) -> dict:
    """Fetch Gmail messages for the user."""
    token = get_user_token(user_id)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('gmail', 'v1', credentials=credentials)
    
    try:
        results = service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()
        messages = results.get('messages', [])
        
        email_list = []
        for msg in messages[:5]:  # Limit to 5 for performance
            message = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            email_list.append({"subject": subject, "from": sender, "id": msg['id']})
        
        return {"emails": email_list, "total": len(messages)}
    except Exception as e:
        return {"error": str(e)}

def get_calendar_events(user_id: str, max_results: int = 10) -> dict:
    """Fetch upcoming calendar events for the user."""
    token = get_user_token(user_id)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('calendar', 'v3', credentials=credentials)
    
    try:
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now, maxResults=max_results,
            singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append({
                "summary": event.get('summary', 'No Title'),
                "start": start,
                "id": event['id']
            })
        
        return {"events": event_list}
    except Exception as e:
        return {"error": str(e)}

def create_calendar_event(user_id: str, title: str, start_time: str, end_time: str, description: str = "") -> dict:
    """Create a new calendar event."""
    token = get_user_token(user_id)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('calendar', 'v3', credentials=credentials)
    
    event = {
        'summary': title,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'UTC'},
        'end': {'dateTime': end_time, 'timeZone': 'UTC'},
    }
    
    try:
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return {"success": True, "event_id": created_event['id'], "link": created_event.get('htmlLink')}
    except Exception as e:
        return {"error": str(e)}

def search_drive_files(user_id: str, query: str, max_results: int = 10) -> dict:
    """Search Google Drive files."""
    token = get_user_token(user_id)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('drive', 'v3', credentials=credentials)
    
    try:
        results = service.files().list(
            q=f"name contains '{query}'",
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        files = results.get('files', [])
        
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

root_agent = Agent(
    model='gemini-2.5-flash',
    name='smartsolve_agent',
    description='AI-powered problem-solving assistant that helps with daily tasks using Google services.',
    instruction="""You are SmartSolve, an intelligent personal assistant that helps users plan, analyze and complete daily tasks efficiently. 
    
    You have access to Google services (Gmail, Calendar, Drive) through OAuth tokens. Always ask for the user's user_id first if not provided.
    
    Key capabilities:
    - Email management and analysis
    - Calendar scheduling and event management  
    - File search and organization
    - Task planning and productivity optimization
    - Research assistance
    
    Be proactive in suggesting workflows and automations to improve productivity.""",
    tools=[get_gmail_messages, get_calendar_events, create_calendar_event, search_drive_files],
)
