from __future__ import annotations

import json
from datetime import UTC, datetime

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.errors import ExternalServiceError, NotFoundError
from app.db.session import get_session_factory
from app.models.assistant_run import AssistantRun
from app.models.conversation_document import ConversationDocument
from app.models.document import Document
from app.models.enums import AssistantRunExecutionStatus, ToolCallStatus
from app.models.message import Message
from app.models.message_attachment import MessageAttachment
from app.models.tool_call import ToolCall
from app.services.conversation_service import ConversationService
from app.services.credential_service import CredentialService
from app.services.message_service import MessageService
from app.services.session_note_service import SessionNoteService
from app.services.tool_gateway_service import ToolGatewayService

ASSISTANT_SYSTEM_PROMPT = """
You are LearnPilot, a study assistant for students.

Decide whether to:
1. reply directly in Markdown, or
2. request exactly one tool call.

Available tools:
- patch_note: use when the user wants to create, replace, or substantially revise the session note.
- create_calendar_event: use when the user explicitly wants deadlines, meetings, or study events added to Google Calendar.

Return JSON only with this shape:
{
  "decision_type": "assistant_reply" | "tool_request",
  "assistant_reply": "markdown reply or empty string",
  "tool_request": {
    "tool_name": "patch_note" | "create_calendar_event",
    "arguments": {}
  }
}

Rules:
- Request at most one tool.
- Use assistant_reply for normal Q&A or lightweight guidance.
- For patch_note, arguments must contain title, full_markdown, and change_summary.
- For create_calendar_event, arguments must contain events, where each event includes title and start_text, and may include end_text, description, location, source_excerpt, and source_document_id.
- For create_calendar_event, prefer machine-friendly date strings:
  - `YYYY-MM-DD`
  - `YYYY-MM-DD HH:MM`
  - full ISO 8601 is also allowed
- If the source does not explicitly include a year, use the current_year from the provided context.
- Do not invent a different year when the year is unknown.
- If calendar creation is requested, extract the relevant events from the conversation and attached documents.
""".strip()

FALLBACK_ASSISTANT_SYSTEM_PROMPT = """
You are LearnPilot, a study assistant for students.

Respond in concise, professional Markdown.
Use the conversation history, attached documents, and session note when relevant.
If the available context is partial, state that clearly instead of guessing.
""".strip()

TOOL_RESULT_SYSTEM_PROMPT = """
You are LearnPilot, a study assistant for students.

Write a concise Markdown reply for the user after a tool step has completed or been rejected.
Summarize what happened, what was updated or created, and any important caveats.
Do not expose raw JSON or internal fields.
""".strip()

DOCUMENT_EXCERPT_MAX_CHARS = 12000
DOCUMENT_EXCERPT_HEAD_CHARS = 6000
DOCUMENT_EXCERPT_TAIL_CHARS = 6000
DOCUMENT_EXCERPT_GAP_MARKER = "\n\n[... omitted middle section ...]\n\n"


class ToolRequestPayload(BaseModel):
    tool_name: str
    arguments: dict[str, object] = Field(default_factory=dict)


class AssistantDecisionPayload(BaseModel):
    decision_type: str
    assistant_reply: str = ""
    tool_request: ToolRequestPayload | None = None


