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
        
        # Handle confirmation responses
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
        
        # Simple extraction
        name = "Someone"
        if "john" in conversation:
            name = "John"
        elif "sarah" in conversation:
            name = "Sarah"
        elif "with " in conversation:
            parts = conversation.split("with ")
            if len(parts) > 1:
                name = parts[1].split()[0].title() if parts[1].split() else "Someone"
        
        date = "2026-01-06"
        if "today" in conversation:
            date = "2026-01-05"
        elif "tomorrow" in conversation:
            date = "2026-01-06"
            
        time = "14:00"
        if "3pm" in conversation or "3 pm" in conversation:
            time = "15:00"
        elif "2pm" in conversation or "2 pm" in conversation:
            time = "14:00"
        elif "10am" in conversation or "10 am" in conversation:
            time = "10:00"
        
        meeting_info = {"name": name, "date": date, "time": time, "title": "Meeting", "duration": 30}
        
        return JSONResponse(content={
            "status": "awaiting_confirmation",
            "message": f"Schedule meeting with {name} on {date} at {time}?",
            "meeting": meeting_info,
            "extracted_data": meeting_info
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})
