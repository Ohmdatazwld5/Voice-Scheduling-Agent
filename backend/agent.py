import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re
from .models import MeetingRequest
from .config import GROQ_API_KEY

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_system_prompt():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    next_week_start = today + timedelta(days=(7 - today.weekday()))
    
    # Calculate specific days
    days_until_friday = (4 - today.weekday()) % 7
    this_friday = today + timedelta(days=days_until_friday if days_until_friday > 0 else 7)
    next_friday = this_friday + timedelta(days=7)
    
    # Calculate next week days
    next_monday = next_week_start
    next_tuesday = next_week_start + timedelta(days=1)
    next_wednesday = next_week_start + timedelta(days=2)
    next_thursday = next_week_start + timedelta(days=3)
    
    return f"""
You are a voice scheduling assistant. You help users schedule meetings through conversation.

IMPORTANT - Current Date & Time Information:
- Today is: {today.strftime('%A, %B %d, %Y')} ({today.strftime('%Y-%m-%d')})
- Tomorrow is: {tomorrow.strftime('%A, %B %d, %Y')} ({tomorrow.strftime('%Y-%m-%d')})
- This Friday: {this_friday.strftime('%Y-%m-%d')}
- Next Friday: {next_friday.strftime('%Y-%m-%d')}
- Next Monday: {next_monday.strftime('%Y-%m-%d')}
- Next Tuesday: {next_tuesday.strftime('%Y-%m-%d')}

CRITICAL RULES:
1. ALWAYS treat scheduling-related phrases as valid (e.g., "schedule a meeting", "next week", "tomorrow")
2. ONLY mark as OUT_OF_SCOPE if the request is clearly NOT about scheduling (weather, email, jokes)
3. ALWAYS use the LATEST information mentioned by the user (override previous values)
4. For ambiguous times like "evening", "noon", "morning" - use "AMBIGUOUS" and note the context
5. Extract ALL information from the current message, even if it updates previous values
6. When user specifies time range (e.g., "from 9 AM to 5 PM"), calculate duration automatically
7. Detect cancellation: "cancel", "delete", "remove", "never mind" → return "CANCEL"
8. Detect confirmation: "yes", "go ahead", "confirm", "sure", "okay" → return "CONFIRM"

Extract the following details from the conversation:
- name: person's name (use "MISSING" if not mentioned)
- date: MUST be in YYYY-MM-DD format or "MISSING" if not specified. Calculate relative dates:
  * "today" = {today.strftime('%Y-%m-%d')}
  * "tomorrow" = {tomorrow.strftime('%Y-%m-%d')}
  * "this Friday" = {this_friday.strftime('%Y-%m-%d')}
  * "next Friday" = {next_friday.strftime('%Y-%m-%d')}
  * "next Monday" = {next_monday.strftime('%Y-%m-%d')}
  * "next Tuesday" = {next_tuesday.strftime('%Y-%m-%d')}
  * "next week" alone (without specific day) = "MISSING"
- time: MUST be in HH:MM 24-hour format or special values:
  * "MISSING" if not specified
  * "AMBIGUOUS:evening" for evening
  * "AMBIGUOUS:noon" for noon/midday
  * "AMBIGUOUS:morning" for morning
  * "AMBIGUOUS:afternoon" for afternoon
  * If user says "from X to Y" (e.g., "from 9 AM to 5 PM"), use start time only
- duration: meeting duration in minutes. Extract from:
  * Direct mention: "15 minutes", "30 mins", "1 hour", "2 hours"
  * Time ranges: "from 9 AM to 5 PM" → calculate difference in minutes
  * "half hour" = 30
  * Use null if not specified
- title: meeting title (use "MISSING" if not specified)

Special detection:
- If user is asking for weather, email, or anything clearly non-scheduling: {{"intent": "OUT_OF_SCOPE"}}
- If user is canceling: {{"intent": "CANCEL"}}
- If user is confirming: {{"intent": "CONFIRM"}}
- If user mentions scheduling, meeting, or time-related words: {{"intent": "SCHEDULE"}}

Examples:
Input: "from 9:00 AM to 5:00 PM"
Output: {{"time": "09:00", "duration": 480}}

Input: "schedule a meeting next week"
Output: {{"intent": "SCHEDULE", "date": "MISSING", "time": "MISSING"}}

Input: "30 minute meeting with John tomorrow at 2 PM"
Output: {{"intent": "SCHEDULE", "name": "John", "date": "{tomorrow.strftime('%Y-%m-%d')}", "time": "14:00", "duration": 30}}

Respond ONLY in valid JSON format:
{{
  "intent": "SCHEDULE" or "OUT_OF_SCOPE" or "CANCEL" or "CONFIRM",
  "name": "person's name or MISSING",
  "date": "YYYY-MM-DD or MISSING",
  "time": "HH:MM or MISSING or AMBIGUOUS:context",
  "duration": number or null,
  "title": "meeting title or MISSING"
}}
"""

