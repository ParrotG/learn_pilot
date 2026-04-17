from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class AssistantRunStartRequest(BaseModel):
    message_id: str | None = None


class AssistantRunResponse(TimestampedModel):
    conversation_id: str
    message_id: str
    user_id: str
    status: str
    trace: dict[str, Any]
    error_message: str | None


class AssistantRunStartResponse(BaseModel):
    assistant_run: AssistantRunResponse

