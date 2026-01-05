from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os

# Simple API without complex dependencies
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScheduleRequest(BaseModel):
    conversation: str
    access_token: str = ""
    conversation_history: Optional[List[str]] = []
    current_data: Optional[dict] = None
    confirmation: Optional[bool] = None

@app.get("/")
async def root():
    return {"message": "Voice Scheduling Agent API", "status": "working"}

@app.get("/health")
async def health():
    groq_key = os.environ.get("GROQ_API_KEY")
    return {
        "status": "healthy", 
        "groq_key_set": bool(groq_key),
        "groq_key_preview": groq_key[:10] + "..." if groq_key else "not set"
    }

@app.post("/schedule")
async def schedule_meeting(request: ScheduleRequest):
    """Simple mock response for now - will always work"""
    try:
        conversation = request.conversation.lower()
        
        # Simple keyword extraction (mock AI)
        name = "Unknown Person"
        if "john" in conversation:
            name = "John"
        elif "sarah" in conversation:
            name = "Sarah"
        elif "with" in conversation:
            # Try to extract name after "with"
            parts = conversation.split("with")
            if len(parts) > 1:
                potential_name = parts[1].strip().split()[0]
                if potential_name:
                    name = potential_name.title()
        
        # Extract date
        date = "2026-01-06"  # Tomorrow
        if "today" in conversation:
            date = "2026-01-05"
        elif "tomorrow" in conversation:
            date = "2026-01-06"
        elif "next week" in conversation:
            date = "2026-01-13"
        
        # Extract time
        time = "14:00"  # Default 2 PM
        if "3 pm" in conversation or "3pm" in conversation:
            time = "15:00"
        elif "10 am" in conversation or "10am" in conversation:
            time = "10:00"
        elif "morning" in conversation:
            time = "09:00"
        
        # Return confirmation
        return JSONResponse(
            status_code=200,
            content={
                "status": "awaiting_confirmation",
                "message": f"I can schedule a meeting with {name} on {date} at {time}. Should I book it?",
                "meeting": {
                    "name": name,
                    "date": date,
                    "time": time,
                    "title": "Meeting",
                    "duration": 30
                },
                "extracted_data": {
                    "name": name,
                    "date": date,
                    "time": time,
                    "title": "Meeting"
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Simple error: {str(e)}"
            }
        )

# Export for Vercel
handler = app
