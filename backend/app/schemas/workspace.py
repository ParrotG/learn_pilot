from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import TimestampedModel
from app.schemas.document import DocumentListItem
from app.schemas.message import MessageResponse


class ConversationDocumentResponse(TimestampedModel):
    conversation_id: str
    document_id: str
    attached_by_message_id: str | None
    document: DocumentListItem


class ConversationDocumentUploadResponse(BaseModel):
    document: DocumentListItem
    conversation_document: ConversationDocumentResponse
    system_message: MessageResponse
