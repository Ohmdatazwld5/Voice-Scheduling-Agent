from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agent import extract_meeting_details, generate_success_message
from backend.models import MeetingRequest

app = FastAPI(title="Voice Scheduling Agent API")

# CORS configuration
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://voice-scheduling-agent.vercel.app",
    "https://*.vercel.app",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    return {"message": "Voice Scheduling Agent API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/schedule")
async def schedule_meeting(request: ScheduleRequest):
    try:
        # Handle confirmation
        if request.confirmation is not None:
            if request.confirmation and request.current_data:
                meeting = MeetingRequest(**request.current_data)
                success_msg = generate_success_message(meeting)
                return {
                    "status": "confirmed",
                    "message": success_msg,
                    "meeting": request.current_data
                }
            else:
                return {
                    "status": "cancelled",
                    "message": "No problem! Let me know if you'd like to schedule a different time.",
                    "reset": True
                }
        
        # Extract meeting details
        result = extract_meeting_details(
            request.conversation,
            request.conversation_history,
            request.current_data
        )
        
        # Handle different response types
        if result.get("error"):
            return {"status": "error", "message": result["message"]}
        
        if result.get("out_of_scope"):
            return {"status": "out_of_scope", "message": result["message"]}
        
        if result.get("cancelled"):
            return {
                "status": "cancelled",
                "message": result["message"],
                "reset": result.get("reset", False)
            }
        
        if result.get("ambiguous_time"):
            return {
                "status": "ambiguous",
                "message": result["message"],
                "context": result.get("context"),
                "extracted_data": result.get("extracted_data")
            }
        
        if result.get("incomplete"):
            return {
                "status": "incomplete",
                "message": result["follow_up_question"],
                "missing_fields": result["missing_fields"],
                "extracted_data": result["extracted_data"]
            }
        
        if result.get("awaiting_confirmation"):
            meeting_dict = {
                "name": result["meeting"].name,
                "date": result["meeting"].date,
                "time": result["meeting"].time,
                "duration": result["meeting"].duration,
                "title": result["meeting"].title
            }
            return {
                "status": "awaiting_confirmation",
                "message": result["confirmation_message"],
                "meeting": meeting_dict,
                "extracted_data": result["extracted_data"]
            }
        
        return {"status": "error", "message": "Unexpected response from AI agent"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