class AssistantRuntimeService:
    def __init__(
        self,
        *,
        llm_client,
        credential_service: CredentialService,
        conversation_service: ConversationService,
        message_service: MessageService,
        session_note_service: SessionNoteService,
        tool_gateway_service: ToolGatewayService,
    ) -> None:
        self.llm_client = llm_client
        self.credential_service = credential_service
        self.conversation_service = conversation_service
        self.message_service = message_service
        self.session_note_service = session_note_service
        self.tool_gateway_service = tool_gateway_service

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
            pending_tool_call_id=None,
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
            run = await self._load_run(session, run_id=run_id)
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
                if run.pending_tool_call_id:
                    await self._resume_from_tool_call(session, run=run, api_key=api_key, settings=settings)
                else:
                    await self._start_new_run(session, run=run, api_key=api_key, settings=settings)
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
                run.trace = {"failure_stage": "assistant_runtime"}
                await session.commit()

    async def _start_new_run(
        self,
        session: AsyncSession,
        *,
        run: AssistantRun,
        api_key: str,
        settings: Settings,
    ) -> None:
        runtime_context = await self._build_runtime_context(
            session,
            user_id=run.user_id,
            conversation_id=run.conversation_id,
            message=run.message,
        )
        decision = await self._generate_assistant_decision(api_key=api_key, runtime_context=runtime_context)

        if decision.decision_type == "assistant_reply":
            await self.message_service.create_assistant_message(
                session,
                user_id=run.user_id,
                conversation_id=run.conversation_id,
                content=decision.assistant_reply.strip(),
            )
            run.status = AssistantRunExecutionStatus.COMPLETED.value
            run.error_message = None
            run.trace = {
                "decision_type": decision.decision_type,
                "documents_considered": runtime_context["documents_considered"],
            }
            await session.commit()
            return

        if decision.tool_request is None:
            raise ExternalServiceError("The assistant decision did not include tool request details.")

        tool_name = decision.tool_request.tool_name
        if tool_name == "patch_note":
            tool_call = await self.tool_gateway_service.create_patch_note_tool_call(
                session,
                run=run,
                title=str(decision.tool_request.arguments.get("title", "Study Note")),
                full_markdown=str(decision.tool_request.arguments.get("full_markdown", "")),
                change_summary=str(decision.tool_request.arguments.get("change_summary", "Updated the note.")),
            )
            await session.commit()
            await self.message_service.create_tool_message(
                session,
                user_id=run.user_id,
                conversation_id=run.conversation_id,
                content=f"Updated the session note.\n\n{tool_call.arguments_json['change_summary']}",
            )
            final_reply = await self._generate_post_tool_reply(
                api_key=api_key,
                conversation_id=run.conversation_id,
                user_id=run.user_id,
                tool_result={
                    "tool_name": tool_name,
                    "status": tool_call.status,
                    "change_summary": tool_call.arguments_json["change_summary"],
                },
            )
            await self.message_service.create_assistant_message(
                session,
                user_id=run.user_id,
                conversation_id=run.conversation_id,
                content=final_reply,
            )
            run.status = AssistantRunExecutionStatus.COMPLETED.value
            run.trace = {
                "decision_type": "tool_request",
                "tool_name": tool_name,
                "tool_call_id": tool_call.id,
            }
            run.error_message = None
            await session.commit()
            return

        if tool_name == "create_calendar_event":
            raw_events = decision.tool_request.arguments.get("events")
            if not isinstance(raw_events, list):
                raise ExternalServiceError("The calendar tool request did not include a valid event list.")
            tool_call = await self.tool_gateway_service.create_calendar_tool_call(
                session,
                run=run,
                events_payload=[
                    item for item in raw_events if isinstance(item, dict)
                ],
            )
            run.status = AssistantRunExecutionStatus.WAITING_FOR_APPROVAL.value
            run.pending_tool_call_id = tool_call.id
            run.trace = {
                "decision_type": "tool_request",
                "tool_name": tool_name,
                "tool_call_id": tool_call.id,
                "candidate_event_count": len(tool_call.result_json.get("candidate_event_ids", []))
                if tool_call.result_json
                else 0,
            }
            run.error_message = None
            await session.commit()
            return

        raise ExternalServiceError(f"Unsupported tool requested by assistant: {tool_name}")

    async def _resume_from_tool_call(
        self,
        session: AsyncSession,
        *,
        run: AssistantRun,
        api_key: str,
        settings: Settings,
    ) -> None:
        tool_call = await self.tool_gateway_service.get_tool_call(
            session,
            user_id=run.user_id,
            tool_call_id=run.pending_tool_call_id,
        )
        if tool_call.status == ToolCallStatus.PENDING_APPROVAL.value:
            run.status = AssistantRunExecutionStatus.WAITING_FOR_APPROVAL.value
            await session.commit()
            return

        if tool_call.status == ToolCallStatus.REJECTED.value:
            await self.message_service.create_tool_message(
                session,
                user_id=run.user_id,
                conversation_id=run.conversation_id,
                content="Calendar event creation was rejected by the user.",
            )
            final_reply = await self._generate_post_tool_reply(
                api_key=api_key,
                conversation_id=run.conversation_id,
                user_id=run.user_id,
                tool_result={
                    "tool_name": tool_call.tool_name,
                    "status": tool_call.status,
                    "result": "The user rejected the calendar write request.",
                },
            )
            await self.message_service.create_assistant_message(
                session,
                user_id=run.user_id,
                conversation_id=run.conversation_id,
                content=final_reply,
            )
            run.status = AssistantRunExecutionStatus.COMPLETED.value
            run.pending_tool_call_id = None
            run.trace = {"tool_name": tool_call.tool_name, "tool_status": tool_call.status}
            run.error_message = None
            await session.commit()
            return

        if tool_call.status != ToolCallStatus.APPROVED.value:
            raise ExternalServiceError(f"Cannot resume tool call in state {tool_call.status}.")

        result = await self.tool_gateway_service.execute_approved_tool_call(
            session,
            tool_call=tool_call,
            user_id=run.user_id,
            settings=settings,
        )
        await session.commit()
        await self.message_service.create_tool_message(
            session,
            user_id=run.user_id,
            conversation_id=run.conversation_id,
            content=(
                "Created Google Calendar events.\n\n"
                f"Events created: {len(result.get('calendar_record_ids', []))}"
            ),
        )
        final_reply = await self._generate_post_tool_reply(
            api_key=api_key,
            conversation_id=run.conversation_id,
            user_id=run.user_id,
            tool_result={
                "tool_name": tool_call.tool_name,
                "status": tool_call.status,
                **result,
            },
        )
        await self.message_service.create_assistant_message(
            session,
            user_id=run.user_id,
            conversation_id=run.conversation_id,
            content=final_reply,
        )
        run.status = AssistantRunExecutionStatus.COMPLETED.value
        run.pending_tool_call_id = None
        run.trace = {
            "tool_name": tool_call.tool_name,
            "tool_status": tool_call.status,
            "candidate_event_count": len(tool_call.candidate_events),
        }
        run.error_message = None
        await session.commit()

    async def _load_run(self, session: AsyncSession, *, run_id: str) -> AssistantRun | None:
        result = await session.execute(
            select(AssistantRun)
            .where(AssistantRun.id == run_id)
            .options(
                selectinload(AssistantRun.message)
                .selectinload(Message.attachments)
                .selectinload(MessageAttachment.document),
                selectinload(AssistantRun.conversation),
                selectinload(AssistantRun.tool_calls)
                .selectinload(ToolCall.candidate_events),
            )
        )
        return result.scalar_one_or_none()

    async def _build_runtime_context(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        message: Message,
    ) -> dict[str, object]:
        messages = await self.message_service.list_messages(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        session_note = await self.session_note_service.get_note_for_conversation(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        document_context = await self._build_document_context(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
            message=message,
        )
        return {
            "conversation_messages": self._serialize_messages_for_llm(messages[-12:]),
            "documents_considered": document_context["documents_considered"],
            "documents": document_context["documents"],
            "current_year": datetime.now(UTC).year,
            "current_date": datetime.now(UTC).date().isoformat(),
            "session_note": {
                "title": session_note.title,
                "current_markdown": session_note.current_markdown,
            }
            if session_note
            else None,
        }

    async def _build_document_context(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        message: Message,
    ) -> dict[str, object]:
        attached_documents = [attachment.document for attachment in message.attachments if attachment.document is not None]
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
            excerpt = self._build_document_excerpt(document.extracted_text or "")
            excerpts.append(
                {
                    "id": document.id,
                    "filename": document.filename,
                    "text_length": len(document.extracted_text or ""),
                    "excerpt": excerpt,
                }
            )
        return {
            "documents_considered": [document["filename"] for document in excerpts],
            "documents": excerpts,
        }

    async def _generate_assistant_decision(
        self,
        *,
        api_key: str,
        runtime_context: dict[str, object],
    ) -> AssistantDecisionPayload:
        raw_json = await self.llm_client.generate_json(
            api_key=api_key,
            system_prompt=ASSISTANT_SYSTEM_PROMPT,
            user_prompt=json.dumps(runtime_context, ensure_ascii=False),
        )
        try:
            payload = json.loads(raw_json)
            normalized_payload = self._normalize_assistant_decision_payload(payload)
            return AssistantDecisionPayload.model_validate(normalized_payload)
        except (ValidationError, ValueError, TypeError, json.JSONDecodeError):
            fallback_reply = await self.llm_client.generate_markdown_reply(
                api_key=api_key,
                system_prompt=FALLBACK_ASSISTANT_SYSTEM_PROMPT,
                conversation_messages=runtime_context["conversation_messages"],
                additional_context={
                    "documents_considered": runtime_context["documents_considered"],
                    "documents": runtime_context["documents"],
                    "session_note": runtime_context["session_note"],
                },
            )
            return AssistantDecisionPayload(
                decision_type="assistant_reply",
                assistant_reply=fallback_reply,
                tool_request=None,
            )

    async def _generate_post_tool_reply(
        self,
        *,
        api_key: str,
        conversation_id: str,
        user_id: str,
        tool_result: dict[str, object],
    ) -> str:
        session_factory = get_session_factory()
        async with session_factory() as follow_up_session:
            messages = await self.message_service.list_messages(
                follow_up_session,
                user_id=user_id,
                conversation_id=conversation_id,
            )
        return await self.llm_client.generate_markdown_reply(
            api_key=api_key,
            system_prompt=TOOL_RESULT_SYSTEM_PROMPT,
            conversation_messages=self._serialize_messages_for_llm(messages[-12:]),
            additional_context={"tool_result": tool_result},
        )

    def _serialize_messages_for_llm(self, messages: list[Message]) -> list[dict[str, str]]:
        serialized: list[dict[str, str]] = []
        for message in messages:
            role = message.role
            content = message.content_markdown
            if role == "tool":
                role = "system"
                content = f"Tool update:\n{content}"
            if role not in {"user", "assistant", "system"}:
                continue
            serialized.append({"role": role, "content": content})
        return serialized

    def _normalize_assistant_decision_payload(self, payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            raise ValueError("Assistant decision payload must be a JSON object.")

        raw_tool_request = payload.get("tool_request") or payload.get("tool") or payload.get("function_call")
        if raw_tool_request is None and any(
            key in payload for key in ("tool_name", "arguments", "args", "parameters", "events")
        ):
            raw_tool_request = {
                "tool_name": payload.get("tool_name") or payload.get("name"),
                "arguments": payload.get("arguments") or payload.get("args") or payload.get("parameters") or {},
            }
            if "events" in payload and not raw_tool_request["arguments"]:
                raw_tool_request["arguments"] = {"events": payload.get("events")}

        tool_request = self._normalize_tool_request(raw_tool_request)
        assistant_reply = self._coerce_text(
            payload.get("assistant_reply")
            or payload.get("reply")
            or payload.get("response")
            or payload.get("message")
            or payload.get("content")
        )
        decision_type = self._coerce_text(
            payload.get("decision_type") or payload.get("decision") or payload.get("type")
        ).lower()

        if tool_request is not None and decision_type not in {"assistant_reply", "tool_request"}:
            decision_type = "tool_request"
        elif assistant_reply and decision_type not in {"assistant_reply", "tool_request"}:
            decision_type = "assistant_reply"

        if decision_type == "tool_request" and tool_request is not None:
            return {
                "decision_type": "tool_request",
                "assistant_reply": assistant_reply,
                "tool_request": tool_request,
            }
        if decision_type == "assistant_reply" and assistant_reply:
            return {
                "decision_type": "assistant_reply",
                "assistant_reply": assistant_reply,
                "tool_request": None,
            }
        if tool_request is not None:
            return {
                "decision_type": "tool_request",
                "assistant_reply": assistant_reply,
                "tool_request": tool_request,
            }
        if assistant_reply:
            return {
                "decision_type": "assistant_reply",
                "assistant_reply": assistant_reply,
                "tool_request": None,
            }
        raise ValueError("Assistant decision payload did not contain a usable reply or tool request.")

    def _normalize_tool_request(self, raw_tool_request: object) -> dict[str, object] | None:
        if raw_tool_request is None:
            return None
        if isinstance(raw_tool_request, str):
            try:
                raw_tool_request = json.loads(raw_tool_request)
            except json.JSONDecodeError:
                return None
        if not isinstance(raw_tool_request, dict):
            return None

        tool_name = self._coerce_text(
            raw_tool_request.get("tool_name")
            or raw_tool_request.get("name")
            or raw_tool_request.get("tool")
            or raw_tool_request.get("function_name")
        )
        arguments = (
            raw_tool_request.get("arguments")
            or raw_tool_request.get("args")
            or raw_tool_request.get("parameters")
            or {}
        )
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}

        if not tool_name:
            return None
        return {"tool_name": tool_name, "arguments": arguments}

    def _coerce_text(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            parts: list[str] = []
            for item in value:
                if isinstance(item, str):
                    stripped = item.strip()
                    if stripped:
                        parts.append(stripped)
                elif isinstance(item, dict):
                    text_value = item.get("text")
                    if isinstance(text_value, str) and text_value.strip():
                        parts.append(text_value.strip())
            return "\n".join(parts).strip()
        if isinstance(value, dict):
            for key in ("text", "content", "message"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
        return str(value).strip()

    def _build_document_excerpt(self, text: str) -> str:
        if len(text) <= DOCUMENT_EXCERPT_MAX_CHARS:
            return text
        head = text[:DOCUMENT_EXCERPT_HEAD_CHARS].rstrip()
        tail = text[-DOCUMENT_EXCERPT_TAIL_CHARS :].lstrip()
        return f"{head}{DOCUMENT_EXCERPT_GAP_MARKER}{tail}"
