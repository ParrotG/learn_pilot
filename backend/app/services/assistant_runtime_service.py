from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.errors import NotFoundError
from app.db.session import get_session_factory
from app.models.assistant_run import AssistantRun
from app.models.conversation_document import ConversationDocument
from app.models.document import Document
from app.models.enums import AssistantRunExecutionStatus
from app.models.message import Message
from app.models.message_attachment import MessageAttachment
from app.services.conversation_service import ConversationService
from app.services.credential_service import CredentialService
from app.services.message_service import MessageService

ASSISTANT_SYSTEM_PROMPT = """
You are LearnPilot, a study assistant for students.

Respond in concise, professional Markdown.
Use the conversation history and any attached academic documents when relevant.
If document excerpts are provided, ground your answer in them and say when information may be partial.
""".strip()


class AssistantRuntimeService:
    def __init__(
        self,
        *,
        llm_client,
        credential_service: CredentialService,
        conversation_service: ConversationService,
        message_service: MessageService,
    ) -> None:
        self.llm_client = llm_client
        self.credential_service = credential_service
        self.conversation_service = conversation_service
        self.message_service = message_service

    async def create_run(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        message_id: str,
    ) -> AssistantRun:
        await self.conversation_service.get_conversation(session, user_id=user_id, conversation_id=conversation_id)
        message = await self.message_service.get_message(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )
        run = AssistantRun(
            conversation_id=conversation_id,
            message_id=message.id,
            user_id=user_id,
            status=AssistantRunExecutionStatus.QUEUED.value,
            trace={},
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)
        return run

    async def get_run(self, session: AsyncSession, *, user_id: str, run_id: str) -> AssistantRun:
        result = await session.execute(
            select(AssistantRun).where(AssistantRun.id == run_id, AssistantRun.user_id == user_id)
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise NotFoundError("Assistant run not found.")
        return run

    async def process_run(self, run_id: str, settings: Settings) -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            result = await session.execute(
                select(AssistantRun)
                .where(AssistantRun.id == run_id)
                .options(
                    selectinload(AssistantRun.message)
                    .selectinload(Message.attachments)
                    .selectinload(MessageAttachment.document),
                    selectinload(AssistantRun.conversation),
                )
            )
            run = result.scalar_one_or_none()
            if run is None:
                return

            if run.status not in {
                AssistantRunExecutionStatus.QUEUED.value,
                AssistantRunExecutionStatus.RUNNING.value,
            }:
                return

            run.status = AssistantRunExecutionStatus.RUNNING.value
            await session.commit()

            try:
                _, api_key = await self.credential_service.get_decrypted_llm_api_key(
                    session,
                    user_id=run.user_id,
                    settings=settings,
                )
                messages = await self.message_service.list_messages(
                    session,
                    user_id=run.user_id,
                    conversation_id=run.conversation_id,
                )
                context_messages = [
                    {"role": message.role, "content": message.content_markdown}
                    for message in messages[-12:]
                    if message.role in {"user", "assistant", "system"}
                ]
                document_context = await self._build_document_context(
                    session,
                    user_id=run.user_id,
                    conversation_id=run.conversation_id,
                    message=run.message,
                )
                reply = await self.llm_client.generate_markdown_reply(
                    api_key=api_key,
                    system_prompt=ASSISTANT_SYSTEM_PROMPT,
                    conversation_messages=context_messages,
                    additional_context=document_context,
                )
                await self.message_service.create_assistant_message(
                    session,
                    user_id=run.user_id,
                    conversation_id=run.conversation_id,
                    content=reply,
                )
                run.status = AssistantRunExecutionStatus.COMPLETED.value
                run.trace = {
                    "message_count": len(context_messages),
                    "documents_considered": document_context["documents_considered"],
                }
                run.error_message = None
                await session.commit()
            except Exception as exc:
                await self.message_service.create_assistant_message(
                    session,
                    user_id=run.user_id,
                    conversation_id=run.conversation_id,
                    content=(
                        "LearnPilot could not complete this response.\n\n"
                        f"Error: `{str(exc)}`"
                    ),
                    status="error",
                )
                run.status = AssistantRunExecutionStatus.FAILED.value
                run.error_message = str(exc)
                run.trace = {"failure_stage": "assistant_generation"}
                await session.commit()

    async def _build_document_context(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        message: Message,
    ) -> dict[str, object]:
        attached_documents = [attachment.document for attachment in message.attachments]
        if not attached_documents:
            result = await session.execute(
                select(Document)
                .join(ConversationDocument, ConversationDocument.document_id == Document.id)
                .where(
                    ConversationDocument.conversation_id == conversation_id,
                    Document.user_id == user_id,
                )
                .order_by(Document.created_at.desc())
            )
            attached_documents = list(result.scalars().all())[:3]

        excerpts = []
        for document in attached_documents[:3]:
            excerpts.append(
                {
                    "id": document.id,
                    "filename": document.filename,
                    "excerpt": (document.extracted_text or "")[:4000],
                }
            )
        return {
            "documents_considered": [document["filename"] for document in excerpts],
            "documents": excerpts,
        }
