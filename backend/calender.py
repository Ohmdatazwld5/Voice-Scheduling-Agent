from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def create_event(credentials, meeting):
    service = build("calendar", "v3", credentials=credentials)

    start = datetime.fromisoformat(f"{meeting.date}T{meeting.time}")
    end = start + timedelta(minutes=30)

    event = {
        "summary": meeting.title,
        "description": f"Scheduled with {meeting.name}",
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
    }

    return service.events().insert(calendarId="primary", body=event).execute()