def extract_meeting_details(conversation: str, conversation_history: list = None, current_data: dict = None) -> Dict[str, Any]:
    """Extract meeting details with conversation context and correction handling"""
    
    # Detect cancellation intent FIRST
    conversation_lower = conversation.lower()
    cancellation_keywords = ['cancel', 'delete', 'remove', 'cancel this', 'cancel that', 'delete this', 
                            'never mind', 'forget it', 'don\'t schedule', 'no thanks']
    is_cancellation = any(keyword in conversation_lower for keyword in cancellation_keywords)
    
    if is_cancellation:
        return {
            "cancelled": True,
            "message": "Okay, I've cancelled that. The meeting won't be scheduled. Is there anything else you'd like to schedule?",
            "reset": True
        }
    
    # Simple keyword detection to prevent false OUT_OF_SCOPE
    scheduling_keywords = ['schedule', 'meeting', 'book', 'appointment', 'tomorrow', 'today', 
                          'next week', 'friday', 'monday', 'tuesday', 'wednesday', 'thursday',
                          'time', 'pm', 'am', 'with', 'for']
    has_scheduling_context = any(keyword in conversation_lower for keyword in scheduling_keywords)
    
    # Build conversation context
    messages = [{"role": "system", "content": get_system_prompt()}]
    
    if conversation_history:
        for i, msg in enumerate(conversation_history):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": msg})
    
    messages.append({"role": "user", "content": conversation})
    
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
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": "I'm having trouble connecting to my AI service. Please try again in a moment."
        }

    content = response.json()["choices"][0]["message"]["content"]
    import json
    extracted_data = json.loads(content)
    
    # Handle special intents
    intent = extracted_data.get("intent", "SCHEDULE")
    
    # Override OUT_OF_SCOPE if we have scheduling context
    if intent == "OUT_OF_SCOPE" and (has_scheduling_context or current_data):
        intent = "SCHEDULE"
        extracted_data["intent"] = "SCHEDULE"
    
    if intent == "OUT_OF_SCOPE":
        return {
            "out_of_scope": True,
            "message": "I can only help with scheduling meetings. Is there a meeting you'd like to schedule?"
        }
    
    if intent == "CANCEL":
        return {
            "cancelled": True,
            "message": "Okay, I won't schedule it. Let me know if you want to schedule something else.",
            "reset": True
        }
    
    if intent == "CONFIRM":
        # Only allow confirmation if we have all required data
        if current_data and all(current_data.get(field) not in [None, "MISSING", ""] for field in ["name", "date", "time"]):
            return {
                "confirmed": True,
                "current_data": current_data
            }
        else:
            return {
                "incomplete": True,
                "missing_fields": ["time", "date", "name"],
                "extracted_data": current_data or {},
                "follow_up_question": "I still need more information before I can schedule. Who is the meeting with, when, and what time?"
            }
    
    # Merge with current data, prioritizing new values (correction/override)
    if current_data:
        merged_data = current_data.copy()
        for key in ["name", "date", "time", "duration", "title"]:
            new_value = extracted_data.get(key)
            if new_value and new_value != "MISSING" and new_value != "":
                merged_data[key] = new_value
        extracted_data = merged_data
    
    # Handle ambiguous time
    time_value = extracted_data.get("time", "MISSING")
    if time_value and isinstance(time_value, str) and time_value.startswith("AMBIGUOUS:"):
        context = time_value.split(":")[1]
        suggestions = {
            "evening": "6:00 PM",
            "noon": "12:00 PM",
            "morning": "9:00 AM",
            "afternoon": "2:00 PM"
        }
        suggested_time = suggestions.get(context, "6:00 PM")
        return {
            "ambiguous_time": True,
            "context": context,
            "extracted_data": extracted_data,
            "message": f"By {context}, do you mean around {suggested_time}? Or would you prefer a different time?"
        }
    
    # Check for missing information
    missing_fields = []
    if not extracted_data.get("name") or extracted_data.get("name") == "MISSING":
        missing_fields.append("name")
    if not extracted_data.get("date") or extracted_data.get("date") == "MISSING":
        missing_fields.append("date")
    if not extracted_data.get("time") or extracted_data.get("time") == "MISSING":
        missing_fields.append("time")
    
    # Handle duration (optional)
    duration = extracted_data.get("duration")
    if duration is None or duration == "MISSING" or duration == "":
        extracted_data["duration"] = None
    else:
        try:
            extracted_data["duration"] = int(duration)
        except (ValueError, TypeError):
            extracted_data["duration"] = None
    
    # Handle title (optional)
    if not extracted_data.get("title") or extracted_data.get("title") == "MISSING":
        extracted_data["title"] = "Meeting"
    
    if missing_fields:
        return {
            "incomplete": True,
            "missing_fields": missing_fields,
            "extracted_data": extracted_data,
            "follow_up_question": generate_follow_up_question(missing_fields, extracted_data)
        }
    
    # All required fields present, create meeting
    try:
        meeting = MeetingRequest(
            name=extracted_data["name"],
            date=extracted_data["date"],
            time=extracted_data["time"],
            duration=extracted_data["duration"],
            title=extracted_data.get("title", "Meeting")
        )
    except Exception as e:
        return {
            "error": True,
            "message": f"I couldn't process that information. Please try again with the format: 'Schedule a meeting with [name] on [date] at [time]'"
        }
    
    # Generate confirmation message
    confirmation_msg = generate_confirmation_message(meeting)
    
    return {
        "incomplete": False,
        "awaiting_confirmation": True,
        "meeting": meeting,
        "extracted_data": extracted_data,
        "confirmation_message": confirmation_msg
    }

