from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AssistantAction


class IntentResult(BaseModel):
    actions: list[AssistantAction]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str


class GeneratedNote(BaseModel):
    summary: str
    key_points: list[str]
    action_items: list[str]


class CandidateEventPayload(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime | None = None
    description: str | None = None
    location: str | None = None
    source_excerpt: str | None = None

