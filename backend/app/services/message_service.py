from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, NotFoundError
from app.db.base import utcnow
from app.models.conversation_document import ConversationDocument
from app.models.document import Document
from app.models.enums import MessageRole, MessageStatus
from app.models.message import Message
from app.models.message_attachment import MessageAttachment
from app.schemas.message import MessageDocumentReference, MessageResponse
from app.services.conversation_service import ConversationService


class MessageService:
    def __init__(self, conversation_service: ConversationService) -> None:
        self.conversation_service = conversation_service

    async def list_messages(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
    ) -> list[Message]:
        await self.conversation_service.get_conversation(session, user_id=user_id, conversation_id=conversation_id)
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.user_id == user_id)
            .options(selectinload(Message.attachments).selectinload(MessageAttachment.document))
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def create_user_message(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        content: str,
        attachment_document_ids: Sequence[str],
    ) -> Message:
        conversation = await self.conversation_service.get_conversation(
            session, user_id=user_id, conversation_id=conversation_id
        )
        attached_documents = await self._resolve_conversation_documents(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
            document_ids=attachment_document_ids,
        )
        message = Message(
            conversation_id=conversation.id,
            user_id=user_id,
            role=MessageRole.USER.value,
            content_markdown=content.strip(),
            status=MessageStatus.COMPLETE.value,
        )
        session.add(message)
        await session.flush()

        for document in attached_documents:
            session.add(MessageAttachment(message_id=message.id, document_id=document.id))

        conversation.last_message_at = utcnow()
        if conversation.title == "New chat":
            conversation.title = self._derive_title(content)
        await session.commit()

        refreshed = await self.get_message(session, user_id=user_id, conversation_id=conversation_id, message_id=message.id)
        return refreshed

    async def create_system_message(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        content: str,
    ) -> Message:
        conversation = await self.conversation_service.get_conversation(
            session, user_id=user_id, conversation_id=conversation_id
        )
        message = Message(
            conversation_id=conversation.id,
            user_id=user_id,
            role=MessageRole.SYSTEM.value,
            content_markdown=content,
            status=MessageStatus.COMPLETE.value,
        )
        session.add(message)
        conversation.last_message_at = utcnow()
        await session.commit()
        return await self.get_message(session, user_id=user_id, conversation_id=conversation_id, message_id=message.id)

    async def create_assistant_message(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        content: str,
        status: str = MessageStatus.COMPLETE.value,
    ) -> Message:
        conversation = await self.conversation_service.get_conversation(
            session, user_id=user_id, conversation_id=conversation_id
        )
        message = Message(
            conversation_id=conversation.id,
            user_id=user_id,
            role=MessageRole.ASSISTANT.value,
            content_markdown=content,
            status=status,
        )
        session.add(message)
        conversation.last_message_at = utcnow()
        await session.commit()
        return await self.get_message(session, user_id=user_id, conversation_id=conversation_id, message_id=message.id)

    async def get_message(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        message_id: str,
    ) -> Message:
        result = await session.execute(
            select(Message)
            .where(
                Message.id == message_id,
                Message.user_id == user_id,
                Message.conversation_id == conversation_id,
            )
            .options(selectinload(Message.attachments).selectinload(MessageAttachment.document))
        )
        message = result.scalar_one_or_none()
        if message is None:
            raise NotFoundError("Message not found.")
        return message

    async def get_latest_user_message(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
    ) -> Message:
        result = await session.execute(
            select(Message)
            .where(
                Message.user_id == user_id,
                Message.conversation_id == conversation_id,
                Message.role == MessageRole.USER.value,
            )
            .order_by(Message.created_at.desc())
            .options(selectinload(Message.attachments).selectinload(MessageAttachment.document))
            .limit(1)
        )
        message = result.scalar_one_or_none()
        if message is None:
            raise NotFoundError("No user message was found for this conversation.")
        return message

    async def _resolve_conversation_documents(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        document_ids: Sequence[str],
    ) -> list[Document]:
        if not document_ids:
            return []

        result = await session.execute(
            select(Document)
            .join(ConversationDocument, ConversationDocument.document_id == Document.id)
            .where(
                Document.user_id == user_id,
                ConversationDocument.conversation_id == conversation_id,
                Document.id.in_(document_ids),
            )
        )
        documents = list(result.scalars().all())
        if len(documents) != len(set(document_ids)):
            raise BadRequestError("One or more attached documents do not belong to this conversation.")
        return documents

    def _derive_title(self, content: str) -> str:
        words = content.strip().split()
        derived = " ".join(words[:6]).strip()
        return derived[:255] if derived else "New chat"

    def to_response(self, message: Message) -> MessageResponse:
        return MessageResponse(
            id=message.id,
            created_at=message.created_at,
            updated_at=message.updated_at,
            conversation_id=message.conversation_id,
            user_id=message.user_id,
            role=message.role,
            content_markdown=message.content_markdown,
            status=message.status,
            attachments=[
                MessageDocumentReference(
                    id=attachment.document.id,
                    filename=attachment.document.filename,
                    processing_status=attachment.document.processing_status,
                )
                for attachment in message.attachments
                if attachment.document is not None
            ],
        )
