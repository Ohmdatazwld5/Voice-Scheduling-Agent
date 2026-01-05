from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from backend.agent import extract_meeting_details, generate_success_message
from backend.calender import create_event
import os

app = FastAPI()

# Add CORS middleware - MUST be after app creation but before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Voice Scheduling Agent API"}

class ScheduleRequest(BaseModel):
    conversation: str
    access_token: str = ""
    conversation_history: Optional[List[str]] = []
    current_data: Optional[dict] = None
    confirmation: Optional[bool] = None

@app.post("/schedule")
async def schedule_meeting(request: ScheduleRequest):
    try:
        # Handle explicit confirmation response
        if request.confirmation is not None:
            if request.confirmation and request.current_data:
                # User confirmed - create the meeting
                from backend.models import MeetingRequest
                meeting = MeetingRequest(**request.current_data)
                success_msg = generate_success_message(meeting)
                
                # Optionally create calendar event if access_token provided
                if request.access_token:
                    try:
                        event = create_event(request.access_token, meeting)
                        return {
                            "status": "confirmed",
                            "message": success_msg,
                            "meeting": meeting.model_dump(),
                            "event": event
                        }
                    except Exception as e:
                        return {
                            "status": "confirmed",
                            "message": success_msg + f"\n\n⚠️ Note: I couldn't create the calendar event due to a calendar issue. Error: {str(e)}",
                            "meeting": meeting.model_dump()
                        }
                
                return {
                    "status": "confirmed",
                    "message": success_msg,
                    "meeting": meeting.model_dump()
                }
            else:
                # User declined
                return {
                    "status": "cancelled",
                    "message": "No problem! Let me know if you'd like to schedule a different time.",
                    "reset": True
                }
        
        # Extract meeting details with correction/override support
        result = extract_meeting_details(
            request.conversation,
            request.conversation_history,
            request.current_data
        )
        
        # Handle out of scope
        if result.get("out_of_scope"):
            return {
                "status": "out_of_scope",
                "message": result["message"]
            }
        
        # Handle cancellation
        if result.get("cancelled"):
            return {
                "status": "cancelled",
                "message": result["message"],
                "reset": True
            }
        
        # Handle confirmation attempt with missing data
        if result.get("confirmed"):
            # This shouldn't happen if logic is correct, but safety check
            return {
                "status": "incomplete",
                "message": "I still need more information before scheduling."
            }
        
        # Handle ambiguous time
        if result.get("ambiguous_time"):
            return {
                "status": "ambiguous",
                "message": result["message"],
                "extracted_data": result["extracted_data"]
            }
        
        # Handle incomplete data
        if result.get("incomplete"):
            return {
                "status": "incomplete",
                "missing_fields": result["missing_fields"],
                "extracted_data": result["extracted_data"],
                "message": result["follow_up_question"]
            }
        
        # Handle awaiting confirmation
        if result.get("awaiting_confirmation"):
            return {
                "status": "awaiting_confirmation",
                "meeting": result["meeting"].model_dump(),
                "extracted_data": result["extracted_data"],
                "message": result["confirmation_message"]
            }
        
        return {"error": "Unexpected state"}
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "I encountered an error. Please try again."
        }

@app.get("/")
async def root():
    return {"message": "Voice Scheduling Agent API - Ready to schedule meetings!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
