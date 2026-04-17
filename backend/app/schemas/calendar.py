from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class ExtractEventsRequest(BaseModel):
    document_id: str


class CreateCalendarEventsRequest(BaseModel):
    candidate_event_ids: list[str]


class CandidateEventResponse(TimestampedModel):
    user_id: str
    document_id: str | None
    conversation_id: str | None
    tool_call_id: str | None
    source_message_id: str | None
    source_document_id: str | None
    title: str
    start_time: datetime
    end_time: datetime | None
    description: str | None
    location: str | None
    source_excerpt: str | None
    normalized_year_defaulted: bool
    status: str
    error_message: str | None


class CalendarRecordResponse(TimestampedModel):
    user_id: str
    candidate_event_id: str
    google_event_id: str
