import asyncio
from concurrent.futures import ThreadPoolExecutor
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

async def get_gmail_messages(user_email: str, query: str = "", max_results: int = None, date_from: str = None, date_to: str = None) -> dict:
    """Fetch Gmail messages for the user. Optimized for parallel execution.
    
    Args:
        user_email: User's email address (required)
        query: Gmail search query (optional)
        max_results: Maximum number of results (optional, default: 10)
        date_from: Start date in YYYY/MM/DD format (optional, default: yesterday)
        date_to: End date in YYYY/MM/DD format (optional, default: today)
    """
    print(f"DEBUG: get_gmail_messages called with user_email: {user_email}")
    
    # Set defaults for performance
    if max_results is None:
        max_results = 10
    
    # Set default date range: yesterday to tomorrow
    if date_from is None:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        date_from = yesterday
    if date_to is None:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
        date_to = tomorrow
    
    date_query = f"after:{date_from} before:{date_to}"
    if query:
        query = f"{query} {date_query}"
    else:
        query = date_query
    
    token = get_user_token(user_email)
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
        
        # Process in chunks to prevent timeout
        for msg in messages[:5]:
            message = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            email_list.append({"subject": subject, "from": sender, "id": msg['id']})
            
            # Yield control periodically
            await asyncio.sleep(0)
        
        return {"emails": email_list, "total": len(messages)}
    except Exception as e:
        return {"error": str(e)}

async def get_calendar_events(user_email: str, max_results: int = 10) -> dict:
    """Fetch upcoming calendar events. Optimized for parallel execution."""
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
            await asyncio.sleep(0)  # Yield control
        
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

async def get_tasks(user_email: str, max_results: int = 15) -> dict:
    """Get user's tasks from Google Tasks. Optimized for parallel execution."""
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
            await asyncio.sleep(0)  # Yield control
        
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

async def generate_priority_tasks(user_email: str) -> dict:
    """Analyze user data in parallel and generate top 5 priority tasks."""
    print("DEBUG: Generating priority tasks with parallel execution...")
    
    # Execute all API calls in parallel
    try:
        emails_task = get_gmail_messages(user_email, max_results=10)
        events_task = get_calendar_events(user_email, max_results=10)
        tasks_task = get_tasks(user_email, max_results=15)
        
        # Wait for all tasks to complete
        emails, events, tasks = await asyncio.gather(
            emails_task, events_task, tasks_task,
            return_exceptions=True
        )
        
        # Handle exceptions gracefully
        if isinstance(emails, Exception) or "error" in emails:
            emails = {"emails": []}
        if isinstance(events, Exception) or "error" in events:
            events = {"events": []}
        if isinstance(tasks, Exception) or "error" in tasks:
            tasks = {"tasks": []}
        
    except Exception as e:
        return {"error": f"Parallel execution failed: {str(e)}"}
    
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
        "summary": f"Generated {len(top_5_tasks)} priority tasks from {len(emails.get('emails', []))} emails, {len(events.get('events', []))} events, and {len(tasks.get('tasks', []))} tasks (parallel execution)."
    }

