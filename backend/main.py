from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.agent import extract_meeting_details
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

@app.post("/schedule")
async def schedule_meeting(request: ScheduleRequest):
    try:
        if not request.conversation:
            return {"error": "No conversation provided"}
        
        # Extract meeting details using AI
        result = extract_meeting_details(request.conversation)
        
        # Check if information is incomplete
        if result.get("incomplete"):
            return {
                "status": "incomplete",
                "missing_fields": result["missing_fields"],
                "follow_up_question": result["follow_up_question"],
                "extracted_data": result["extracted_data"]
            }
        
        meeting = result["meeting"]
        
        if not request.access_token:
            return {
                "status": "success",
                "meeting": meeting.model_dump(),
                "message": "Meeting details extracted. Add access_token to create calendar event."
            }
        
        # Create calendar event
        event = create_event(request.access_token, meeting)
        
        return {
            "status": "success",
            "meeting": meeting.model_dump(),
            "event": event
        }
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Voice Scheduling Agent API"}
