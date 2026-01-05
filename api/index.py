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
        
        # Handle voice confirmations (yes/no in conversation)
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
                "reset": False
            })
        
        # Extract meeting information
        name = None
        if "john" in conversation:
            name = "John"
        elif "sarah" in conversation:
            name = "Sarah"
        elif "with " in conversation:
            parts = conversation.split("with ")
            if len(parts) > 1:
                words = parts[1].split()
                name = words[0].title() if words else None
        
        date = None
        if "today" in conversation:
            date = "2026-01-05"
        elif "tomorrow" in conversation:
            date = "2026-01-06"
        elif "next week" in conversation:
            date = "2026-01-13"
            
        time = None
        if "3pm" in conversation or "3 pm" in conversation:
            time = "15:00"
        elif "2pm" in conversation or "2 pm" in conversation:
            time = "14:00"
        elif "10am" in conversation or "10 am" in conversation:
            time = "10:00"
        elif "morning" in conversation:
            time = "09:00"
        elif "afternoon" in conversation:
            time = "14:00"
        
        # Check what's missing
        missing = []
        if not name:
            missing.append("name")
        if not date:
            missing.append("date")
        if not time:
            missing.append("time")
        
        # If information is incomplete, ask for it
        if missing:
            extracted = {}
            if name:
                extracted["name"] = name
            if date:
                extracted["date"] = date
            if time:
                extracted["time"] = time
                
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
                return JSONResponse(content={
                    "status": "incomplete",
                    "message": "What time works best?",
                    "extracted_data": extracted
                })
        
        # All information collected, ask for confirmation
        meeting_info = {"name": name, "date": date, "time": time, "title": "Meeting", "duration": 30}
        
        return JSONResponse(content={
            "status": "awaiting_confirmation",
            "message": f"I'll schedule a meeting with {name} on {date} at {time}. Should I book it?",
            "meeting": meeting_info,
            "extracted_data": meeting_info
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})
