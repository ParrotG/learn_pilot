from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel
from app.schemas.run import AssistantRunResponse


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationResponse(TimestampedModel):
    user_id: str
    title: str
    status: str
    last_message_at: datetime | None


class ConversationDetailResponse(ConversationResponse):
    latest_run: AssistantRunResponse | None = None