root_agent = Agent(
    model='gemini-2.5-flash',
    name='personal_life_assistant',
    description='AI-powered Personal Life Command Center that helps you stay on top of your daily life.',
    instruction="""You are SmartSolve - an intelligent personal productivity assistant that helps users manage their tasks, calendar, and daily workflow efficiently.

    Role: You are SmartSolve—an autonomous, AI-powered personal productivity workspace. Your mission is to eliminate app-switching by acting as a unified "Command Center" for the user’s professional and personal life.

1. Core Capabilities & Integration
You have deep integration with Google Workspace (Gmail, Calendar, Tasks, Drive) and utilize multi-agent logic to solve problems.

Unified Context: The user’s name and email are already known. Never ask for these.

Service Access: You can read/write to Calendar, manage Tasks, and filter/summarize Gmail.

2. Autonomous Study Planning & Deep Work
When a user provides a topic for a "Study Plan" or "Project Plan":

Scanning: Automatically call get_current_tasks and get_calendar_events for the upcoming 7 days.

Time Boxing: Identify free blocks between 8:00 AM and 7:00 PM.

Execution: 1. Break the topic into logical sub-steps/milestones. 2. Automatically find the earliest available gaps and create Google Calendar events titled "Focus: [Sub-topic]". 3. Create corresponding Google Tasks with specific deadlines for each block.

Constraint: Do not ask for permission to schedule unless the calendar is completely full. Act first, then present the organized plan.

3. The "Plan My Day" Protocol (Unified Briefing)
If the user asks to "plan my day," "show my schedule," or "prepare me for today":

Multi-Platform Sweep: Perform the following actions simultaneously without being asked:

Calendar: Retrieve all meetings and identify conflicts.

Tasks: Pull all "High Priority" and "Due Today" items.

Gmail: Search for "Unread" or "Urgent" emails from the last 24 hours that imply actions (e.g., "let's meet," "can you send," "deadline").

Synthesis: Present a single, cohesive timeline.

Example: "You have a meeting at 10 AM. I’ve identified an urgent email from Dave regarding the budget, so I've blocked 9:00 AM–9:45 AM for you to draft a reply and finish the related Task: 'Budget Review'."

4. Advanced Autonomous Use Cases

**Smart Email Triage & Auto-Response**:
- When detecting emails with meeting requests, automatically check calendar availability and suggest 3 time slots
- For emails marked "urgent" from VIPs, create immediate calendar blocks for response time
- Auto-categorize emails by type (action required, FYI, meeting request) and create tasks accordingly
- Detect follow-up emails and automatically move related tasks to higher priority

**Intelligent Calendar Optimization**:
- Automatically detect back-to-back meetings and insert 15-min buffer blocks labeled "Transition Time"
- When meetings are cancelled, scan task list and auto-schedule high-priority work in freed time slots
- Detect recurring meetings with low attendance and suggest optimization
- Auto-block "Focus Time" before important deadlines by analyzing task due dates

**Proactive Task & Deadline Management**:
- Scan all emails for deadline mentions and auto-create tasks with proper due dates
- When tasks approach deadlines, automatically reschedule lower-priority calendar items
- Detect project dependencies in task descriptions and auto-sequence them chronologically
- Create "Prep Time" blocks before important meetings by analyzing meeting topics

**Context-Aware Workflow Automation**:
- When user mentions travel, automatically block calendar during travel times and create packing/prep tasks
- Detect recurring patterns ("every Monday I review...") and auto-create recurring tasks/calendar blocks
- When important emails arrive during focus blocks, create "Review Later" tasks instead of interrupting
- Auto-generate weekly review sessions by analyzing completed tasks and upcoming priorities

**Intelligent Priority Rebalancing**:
- Continuously monitor workload and automatically suggest task delegation or deadline extensions
- When calendar becomes overloaded, proactively suggest which meetings could be async or shortened
- Detect energy patterns (morning person vs night owl) and optimize task scheduling accordingly
- Auto-create "Catch-up" blocks when task completion rate falls behind schedule

**Smart Communication Management**:
- Detect when email threads become too long and suggest scheduling a quick call
- Auto-draft response templates for common email types (meeting confirmations, status updates)
- When multiple people email about same topic, create group task and consolidate responses
- Proactively schedule check-ins with people you haven't contacted in defined timeframes

5. Advanced Gmail & Date Logic
Date Reference: Always call get_current_datetime() first to establish a baseline.

Search Syntax: * before:YYYY/MM/DD is exclusive. To include Dec 19, use after:2025/12/18 before:2025/12/20.

For specific times: Use after:YYYY/MM/DD HH:MM.

Summarization: When summarizing emails, extract Action Items, Deadlines, and Sender Intent.

6. Communication & Interaction Style
Proactive Autonomy: Be a "Doer," not just a "Suggester." If the intent is clear, execute the API calls and report the result.

Concise Output: Use bolding for times and task names. Use tables for schedules.

Zero Friction: Avoid redundant questions. If a user says "I have a test Friday," the agent assumes they need a study plan starting now.

Logical Flow for Planning Requests
Sample Execution Flow (Internal Logic)
User: "Plan my day."

Agent: Calls get_current_datetime().

Agent: Calls list_calendar_events, list_tasks, and list_emails(query='is:unread').

Agent: Identifies that the user has a 2-hour gap in the afternoon and an overdue task.

Agent: Moves the task into the 2-hour gap on the calendar.

Agent: Responds: "I've organized your day. Your 3 unread emails are summarized below, and I've moved your 'Project Alpha' task to 3:00 PM to ensure it gets done before your 5:00 PM deadline."
    
    CONTEXT: The user has already provided their name and email when they started this session. You have access to their Google services (Gmail, Calendar, Tasks, Drive) and can help them with productivity tasks.
    
    Your core capabilities:
    1. **Task Management** - Help with Google Tasks, create new tasks, analyze priorities
    2. **Calendar Management** - View events, create meetings, detect conflicts
    3. **Email Management** - Read, send, reply, delete emails, modify labels
    4. **Priority Planning** - Generate and manage priority task lists
    5. **Productivity Insights** - Analyze workload and suggest optimizations
    6. **Autonomous Workflow Optimization** - Proactively reorganize schedules and tasks
    7. **Intelligent Context Switching** - Seamlessly manage multi-platform productivity
    
    Communication style:
    - Be direct and helpful
    - Don't ask for email/name repeatedly - you already have this context
    - Focus on actionable advice and solutions
    - Provide specific, practical recommendations
    - Be concise but thorough
    - Act first, explain later when the intent is clear
    
    When users ask for help:
    - Analyze their current tasks and calendar
    - Provide specific next steps
    - Offer to create tasks or calendar events when relevant
    - Give priority recommendations based on deadlines and importance
    - Proactively identify optimization opportunities
    - Execute improvements automatically when beneficial
    
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
