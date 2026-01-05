from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import json
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = FastAPI()

# In-memory storage for tokens (for demo - use database in production)
user_tokens = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api")
@app.get("/api/")
def root():
    return JSONResponse(content={"message": "API Working", "status": "ok"})

@app.get("/api/health")
def health():
    return JSONResponse(content={"status": "healthy"})

@app.get("/api/auth/google")
async def google_auth():
    """Initiate Google OAuth flow"""
    try:
        # Create OAuth credentials from environment
        client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": [os.getenv("REDIRECT_URI", "https://voice-scheduling-agent-7exx.vercel.app/api/auth/callback")],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=["https://www.googleapis.com/auth/calendar"],
            redirect_uri=client_config["web"]["redirect_uris"][0]
        )
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return JSONResponse(content={"auth_url": auth_url, "state": state})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/auth/callback")
async def google_callback(code: str = None, state: str = None):
    """Handle Google OAuth callback"""
    try:
        if not code:
            return JSONResponse(content={"error": "No code provided"}, status_code=400)
        
        client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": [os.getenv("REDIRECT_URI", "https://voice-scheduling-agent-7exx.vercel.app/api/auth/callback")],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=["https://www.googleapis.com/auth/calendar"],
            redirect_uri=client_config["web"]["redirect_uris"][0]
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store token (use session ID in production)
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
        user_tokens["default_user"] = token_data
        
        # Redirect back to app with success
        return RedirectResponse(url="/?auth=success")
    except Exception as e:
        return RedirectResponse(url=f"/?auth=error&message={str(e)}")

