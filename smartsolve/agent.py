from google.adk.agents.llm_agent import Agent
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.cloud import firestore
from google.auth.transport.requests import Request
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_user_token(user_email: str) -> str:
    """Retrieve user's Google OAuth token directly from Firestore."""
    print(f"DEBUG: Getting token from Firestore for: {user_email}")
    try:
        db = firestore.Client(database='smartsolve')
        doc_ref = db.collection('user_tokens').document(user_email)
        doc = doc_ref.get()
        
        if not doc.exists:
            print("DEBUG: No token found in Firestore")
            return None
        
        token_data = doc.to_dict()
        print("DEBUG: Token retrieved from Firestore")
        
        # Create credentials and refresh if needed
        with open("client-secret.json", 'r') as f:
            client_id = json.load(f)["web"]["client_id"]
        
        credentials = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id
        )
        
        # Refresh if expired
        if credentials.expired:
            print("DEBUG: Token expired, refreshing...")
            credentials.refresh(Request())
            # Update Firestore with new token
            doc_ref.set({
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
        
        return credentials.token
    except Exception as e:
        print(f"DEBUG: Firestore error: {str(e)}")
        return None

def get_gmail_messages(user_email: str, query: str = "", max_results: int = 10) -> dict:
    """Fetch Gmail messages for the user."""
    print(f"DEBUG: get_gmail_messages called with user_email: {user_email}")
    
    print("DEBUG: Getting token...")
    token = get_user_token(user_email)
    if not token:
        print("DEBUG: No token found")
        return {"error": "User not authenticated"}
    
    print(f"DEBUG: Token retrieved: {token[:20]}...")
    
    print("DEBUG: Building Gmail service...")
    credentials = Credentials(token=token)
    service = build('gmail', 'v1', credentials=credentials)
    
    print("DEBUG: Making Gmail API call...")
    try:
        results = service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()
        print("DEBUG: Gmail API call successful")
        
        messages = results.get('messages', [])
        print(f"DEBUG: Found {len(messages)} messages")
        
        email_list = []
        for msg in messages[:5]:  # Limit to 5 for performance
            message = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            email_list.append({"subject": subject, "from": sender, "id": msg['id']})
        
        print(f"DEBUG: Returning {len(email_list)} emails")
        return {"emails": email_list, "total": len(messages)}
    except Exception as e:
        print(f"DEBUG: Gmail error: {str(e)}")
        return {"error": str(e)}

def get_calendar_events(user_email: str, max_results: int = 10) -> dict:
    """Fetch upcoming calendar events for the user."""
    token = get_user_token(user_email)
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

def create_calendar_event(user_email: str, title: str, start_time: str, end_time: str, description: str = "") -> dict:
    """Create a new calendar event."""
    token = get_user_token(user_email)
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

def search_drive_files(user_email: str, query: str, max_results: int = 10) -> dict:
    """Search Google Drive files."""
    token = get_user_token(user_email)
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

def create_task(user_email: str, title: str, notes: str = "", due_date: str = "") -> dict:
    """Create a new task in Google Tasks."""
    token = get_user_token(user_email)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('tasks', 'v1', credentials=credentials)
    
    task = {
        'title': title,
        'notes': notes
    }
    if due_date:
        task['due'] = due_date
    
    try:
        created_task = service.tasks().insert(tasklist='@default', body=task).execute()
        return {"success": True, "task_id": created_task['id'], "title": created_task['title']}
    except Exception as e:
        return {"error": str(e)}

def get_tasks(user_email: str, max_results: int = 20) -> dict:
    """Get user's tasks from Google Tasks."""
    token = get_user_token(user_email)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('tasks', 'v1', credentials=credentials)
    
    try:
        results = service.tasks().list(tasklist='@default', maxResults=max_results).execute()
        tasks = results.get('items', [])
        
        task_list = []
        for task in tasks:
            task_list.append({
                "title": task.get('title', 'No Title'),
                "notes": task.get('notes', ''),
                "due": task.get('due', ''),
                "status": task.get('status', ''),
                "id": task['id']
            })
        
        return {"tasks": task_list}
    except Exception as e:
        return {"error": str(e)}

def get_contacts(user_email: str, max_results: int = 50) -> dict:
    """Get user's contacts to identify important people."""
    token = get_user_token(user_email)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('people', 'v1', credentials=credentials)
    
    try:
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=max_results,
            personFields='names,emailAddresses,phoneNumbers'
        ).execute()
        connections = results.get('connections', [])
        
        contact_list = []
        for person in connections:
            names = person.get('names', [])
            emails = person.get('emailAddresses', [])
            
            if names and emails:
                contact_list.append({
                    "name": names[0].get('displayName', ''),
                    "email": emails[0].get('value', ''),
                    "id": person.get('resourceName', '')
                })
        
        return {"contacts": contact_list}
    except Exception as e:
        return {"error": str(e)}

def store_priority_tasks(user_email: str, tasks: list) -> dict:
    """Store user's top 5 priority tasks in Firestore."""
    try:
        db = firestore.Client(database='smartsolve')
        doc_ref = db.collection('priority_tasks').document(user_email)
        
        doc_ref.set({
            "tasks": tasks[:5],  # Limit to top 5
            "updated_at": firestore.SERVER_TIMESTAMP,
            "user_email": user_email
        })
        
        return {"success": True, "message": f"Stored {len(tasks[:5])} priority tasks"}
    except Exception as e:
        return {"error": str(e)}

def get_priority_tasks(user_email: str) -> dict:
    """Get user's stored priority tasks from Firestore."""
    try:
        db = firestore.Client(database='smartsolve')
        doc_ref = db.collection('priority_tasks').document(user_email)
        doc = doc_ref.get()
        
        if not doc.exists:
            return {"tasks": [], "message": "No priority tasks found"}
        
        data = doc.to_dict()
        return {
            "tasks": data.get("tasks", []),
            "updated_at": data.get("updated_at"),
            "total": len(data.get("tasks", []))
        }
    except Exception as e:
        return {"error": str(e)}

def update_priority_task(user_email: str, task_index: int, updated_task: dict) -> dict:
    """Update a specific priority task."""
    try:
        db = firestore.Client(database='smartsolve')
        doc_ref = db.collection('priority_tasks').document(user_email)
        doc = doc_ref.get()
        
        if not doc.exists:
            return {"error": "No priority tasks found to update"}
        
        data = doc.to_dict()
        tasks = data.get("tasks", [])
        
        if 0 <= task_index < len(tasks):
            tasks[task_index] = updated_task
            doc_ref.update({
                "tasks": tasks,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            return {"success": True, "message": f"Updated task {task_index + 1}"}
        else:
            return {"error": "Invalid task index"}
    except Exception as e:
        return {"error": str(e)}

def delete_priority_task(user_email: str, task_index: int) -> dict:
    """Delete a specific priority task."""
    try:
        db = firestore.Client(database='smartsolve')
        doc_ref = db.collection('priority_tasks').document(user_email)
        doc = doc_ref.get()
        
        if not doc.exists:
            return {"error": "No priority tasks found to delete"}
        
        data = doc.to_dict()
        tasks = data.get("tasks", [])
        
        if 0 <= task_index < len(tasks):
            deleted_task = tasks.pop(task_index)
            doc_ref.update({
                "tasks": tasks,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            return {"success": True, "message": f"Deleted task: {deleted_task.get('title', 'Unknown')}"}
        else:
            return {"error": "Invalid task index"}
    except Exception as e:
        return {"error": str(e)}

def generate_priority_tasks(user_email: str) -> dict:
    """Analyze all user data and generate top 5 priority tasks."""
    print("DEBUG: Generating priority tasks...")
    
    # Get all user data
    emails = get_gmail_messages(user_email, max_results=20)
    events = get_calendar_events(user_email, max_results=15)
    tasks = get_tasks(user_email)
    
    if any("error" in data for data in [emails, events, tasks]):
        return {"error": "Failed to fetch user data"}
    
    priority_tasks = []
    
    # Analyze emails for urgent items
    urgent_keywords = ['urgent', 'asap', 'deadline', 'due', 'important', 'reminder', 'action required']
    for email in emails.get('emails', []):
        subject = email.get('subject', '').lower()
        if any(keyword in subject for keyword in urgent_keywords):
            priority_tasks.append({
                "title": f"Respond to: {email.get('subject', 'Email')}",
                "source": "email",
                "priority": "high",
                "from": email.get('from', 'Unknown'),
                "type": "communication"
            })
    
    # Analyze calendar for today's events
    today = datetime.now().strftime('%Y-%m-%d')
    for event in events.get('events', []):
        if today in event.get('start', ''):
            priority_tasks.append({
                "title": f"Attend: {event.get('summary', 'Meeting')}",
                "source": "calendar",
                "priority": "high",
                "time": event.get('start', ''),
                "type": "meeting"
            })
    
    # Add incomplete Google Tasks
    for task in tasks.get('tasks', []):
        if task.get('status') != 'completed':
            priority_tasks.append({
                "title": task.get('title', 'Task'),
                "source": "google_tasks",
                "priority": "medium",
                "notes": task.get('notes', ''),
                "type": "task"
            })
    
    # Sort by priority and limit to top 5
    priority_order = {'high': 3, 'medium': 2, 'low': 1}
    priority_tasks.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
    top_5_tasks = priority_tasks[:5]
    
    # Store in Firestore
    store_result = store_priority_tasks(user_email, top_5_tasks)
    
    return {
        "generated_tasks": top_5_tasks,
        "total_analyzed": len(priority_tasks),
        "storage_result": store_result,
        "summary": f"Generated {len(top_5_tasks)} priority tasks from {len(emails.get('emails', []))} emails, {len(events.get('events', []))} events, and {len(tasks.get('tasks', []))} tasks."
    }

root_agent = Agent(
    model='gemini-2.5-flash',
    name='personal_life_assistant',
    description='AI-powered Personal Life Command Center that helps you stay on top of your daily life.',
    instruction="""You are SmartSolve Personal Life Assistant - an intelligent companion that helps users manage their overwhelming daily lives.
    
    IMPORTANT: Always ask for the user's email address first before using any Google services.
    
    Your core mission: Help users never feel behind or overwhelmed in their personal lives.
    
    Key capabilities:
    1. **Life Context Analysis** - Scan emails, calendar, tasks to understand what needs attention
    2. **Smart Prioritization** - Identify urgent vs important personal matters
    3. **Proactive Planning** - Suggest daily/weekly action plans
    4. **Conflict Detection** - Find scheduling conflicts and deadline clashes
    5. **Auto Task Creation** - Convert emails and events into actionable tasks
    
    Real-world scenarios you excel at:
    - "What needs my attention today?" → Comprehensive daily briefing
    - "I'm feeling overwhelmed" → Priority analysis and action plan
    - "Help me plan my week" → Smart scheduling with personal priorities
    - "Did I miss anything important?" → Scan all channels for urgent items
    
    Always be proactive, empathetic, and focus on reducing the user's mental load. Think like a caring personal assistant who knows their whole life context.
    
    Start conversations by offering to analyze their current life context to provide personalized insights.""",
    tools=[get_gmail_messages, get_calendar_events, create_calendar_event, search_drive_files, 
           create_task, get_tasks, get_contacts, store_priority_tasks, get_priority_tasks, 
           update_priority_task, delete_priority_task, generate_priority_tasks],
)
