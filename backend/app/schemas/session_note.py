from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class SessionNoteResponse(TimestampedModel):
    conversation_id: str
    user_id: str
    title: str
    current_markdown: str


class SessionNoteRevisionResponse(TimestampedModel):
    note_id: str
    assistant_run_id: str
    patch_format: str
    patch_text: str
    result_markdown: str


class SessionNoteSummary(BaseModel):
    id: str
    conversation_id: str
    title: str
    updated_at: datetime
