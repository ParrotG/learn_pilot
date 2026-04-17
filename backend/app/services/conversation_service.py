from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models.assistant_run import AssistantRun
from app.models.conversation import Conversation


class ConversationService:
    async def create_conversation(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        title: str | None = None,
    ) -> Conversation:
        conversation = Conversation(user_id=user_id, title=(title or "New chat").strip() or "New chat")
        session.add(conversation)
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
