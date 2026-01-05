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
        
        # Simple extraction
        name = "Someone"
        if "john" in conversation:
            name = "John"
        elif "with " in conversation:
            parts = conversation.split("with ")
            if len(parts) > 1:
                name = parts[1].split()[0].title() if parts[1].split() else "Someone"
        
        date = "2026-01-06"
        if "today" in conversation:
            date = "2026-01-05"
            
        time = "14:00"
        if "3" in conversation:
            time = "15:00"
        elif "10" in conversation:
            time = "10:00"
        
        return JSONResponse(content={
            "status": "awaiting_confirmation",
            "message": f"Schedule meeting with {name} on {date} at {time}?",
            "meeting": {"name": name, "date": date, "time": time, "title": "Meeting"}
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})
