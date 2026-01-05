from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import json

# Simple API without complex dependencies
app = FastAPI()

# CORS - Must be before any routes
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
@app.get("/api")
async def root():
    return JSONResponse(content={"message": "Voice Scheduling Agent API", "status": "working"})

@app.get("/health")
@app.get("/api/health")
async def health():
    return JSONResponse(content={"status": "healthy"})

def extract_meeting_info(conversation: str) -> dict:
    """Extract meeting info from conversation using simple keyword matching"""
    conv_lower = conversation.lower()
    
    # Extract name
    name = "Someone"
    if "john" in conv_lower:
        name = "John"
    elif "sarah" in conv_lower:
        name = "Sarah"
    elif "with" in conv_lower:
        parts = conv_lower.split("with")
        if len(parts) > 1:
            words = parts[1].strip().split()
            if words:
                name = words[0].title()
    
    # Extract date
    date = "2026-01-06"
    if "today" in conv_lower:
        date = "2026-01-05"
    elif "tomorrow" in conv_lower:
        date = "2026-01-06"
    
    # Extract time
    time = "14:00"
    if "3pm" in conv_lower or "3 pm" in conv_lower:
        time = "15:00"
    elif "2pm" in conv_lower or "2 pm" in conv_lower:
        time = "14:00"
    elif "10am" in conv_lower or "10 am" in conv_lower:
        time = "10:00"
    
    return {"name": name, "date": date, "time": time}

@app.post("/schedule")
@app.post("/api/schedule")
async def schedule_meeting(request: Request):
    """Handle meeting scheduling - simplified version"""
    try:
        # Parse request body manually to avoid any Pydantic issues
        body = await request.body()
        data = json.loads(body) if body else {}
        
        conversation = data.get("conversation", "")
        
        # Extract meeting info
        info = extract_meeting_info(conversation)
        
        response_data = {
            "status": "awaiting_confirmation",
            "message": f"I can schedule a meeting with {info['name']} on {info['date']} at {info['time']}. Should I book it?",
            "meeting": {
                "name": info["name"],
                "date": info["date"],
                "time": info["time"],
                "title": "Meeting",
                "duration": 30
            },
            "extracted_data": info
        }
        
        return JSONResponse(content=response_data, status_code=200)
        
    except json.JSONDecodeError as e:
        return JSONResponse(
            content={"status": "error", "message": f"Invalid JSON: {str(e)}"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Error: {str(e)}"},
            status_code=200
        )

# Vercel handler
handler = app
