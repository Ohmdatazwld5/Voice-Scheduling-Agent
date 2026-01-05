from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import requests
from datetime import datetime, timedelta

# Get API key from environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI(title="Voice Scheduling Agent API")

# Global exception handler - ALL errors return JSON
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=200,  # Return 200 so browser doesn't treat as error
        content={
            "status": "error",
            "message": f"Server Error: {str(exc)}"
        }
    )

# CORS configuration
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

def get_system_prompt():
    """Generate system prompt with current date info"""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    return f"""You are a voice scheduling assistant.
    
Current Date: {today.strftime('%A, %B %d, %Y')}
Tomorrow: {tomorrow.strftime('%A, %B %d, %Y')}

Extract meeting details and respond ONLY in valid JSON:
{{
  "intent": "SCHEDULE",
  "name": "person or MISSING",
  "date": "YYYY-MM-DD or MISSING",
  "time": "HH:MM or MISSING",
  "duration": number or null,
  "title": "meeting title or MISSING"
}}"""

def extract_meeting_details(conversation: str):
    """Extract meeting details using Groq API"""
    if not GROQ_API_KEY:
        return {"error": True, "message": "API key not configured"}
    
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": conversation}
    ]
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=10)
        
        # Check response status
        if response.status_code != 200:
            return {
                "error": True,
                "message": f"Groq API error ({response.status_code}): {response.text[:100]}"
            }
        
        # Parse JSON response
        response_json = response.json()
        content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content:
            return {"error": True, "message": "No content from AI"}
        
        # Parse the JSON content
        parsed = json.loads(content)
        return parsed
        
    except json.JSONDecodeError as e:
        return {"error": True, "message": f"Invalid JSON from AI: {str(e)}"}
    except requests.exceptions.Timeout:
        return {"error": True, "message": "Groq API timeout - please try again"}
    except Exception as e:
        return {"error": True, "message": f"Groq API Error: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "Voice Scheduling Agent API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "GROQ_KEY_SET": bool(GROQ_API_KEY)}

@app.post("/schedule")
async def schedule_meeting(request: ScheduleRequest):
    try:
        # Check if API key is set
        if not GROQ_API_KEY:
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": "GROQ_API_KEY not set in environment"
            })
        
        # Simple handling for now
        result = extract_meeting_details(request.conversation)
        
        if result.get("error"):
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": result.get("message", "Unknown error")
            })
        
        # Check for missing fields
        missing = []
        for field in ["name", "date", "time"]:
            val = result.get(field)
            if not val or val == "MISSING":
                missing.append(field)
        
        if missing:
            return JSONResponse(status_code=200, content={
                "status": "incomplete",
                "message": f"I need to know: {', '.join(missing)}",
                "missing_fields": missing,
                "extracted_data": result
            })
        
        return JSONResponse(status_code=200, content={
            "status": "awaiting_confirmation",
            "message": f"I can schedule {result.get('title', 'Meeting')} with {result.get('name')} on {result.get('date')} at {result.get('time')}. Confirm?",
            "meeting": result,
            "extracted_data": result
        })
    
    except Exception as e:
        return JSONResponse(status_code=200, content={
            "status": "error",
            "message": f"Error: {str(e)}"
        })

# Export for Vercel
handler = app
