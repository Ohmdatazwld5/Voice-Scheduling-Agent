import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .models import MeetingRequest
from .config import GROQ_API_KEY

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_system_prompt():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    return f"""
You are a voice scheduling assistant.

IMPORTANT - Current Date Information:
- Today is: {today.strftime('%A, %B %d, %Y')} ({today.strftime('%Y-%m-%d')})
- Tomorrow is: {tomorrow.strftime('%A, %B %d, %Y')} ({tomorrow.strftime('%Y-%m-%d')})

Extract the following details from the conversation:
- name: person's name (use "MISSING" if not mentioned)
- date: MUST be in YYYY-MM-DD format or "MISSING" if not specified. Calculate relative dates:
  * "today" = {today.strftime('%Y-%m-%d')}
  * "tomorrow" = {tomorrow.strftime('%Y-%m-%d')}
  * "next week" or vague date = "MISSING"
  * "next Monday", "this Friday" etc. - calculate from today's date
- time: MUST be in HH:MM 24-hour format or "MISSING" if not specified
- title: meeting title (use "MISSING" if not specified)

Respond ONLY in valid JSON format:
{{
  "name": "person's name or MISSING",
  "date": "YYYY-MM-DD or MISSING",
  "time": "HH:MM or MISSING",
  "title": "meeting title or MISSING"
}}
"""

def extract_meeting_details(conversation: str) -> Dict[str, Any]:
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": conversation}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(GROQ_URL, json=payload, headers=headers)
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    import json
    extracted_data = json.loads(content)
    
    # Check for missing information
    missing_fields = []
    if extracted_data.get("name") == "MISSING":
        missing_fields.append("name")
    if extracted_data.get("date") == "MISSING":
        missing_fields.append("date")
    if extracted_data.get("time") == "MISSING":
        missing_fields.append("time")
    if extracted_data.get("title") == "MISSING":
        extracted_data["title"] = "Meeting"  # Title is optional
    
    if missing_fields:
        # Return incomplete data with missing fields info
        return {
            "incomplete": True,
            "missing_fields": missing_fields,
            "extracted_data": extracted_data,
            "follow_up_question": generate_follow_up_question(missing_fields)
        }
    
    # All required fields present, return MeetingRequest
    return {
        "incomplete": False,
        "meeting": MeetingRequest(
            name=extracted_data["name"],
            date=extracted_data["date"],
            time=extracted_data["time"],
            title=extracted_data.get("title", "Meeting")
        )
    }

def generate_follow_up_question(missing_fields: list) -> str:
    """Generate a natural follow-up question for missing information"""
    if len(missing_fields) == 3:  # name, date, time all missing
        return "I'd be happy to schedule that meeting. Who is the meeting with, when would you like to schedule it, and what time?"
    elif len(missing_fields) == 2:
        if "name" in missing_fields and "date" in missing_fields:
            return "Got it! Who is the meeting with and when would you like to schedule it?"
        elif "name" in missing_fields and "time" in missing_fields:
            return "Sure! Who is the meeting with and what time works best?"
        elif "date" in missing_fields and "time" in missing_fields:
            return "I can help with that. When would you like to schedule the meeting and at what time?"
    else:  # Only one field missing
        if "name" in missing_fields:
            return "Who is the meeting with?"
        elif "date" in missing_fields:
            return "When would you like to schedule the meeting?"
        elif "time" in missing_fields:
            return "What time would you prefer?"
    
    return "Could you provide the missing information?"

