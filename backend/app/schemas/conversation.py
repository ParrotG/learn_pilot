from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel
from app.schemas.run import AssistantRunResponse
from app.schemas.session_note import SessionNoteSummary
from app.schemas.tool_call import ToolCallResponse


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    initial_document_ids: list[str] = Field(default_factory=list)


class ConversationResponse(TimestampedModel):
    user_id: str
    title: str
    status: str
    last_message_at: datetime | None


class ConversationDetailResponse(ConversationResponse):
    latest_run: AssistantRunResponse | None = None
    latest_note: SessionNoteSummary | None = None
    pending_tool_call: ToolCallResponse | None = None