def generate_confirmation_message(meeting: MeetingRequest) -> str:
    """Generate confirmation message with start and end time"""
    try:
        # Parse start time
        start_time = datetime.strptime(meeting.time, "%H:%M")
        
        # Format date nicely
        date_obj = datetime.strptime(meeting.date, "%Y-%m-%d")
        today = datetime.now().date()
        
        if date_obj.date() == today:
            date_str = "today"
        elif date_obj.date() == today + timedelta(days=1):
            date_str = "tomorrow"
        else:
            date_str = f"on {date_obj.strftime('%B %d, %Y')}"
        
        start_str = start_time.strftime("%I:%M %p").lstrip('0').replace(' 0', ' ')
        
        # If duration is provided, show end time
        if meeting.duration:
            end_time = start_time + timedelta(minutes=meeting.duration)
            end_str = end_time.strftime("%I:%M %p").lstrip('0').replace(' 0', ' ')
            return f"I'm about to schedule a {meeting.duration}-minute meeting with {meeting.name} {date_str} from {start_str} to {end_str}. Should I go ahead?"
        else:
            # No duration specified
            return f"I'm about to schedule a meeting with {meeting.name} {date_str} at {start_str}. Should I go ahead?"
    
    except Exception as e:
        return f"I'm about to schedule a meeting with {meeting.name} on {meeting.date} at {meeting.time}. Should I go ahead?"

def generate_success_message(meeting: MeetingRequest) -> str:
    """Generate success message after confirmation"""
    try:
        start_time = datetime.strptime(meeting.time, "%H:%M")
        
        date_obj = datetime.strptime(meeting.date, "%Y-%m-%d")
        today = datetime.now().date()
        
        if date_obj.date() == today:
            date_str = "today"
        elif date_obj.date() == today + timedelta(days=1):
            date_str = "tomorrow"
        else:
            date_str = f"on {date_obj.strftime('%B %d, %Y')}"
        
        start_str = start_time.strftime("%I:%M %p").lstrip('0').replace(' 0', ' ')
        
        if meeting.duration:
            end_time = start_time + timedelta(minutes=meeting.duration)
            end_str = end_time.strftime("%I:%M %p").lstrip('0').replace(' 0', ' ')
            return f"✅ Your {meeting.duration}-minute meeting with {meeting.name} has been scheduled for {date_str} from {start_str} to {end_str}."
        else:
            return f"✅ Your meeting with {meeting.name} has been scheduled for {date_str} at {start_str}."
    
    except Exception as e:
        return f"✅ Your meeting with {meeting.name} has been scheduled for {meeting.date} at {meeting.time}."

def generate_follow_up_question(missing_fields: list, current_data: dict = None) -> str:
    """Generate a natural follow-up question for missing information"""
    
    # Show what we have so far
    known_info = []
    if current_data:
        if current_data.get("name") and current_data.get("name") != "MISSING":
            known_info.append(f"with {current_data['name']}")
        if current_data.get("date") and current_data.get("date") != "MISSING":
            try:
                date_obj = datetime.strptime(current_data['date'], "%Y-%m-%d")
                if date_obj.date() == datetime.now().date():
                    known_info.append("today")
                elif date_obj.date() == (datetime.now() + timedelta(days=1)).date():
                    known_info.append("tomorrow")
                else:
                    known_info.append(f"on {date_obj.strftime('%B %d')}")
            except:
                pass
        if current_data.get("duration"):
            known_info.append(f"for {current_data['duration']} minutes")
    
    context = " ".join(known_info) if known_info else ""
    
    if len(missing_fields) == 3:  # name, date, time all missing
        return "I'd be happy to schedule that meeting. Who is the meeting with, when would you like to schedule it, and what time?"
    elif len(missing_fields) == 2:
        if "name" in missing_fields and "date" in missing_fields:
            return f"Got it{' ' + context if context else ''}! Who is the meeting with and when would you like to schedule it?"
        elif "name" in missing_fields and "time" in missing_fields:
            return f"Sure{' ' + context if context else ''}! Who is the meeting with and what time works best?"
        elif "date" in missing_fields and "time" in missing_fields:
            return f"I can help{' ' + context if context else ''}. When would you like to schedule the meeting (which day) and at what time?"
    else:  # Only one field missing
        if "name" in missing_fields:
            return f"Who is the meeting with{' ' + context if context else ''}?"
        elif "date" in missing_fields:
            return f"When would you like to schedule the meeting{' ' + context if context else ''}? Please specify which day (e.g., Monday, next Tuesday, etc.)."
        elif "time" in missing_fields:
            return f"What time would you prefer{' ' + context if context else ''}?"
    
    return "Could you provide the missing information?"

