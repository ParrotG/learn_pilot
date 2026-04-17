from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, NotFoundError
from app.models.assistant_run import AssistantRun
from app.models.conversation import Conversation
from app.models.conversation_document import ConversationDocument
from app.models.document import Document


class ConversationService:
    async def create_conversation(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        title: str | None = None,
        initial_document_ids: list[str] | None = None,
    ) -> Conversation:
        conversation = Conversation(user_id=user_id, title=(title or "New chat").strip() or "New chat")
        session.add(conversation)
        await session.flush()
        if initial_document_ids:
            result = await session.execute(
                select(Document).where(
                    Document.user_id == user_id,
                    Document.id.in_(initial_document_ids),
                )
            )
            documents = list(result.scalars().all())
            if len(documents) != len(set(initial_document_ids)):
                raise BadRequestError("One or more initial documents could not be attached to the conversation.")
            for document in documents:
                session.add(
                    ConversationDocument(
                        conversation_id=conversation.id,
                        document_id=document.id,
                    )
                )
        await session.commit()
        await session.refresh(conversation)
        return conversation

    async def list_conversations(self, session: AsyncSession, *, user_id: str) -> list[Conversation]:
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_conversation(self, session: AsyncSession, *, user_id: str, conversation_id: str) -> Conversation:
        result = await session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.assistant_runs))
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise NotFoundError("Conversation not found.")
        return conversation

    async def get_latest_run(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
    ) -> AssistantRun | None:
        result = await session.execute(
            select(AssistantRun)
            .where(AssistantRun.user_id == user_id, AssistantRun.conversation_id == conversation_id)
            .order_by(AssistantRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_conversation(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
    ) -> None:
        conversation = await self.get_conversation(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        await session.delete(conversation)
        await session.commit()
