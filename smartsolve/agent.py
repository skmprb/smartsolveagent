from google.adk.agents.llm_agent import Agent
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.cloud import firestore
from google.auth.transport.requests import Request
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import List, Dict

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
            client_data = json.load(f)["web"]
        
        credentials = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_data["client_id"],
            client_secret=client_data["client_secret"]
        )
        
        # Refresh if expired
        if credentials.expired:
            print("DEBUG: Token expired, refreshing...")
            credentials.refresh(Request())
            # Update Firestore with new token
            doc_ref.set({
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
        
        return credentials.token
    except Exception as e:
        print(f"DEBUG: Firestore error: {str(e)}")
        return None

def get_gmail_messages(user_email: str, query: str = "", max_results: int = None, date_from: str = None, date_to: str = None) -> dict:
    """Fetch Gmail messages for the user. By default fetches emails from yesterday to today.
    
    Args:
        user_email: User's email address (required)
        query: Gmail search query (optional)
        max_results: Maximum number of results (optional, default: 20)
        date_from: Start date in YYYY/MM/DD format (optional, default: yesterday)
        date_to: End date in YYYY/MM/DD format (optional, default: today)
    """
    print(f"DEBUG: get_gmail_messages called with user_email: {user_email}")
    
    # Set defaults
    if max_results is None:
        max_results = 20
    
    # Set default date range: yesterday to tomorrow (to include today's emails)
    if date_from is None:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        date_from = yesterday
    if date_to is None:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
        date_to = tomorrow
    
    # Build date range query
    date_query = f"after:{date_from} before:{date_to}"
    
    # Combine with existing query
    if query:
        query = f"{query} {date_query}"
    else:
        query = date_query
    
    print(f"DEBUG: Final query: {query}")
    
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

def get_current_datetime() -> dict:
    """Get current system date and time. Use this to calculate relative dates like 'yesterday', 'today', 'last week'."""
    now = datetime.now()
    return {
        "current_datetime": now.isoformat(),
        "date": now.strftime('%Y-%m-%d'),
        "time": now.strftime('%H:%M:%S'),
        "timestamp": int(now.timestamp()),
        "formatted": now.strftime('%Y/%m/%d %H:%M')
    }

def store_priority_tasks(user_email: str, tasks: str) -> dict:
    """Store user's top 5 priority tasks in Firestore. Pass tasks as JSON string."""
    try:
        import json
        tasks_list = json.loads(tasks) if isinstance(tasks, str) else tasks
        
        db = firestore.Client(database='smartsolve')
        doc_ref = db.collection('priority_tasks').document(user_email)
        
        doc_ref.set({
            "tasks": tasks_list[:5],  # Limit to top 5
            "updated_at": firestore.SERVER_TIMESTAMP,
            "user_email": user_email
        })
        
        return {"success": True, "message": f"Stored {len(tasks_list[:5])} priority tasks"}
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

def update_priority_task(user_email: str, task_index: int, updated_task: str) -> dict:
    """Update a specific priority task. Pass updated_task as JSON string."""
    try:
        import json
        task_dict = json.loads(updated_task) if isinstance(updated_task, str) else updated_task
        
        db = firestore.Client(database='smartsolve')
        doc_ref = db.collection('priority_tasks').document(user_email)
        doc = doc_ref.get()
        
        if not doc.exists:
            return {"error": "No priority tasks found to update"}
        
        data = doc.to_dict()
        tasks = data.get("tasks", [])
        
        if 0 <= task_index < len(tasks):
            tasks[task_index] = task_dict
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

def send_email(user_email: str, to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> dict:
    """Send an email via Gmail."""
    token = get_user_token(user_email)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('gmail', 'v1', credentials=credentials)
    
    try:
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        message.attach(MIMEText(body, 'plain'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {"success": True, "message_id": result['id']}
    except Exception as e:
        return {"error": str(e)}

def delete_email(user_email: str, message_id: str) -> dict:
    """Delete an email by message ID."""
    token = get_user_token(user_email)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('gmail', 'v1', credentials=credentials)
    
    try:
        service.users().messages().delete(userId='me', id=message_id).execute()
        return {"success": True, "message": f"Email {message_id} deleted"}
    except Exception as e:
        return {"error": str(e)}

def modify_email_labels(user_email: str, message_id: str, add_labels: str = "", remove_labels: str = "") -> dict:
    """Modify email labels (mark as read/unread, add/remove labels).
    
    Common labels: UNREAD, STARRED, IMPORTANT, SPAM, TRASH
    Pass labels as comma-separated string: 'STARRED,IMPORTANT'
    """
    token = get_user_token(user_email)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('gmail', 'v1', credentials=credentials)
    
    try:
        body = {}
        if add_labels:
            body['addLabelIds'] = [label.strip() for label in add_labels.split(',')]
        if remove_labels:
            body['removeLabelIds'] = [label.strip() for label in remove_labels.split(',')]
        
        result = service.users().messages().modify(
            userId='me',
            id=message_id,
            body=body
        ).execute()
        
        return {"success": True, "message_id": result['id']}
    except Exception as e:
        return {"error": str(e)}

def reply_to_email(user_email: str, message_id: str, reply_body: str) -> dict:
    """Reply to an email."""
    token = get_user_token(user_email)
    if not token:
        return {"error": "User not authenticated"}
    
    credentials = Credentials(token=token)
    service = build('gmail', 'v1', credentials=credentials)
    
    try:
        import base64
        from email.mime.text import MIMEText
        
        # Get original message
        original = service.users().messages().get(userId='me', id=message_id).execute()
        headers = original['payload'].get('headers', [])
        
        original_subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        original_from = next((h['value'] for h in headers if h['name'] == 'From'), '')
        thread_id = original.get('threadId')
        
        # Create reply
        reply = MIMEText(reply_body)
        reply['to'] = original_from
        reply['subject'] = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
        reply['In-Reply-To'] = message_id
        reply['References'] = message_id
        
        raw_reply = base64.urlsafe_b64encode(reply.as_bytes()).decode()
        
        result = service.users().messages().send(
            userId='me',
            body={
                'raw': raw_reply,
                'threadId': thread_id
            }
        ).execute()
        
        return {"success": True, "message_id": result['id']}
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
    instruction="""You are SmartSolve - an intelligent personal productivity assistant that helps users manage their tasks, calendar, and daily workflow efficiently.
    
    CONTEXT: The user has already provided their name and email when they started this session. You have access to their Google services (Gmail, Calendar, Tasks, Drive) and can help them with productivity tasks.
    
    Your core capabilities:
    1. **Task Management** - Help with Google Tasks, create new tasks, analyze priorities
    2. **Calendar Management** - View events, create meetings, detect conflicts
    3. **Email Management** - Read, send, reply, delete emails, modify labels
    4. **Priority Planning** - Generate and manage priority task lists
    5. **Productivity Insights** - Analyze workload and suggest optimizations
    
    Communication style:
    - Be direct and helpful
    - Don't ask for email/name repeatedly - you already have this context
    - Focus on actionable advice and solutions
    - Provide specific, practical recommendations
    - Be concise but thorough
    
    When users ask for help:
    - Analyze their current tasks and calendar
    - Provide specific next steps
    - Offer to create tasks or calendar events when relevant
    - Give priority recommendations based on deadlines and importance
    
    **Date/Time Email Queries**: When users ask for emails from specific dates/times (e.g., "summarize emails from yesterday evening 6pm" or "emails from 20/12/2025 to 21/12/2025"):
    - FIRST call get_current_datetime() to get the system time
    - **IMPORTANT Gmail Date Logic**: Gmail's before:YYYY/MM/DD excludes that date (ends at 11:59 PM the day before)
    - To get emails from Dec 19, 2025, use: after:2025/12/18 before:2025/12/20 (this gets Dec 19)
    - For date ranges like "from 20/12/2025 to 21/12/2025", use get_gmail_messages with date_from="2025/12/19" and date_to="2025/12/22"
    - For single dates with time like "yesterday 6pm", calculate the target datetime and use query parameter: "after:YYYY/MM/DD HH:MM"
    - Gmail date format: YYYY/MM/DD for dates, YYYY/MM/DD HH:MM for datetime
    - Summarize the retrieved emails focusing on key points, senders, and action items
    
    Remember: You're here to make their life easier and more organized, not to ask for information they've already provided.

    *Today's Date: {datetime.datetime.now().strftime("%Y-%m-%d")}*
   
    """,
    tools=[get_current_datetime, get_gmail_messages, send_email, reply_to_email, delete_email, modify_email_labels,
           get_calendar_events, create_calendar_event, search_drive_files, create_task, get_tasks, get_contacts,
           store_priority_tasks, get_priority_tasks, update_priority_task, delete_priority_task, generate_priority_tasks],
)
