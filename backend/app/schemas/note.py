from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class NoteSaveRequest(BaseModel):
    document_id: str
    summary: str
    key_points: list[str]
    action_items: list[str]


class NoteResponse(TimestampedModel):
    user_id: str
    document_id: str
    summary: str
    key_points: list[str]
    action_items: list[str]

