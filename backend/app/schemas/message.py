from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel
from app.schemas.run import AssistantRunResponse


class MessageDocumentReference(BaseModel):
    id: str
    filename: str
    processing_status: str


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    attachment_document_ids: list[str] = Field(default_factory=list)
    auto_create_run: bool = True


class MessageResponse(TimestampedModel):
    conversation_id: str
    user_id: str
    role: str
    content_markdown: str
    status: str
    attachments: list[MessageDocumentReference] = Field(default_factory=list)


class MessageCreateResponse(BaseModel):
    message: MessageResponse
    assistant_run: AssistantRunResponse | None