@app.post("/api/schedule")
async def schedule(request: Request):
    try:
        body = await request.body()
        data = json.loads(body.decode()) if body else {}
        conversation = data.get("conversation", "").lower()
        confirmation = data.get("confirmation")
        current_data = data.get("current_data", {})
        conversation_history = data.get("conversation_history", [])
        
        # Handle confirmation responses (button clicks)
        if confirmation is not None:
            if confirmation:
                meeting_data = current_data if current_data else {"name": "Guest", "date": "2026-01-06", "time": "14:00", "title": "Meeting", "duration": 30}
                
                # Try to create actual Google Calendar event
                calendar_event = None
                if "default_user" in user_tokens:
                    try:
                        token_data = user_tokens["default_user"]
                        credentials = Credentials(
                            token=token_data["token"],
                            refresh_token=token_data.get("refresh_token"),
                            token_uri=token_data["token_uri"],
                            client_id=token_data["client_id"],
                            client_secret=token_data["client_secret"],
                            scopes=token_data["scopes"]
                        )
                        
                        service = build("calendar", "v3", credentials=credentials)
                        
                        # Create event
                        start_datetime = datetime.fromisoformat(f"{meeting_data['date']}T{meeting_data['time']}")
                        end_datetime = start_datetime + timedelta(minutes=meeting_data.get('duration', 30))
                        
                        event = {
                            "summary": meeting_data.get("title", "Meeting"),
                            "description": f"Scheduled with {meeting_data['name']}",
                            "start": {
                                "dateTime": start_datetime.isoformat(),
                                "timeZone": "America/New_York",
                            },
                            "end": {
                                "dateTime": end_datetime.isoformat(),
                                "timeZone": "America/New_York",
                            },
                        }
                        
                        calendar_event = service.events().insert(calendarId="primary", body=event).execute()
                        
                        return JSONResponse(content={
                            "status": "confirmed",
                            "message": "✅ Meeting scheduled successfully in Google Calendar!",
                            "meeting": meeting_data,
                            "calendar_link": calendar_event.get("htmlLink")
                        })
                    except Exception as e:
                        # If calendar creation fails, still confirm but show error
                        return JSONResponse(content={
                            "status": "confirmed",
                            "message": f"✅ Meeting confirmed, but couldn't add to Google Calendar: {str(e)}. Please connect your Google Calendar.",
                            "meeting": meeting_data,
                            "needs_auth": True
                        })
                else:
                    # No Google auth yet
                    return JSONResponse(content={
                        "status": "confirmed",
                        "message": "✅ Meeting confirmed! Connect Google Calendar to add it automatically.",
                        "meeting": meeting_data,
                        "needs_auth": True
                    })
                
                return JSONResponse(content={
                    "status": "confirmed",
                    "message": "✅ Meeting scheduled successfully!",
                    "meeting": meeting_data
                })
            else:
                return JSONResponse(content={
                    "status": "cancelled",
                    "message": "Meeting cancelled. What would you like to do instead?",
                    "reset": False
                })
        
        # Detect if user is starting a NEW meeting request (ignore old data)
        new_meeting_keywords = ["schedule a", "book a", "new meeting", "another meeting", "different time", "available time", "other time"]
        is_new_request = any(keyword in conversation for keyword in new_meeting_keywords)
        
        # If it's a new request, clear old data
        if is_new_request and current_data:
            current_data = {}
        
        # Handle voice confirmations (yes/no in conversation) - only if we have current_data
        if current_data and ("yes" in conversation or "yeah" in conversation or "sure" in conversation or "confirm" in conversation):
            return JSONResponse(content={
                "status": "confirmed",
                "message": "✅ Meeting scheduled successfully!",
                "meeting": current_data
            })
        
        if current_data and ("no" in conversation or "cancel" in conversation or "nope" in conversation):
            return JSONResponse(content={
                "status": "cancelled",
                "message": "Meeting cancelled. What would you like to do instead?",
                "reset": True
            })
        
        # Start with existing data or empty dict
        extracted = current_data.copy() if current_data else {}
        
        # Extract NEW information from current message
        name = extracted.get("name")
        if not name:
            # First check for known names
            if "john" in conversation:
                name = "John"
            elif "sarah" in conversation:
                name = "Sarah"
            elif "rajini" in conversation:
                name = "Rajini"
            elif "kamal" in conversation:
                name = "Kamal"
            elif "sadish" in conversation or "satish" in conversation:
                name = "Sadish"
            elif "with " in conversation:
                parts = conversation.split("with ")
                if len(parts) > 1:
                    words = parts[1].replace(".", "").replace(",", "").strip().split()
                    if words:
                        name = words[0].title()
            else:
                # If we're expecting a name (previous question was about name), extract it
                if conversation_history and "who would you like to meet" in str(conversation_history[-1:]).lower():
                    # Extract first capitalized word or any word that looks like a name
                    words = conversation.replace(".", "").replace(",", "").strip().split()
                    for word in words:
                        # Skip common words
                        if word.lower() not in ["i", "a", "the", "to", "with", "at", "on", "for", "meeting", "schedule", "book", "minutes", "hour", "am", "pm"]:
                            if len(word) > 2:  # Name should be at least 3 chars
                                name = word.title()
                                break
        
        date = extracted.get("date")
        if not date:
            import re
            from datetime import datetime, timedelta
            
            # Keywords for relative dates
            if "today" in conversation:
                date = "2026-01-05"
            elif "tomorrow" in conversation:
                date = "2026-01-06"
            elif "next week" in conversation:
                date = "2026-01-13"
            else:
                # Try to parse specific dates like "7th January", "January 7", "Jan 7"
                months = {
                    'january': 1, 'jan': 1,
                    'february': 2, 'feb': 2,
                    'march': 3, 'mar': 3,
                    'april': 4, 'apr': 4,
                    'may': 5,
                    'june': 6, 'jun': 6,
                    'july': 7, 'jul': 7,
                    'august': 8, 'aug': 8,
                    'september': 9, 'sep': 9, 'sept': 9,
                    'october': 10, 'oct': 10,
                    'november': 11, 'nov': 11,
                    'december': 12, 'dec': 12
                }
                
                # Pattern: "7th January" or "January 7th" or "January 7"
                for month_name, month_num in months.items():
                    # Try "7th January" format
                    match = re.search(rf'(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_name}', conversation, re.IGNORECASE)
                    if match:
                        day = int(match.group(1))
                        date = f"2026-{month_num:02d}-{day:02d}"
                        break
                    
                    # Try "January 7th" format
                    match = re.search(rf'{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?', conversation, re.IGNORECASE)
                    if match:
                        day = int(match.group(1))
                        date = f"2026-{month_num:02d}-{day:02d}"
                        break
        
        time = extracted.get("time")
        duration = extracted.get("duration", 30)
        
        if not time:
            # Match various time formats
            import re
            
            # Try to find time patterns like "10:00", "3pm", "3 pm", "10 am", etc.
            time_patterns = [
                r'(\d{1,2}):(\d{2})\s*([ap]m)?',  # 10:00, 10:00 AM
                r'(\d{1,2})\s*([ap]m)',            # 10am, 10 am, 3pm
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, conversation, re.IGNORECASE)
                if match:
                    hour = int(match.group(1))
                    minute = match.group(2) if len(match.groups()) > 1 and match.group(2) else "00"
                    meridiem = match.group(3) if len(match.groups()) > 2 else match.group(2) if len(match.groups()) > 1 else None
                    
                    # Convert to 24-hour format
                    if meridiem:
                        meridiem = meridiem.lower()
                        if meridiem == 'pm' and hour != 12:
                            hour += 12
                        elif meridiem == 'am' and hour == 12:
                            hour = 0
                    
                    time = f"{hour:02d}:{minute if isinstance(minute, str) else '00'}"
                    break
            
            # Fallback to keyword matching
            if not time:
                if "morning" in conversation:
                    time = "09:00"
                elif "afternoon" in conversation:
                    time = "14:00"
            
            # Try to detect duration from "X to Y" pattern
            duration_match = re.search(r'(\d{1,2}):(\d{2}).*?to.*?(\d{1,2}):(\d{2})', conversation)
            if duration_match:
                start_hour = int(duration_match.group(1))
                start_min = int(duration_match.group(2))
                end_hour = int(duration_match.group(3))
                end_min = int(duration_match.group(4))
                
                # Calculate duration in minutes
                start_total = start_hour * 60 + start_min
                end_total = end_hour * 60 + end_min
                duration = end_total - start_total
        
        # Update extracted with newly found information
        if name:
            extracted["name"] = name
        if date:
            extracted["date"] = date
        if time:
            extracted["time"] = time
        if duration:
            extracted["duration"] = duration
        extracted["title"] = "Meeting"
        
        # Check what's still missing
        missing = []
        if not name:
            missing.append("name")
        if not date:
            missing.append("date")
        if not time:
            missing.append("time")
        
        # If information is incomplete, ask for next missing piece
        if missing:
            if "name" in missing:
                return JSONResponse(content={
                    "status": "incomplete",
                    "message": "Who would you like to meet with?",
                    "extracted_data": extracted
                })
            elif "date" in missing:
                return JSONResponse(content={
                    "status": "incomplete",
                    "message": "When would you like to schedule the meeting?",
                    "extracted_data": extracted
                })
            elif "time" in missing:
                # Suggest available time slots
                suggested_times = ["9:00 AM", "10:00 AM", "2:00 PM", "3:00 PM", "4:00 PM"]
                return JSONResponse(content={
                    "status": "incomplete",
                    "message": f"What time works best? Here are some available slots: {', '.join(suggested_times)}",
                    "extracted_data": extracted,
                    "suggestions": suggested_times
                })
        
        # All information collected, ask for confirmation
        return JSONResponse(content={
            "status": "awaiting_confirmation",
            "message": f"I'll schedule a meeting with {name} on {date} at {time}. Should I book it?",
            "meeting": extracted,
            "extracted_data": extracted
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})
