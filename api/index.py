from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

app = FastAPI()

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
            if "john" in conversation:
                name = "John"
            elif "sarah" in conversation:
                name = "Sarah"
            elif "rajini" in conversation:
                name = "Rajini"
            elif "kamal" in conversation:
                name = "Kamal"
            elif "with " in conversation:
                parts = conversation.split("with ")
                if len(parts) > 1:
                    words = parts[1].replace(".", "").replace(",", "").strip().split()
                    if words:
                        name = words[0].title()
        
        date = extracted.get("date")
        if not date:
            if "today" in conversation:
                date = "2026-01-05"
            elif "tomorrow" in conversation:
                date = "2026-01-06"
            elif "next week" in conversation:
                date = "2026-01-13"
        
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
