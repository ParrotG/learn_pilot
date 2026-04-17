from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, NotFoundError
from app.models.assistant_run import AssistantRun
from app.models.enums import ToolCallStatus
from app.models.tool_approval_decision import ToolApprovalDecision
from app.models.tool_call import ToolCall
from app.schemas.calendar import CandidateEventResponse
from app.schemas.tool_call import ToolApprovalDecisionResponse, ToolCallResponse
from app.services.calendar_service import CalendarService
from app.services.message_service import MessageService
from app.services.session_note_service import SessionNoteService


class ToolGatewayService:
    def __init__(
        self,
        *,
        calendar_service: CalendarService,
        session_note_service: SessionNoteService,
        message_service: MessageService,
    ) -> None:
        self.calendar_service = calendar_service
        self.session_note_service = session_note_service
        self.message_service = message_service

    async def get_tool_call(self, session: AsyncSession, *, user_id: str, tool_call_id: str) -> ToolCall:
        result = await session.execute(
            select(ToolCall)
            .join(ToolCall.conversation)
            .where(ToolCall.id == tool_call_id, ToolCall.conversation.has(user_id=user_id))
            .options(
                selectinload(ToolCall.candidate_events),
                selectinload(ToolCall.approval_decisions),
            )
        )
        tool_call = result.scalar_one_or_none()
        if tool_call is None:
            raise NotFoundError("Tool call not found.")
        return tool_call

    async def get_pending_tool_call_for_conversation(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
    ) -> ToolCall | None:
        result = await session.execute(
            select(ToolCall)
            .where(
                ToolCall.conversation_id == conversation_id,
                ToolCall.conversation.has(user_id=user_id),
                ToolCall.status == ToolCallStatus.PENDING_APPROVAL.value,
            )
            .options(
                selectinload(ToolCall.candidate_events),
                selectinload(ToolCall.approval_decisions),
            )
            .order_by(ToolCall.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_patch_note_tool_call(
        self,
        session: AsyncSession,
        *,
        run: AssistantRun,
        title: str,
        full_markdown: str,
        change_summary: str,
    ) -> ToolCall:
        tool_call = ToolCall(
            assistant_run_id=run.id,
            conversation_id=run.conversation_id,
            tool_name="patch_note",
            arguments_json={
                "title": title,
                "full_markdown": full_markdown,
                "change_summary": change_summary,
            },
            status=ToolCallStatus.RUNNING.value,
            approval_required=False,
        )
        session.add(tool_call)
        await session.flush()

        note, revision = await self.session_note_service.apply_patch(
            session,
            user_id=run.user_id,
            conversation_id=run.conversation_id,
            assistant_run_id=run.id,
            title=title,
            full_markdown=full_markdown,
        )
        tool_call.status = ToolCallStatus.COMPLETED.value
        tool_call.result_json = {
            "note_id": note.id,
            "revision_id": revision.id,
            "change_summary": change_summary,
        }
        await session.flush()
        return tool_call

    async def create_calendar_tool_call(
        self,
        session: AsyncSession,
        *,
        run: AssistantRun,
        events_payload: list[dict[str, object]],
    ) -> ToolCall:
        if not events_payload:
            raise BadRequestError("Calendar tool requests must include at least one event.")

        tool_call = ToolCall(
            assistant_run_id=run.id,
            conversation_id=run.conversation_id,
            tool_name="create_calendar_event",
            arguments_json={"events": events_payload},
            status=ToolCallStatus.PENDING_APPROVAL.value,
            approval_required=True,
            approval_reason="Creating Google Calendar events requires approval.",
        )
        session.add(tool_call)
        await session.flush()

        created_events = await self.calendar_service.create_pending_events_for_tool_call(
            session,
            user_id=run.user_id,
            conversation_id=run.conversation_id,
            tool_call_id=tool_call.id,
            source_message_id=run.message_id,
            events_payload=events_payload,
        )
        tool_call.result_json = {"candidate_event_ids": [event.id for event in created_events]}
        await session.flush()
        return tool_call

    async def approve_tool_call(
        self,
        session: AsyncSession,
        *,
        tool_call: ToolCall,
        user_id: str,
        comment: str | None,
    ) -> ToolApprovalDecision:
        if tool_call.status != ToolCallStatus.PENDING_APPROVAL.value:
            raise BadRequestError("This tool call is no longer awaiting approval.")
        decision = ToolApprovalDecision(
            tool_call_id=tool_call.id,
            decided_by_user_id=user_id,
            decision=ToolCallStatus.APPROVED.value,
            comment=comment,
        )
        session.add(decision)
        tool_call.status = ToolCallStatus.APPROVED.value
        await session.flush()
        return decision

    async def reject_tool_call(
        self,
        session: AsyncSession,
        *,
        tool_call: ToolCall,
        user_id: str,
        comment: str | None,
    ) -> ToolApprovalDecision:
        if tool_call.status != ToolCallStatus.PENDING_APPROVAL.value:
            raise BadRequestError("This tool call is no longer awaiting approval.")
        decision = ToolApprovalDecision(
            tool_call_id=tool_call.id,
            decided_by_user_id=user_id,
            decision=ToolCallStatus.REJECTED.value,
            comment=comment,
        )
        session.add(decision)
        tool_call.status = ToolCallStatus.REJECTED.value
        if tool_call.candidate_events:
            await self.calendar_service.reject_calendar_events(
                session,
                user_id=user_id,
                candidate_event_ids=[event.id for event in tool_call.candidate_events],
            )
        await session.flush()
        return decision

    async def execute_approved_tool_call(
        self,
        session: AsyncSession,
        *,
        tool_call: ToolCall,
        user_id: str,
        settings,
    ) -> dict[str, object]:
        if tool_call.tool_name != "create_calendar_event":
            raise BadRequestError(f"Unsupported approved tool call: {tool_call.tool_name}")
        tool_call.status = ToolCallStatus.RUNNING.value
        await session.flush()

        try:
            records = await self.calendar_service.create_calendar_events(
                session,
                user_id=user_id,
                candidate_event_ids=[event.id for event in tool_call.candidate_events],
                settings=settings,
            )
            tool_call.status = ToolCallStatus.COMPLETED.value
            tool_call.error_message = None
            tool_call.result_json = {
                "candidate_event_ids": [event.id for event in tool_call.candidate_events],
                "calendar_record_ids": [record.id for record in records],
            }
            await session.flush()
            return tool_call.result_json
        except Exception as exc:
            tool_call.status = ToolCallStatus.FAILED.value
            tool_call.error_message = str(exc)
            await session.flush()
            raise

    def to_response(self, tool_call: ToolCall) -> ToolCallResponse:
        return ToolCallResponse(
            id=tool_call.id,
            created_at=tool_call.created_at,
            updated_at=tool_call.updated_at,
            assistant_run_id=tool_call.assistant_run_id,
            conversation_id=tool_call.conversation_id,
            tool_name=tool_call.tool_name,
            arguments_json=tool_call.arguments_json,
            status=tool_call.status,
            approval_required=tool_call.approval_required,
            approval_reason=tool_call.approval_reason,
            result_json=tool_call.result_json,
            error_message=tool_call.error_message,
            candidate_events=[CandidateEventResponse.model_validate(event) for event in tool_call.candidate_events],
            approval_decisions=[
                ToolApprovalDecisionResponse.model_validate(decision) for decision in tool_call.approval_decisions
            ],
        )
