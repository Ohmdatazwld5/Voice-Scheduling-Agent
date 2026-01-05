from pydantic import BaseModel
from typing import Optional

class MeetingRequest(BaseModel):
    name: str
    date: str
    time: str
    title: Optional[str] = "Meeting"
    duration: Optional[int] = None  # User can specify duration, no default
