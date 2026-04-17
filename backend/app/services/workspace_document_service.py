from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.models.conversation_document import ConversationDocument
from app.models.document import Document
from app.schemas.document import DocumentListItem
from app.schemas.workspace import ConversationDocumentResponse
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.message_service import MessageService


class WorkspaceDocumentService:
    def __init__(
        self,
        *,
        document_service: DocumentService,
        conversation_service: ConversationService,
        message_service: MessageService,
    ) -> None:
        self.document_service = document_service
        self.conversation_service = conversation_service
        self.message_service = message_service

    async def upload_to_conversation(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        upload,
        settings: Settings,
    ) -> dict[str, object]:
        await self.conversation_service.get_conversation(session, user_id=user_id, conversation_id=conversation_id)
        document = await self.document_service.upload_document(
            session,
            user_id=user_id,
            upload=upload,
            settings=settings,
        )
        system_message = await self.message_service.create_system_message(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
            content=f"Uploaded **{document.filename}** and attached it to this conversation.",
        )
        conversation_document = ConversationDocument(
            conversation_id=conversation_id,
            document_id=document.id,
            attached_by_message_id=system_message.id,
        )
        session.add(conversation_document)
        await session.commit()
        await session.refresh(conversation_document)
        item = await self.get_conversation_document(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
            conversation_document_id=conversation_document.id,
        )
        return {
            "document": DocumentListItem.model_validate(document),
            "conversation_document": self.to_response(item),
            "system_message": self.message_service.to_response(system_message),
        }

    async def list_conversation_documents(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
    ) -> list[ConversationDocument]:
        await self.conversation_service.get_conversation(session, user_id=user_id, conversation_id=conversation_id)
        result = await session.execute(
            select(ConversationDocument)
            .join(ConversationDocument.document)
            .where(
                ConversationDocument.conversation_id == conversation_id,
                Document.user_id == user_id,
            )
            .options(selectinload(ConversationDocument.document))
            .order_by(ConversationDocument.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_conversation_document(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        conversation_document_id: str,
    ) -> ConversationDocument:
        await self.conversation_service.get_conversation(session, user_id=user_id, conversation_id=conversation_id)
        result = await session.execute(
            select(ConversationDocument)
            .where(
                ConversationDocument.id == conversation_document_id,
                ConversationDocument.conversation_id == conversation_id,
            )
            .options(selectinload(ConversationDocument.document))
        )
        return result.scalar_one()

    def to_response(self, item: ConversationDocument) -> ConversationDocumentResponse:
        return ConversationDocumentResponse(
            id=item.id,
            created_at=item.created_at,
            updated_at=item.updated_at,
            conversation_id=item.conversation_id,
            document_id=item.document_id,
            attached_by_message_id=item.attached_by_message_id,
            document=DocumentListItem.model_validate(item.document),
        )
