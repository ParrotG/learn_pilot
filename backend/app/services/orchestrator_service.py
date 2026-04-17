from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import BadRequestError
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.enums import AnalysisRunStatus, AssistantAction, DocumentProcessingStatus
from app.schemas.document import AnalyzeDocumentRequest
from app.schemas.domain import IntentResult
from app.services.calendar_service import CalendarService
from app.services.credential_service import CredentialService
from app.services.document_service import DocumentService
from app.services.drive_service import DriveService
from app.services.intent_service import IntentService
from app.services.note_service import NoteService


class OrchestratorService:
    def __init__(
        self,
        *,
        credential_service: CredentialService,
        document_service: DocumentService,
        intent_service: IntentService,
        note_service: NoteService,
        calendar_service: CalendarService,
        drive_service: DriveService,
    ) -> None:
        self.credential_service = credential_service
        self.document_service = document_service
        self.intent_service = intent_service
        self.note_service = note_service
        self.calendar_service = calendar_service
        self.drive_service = drive_service

    async def analyze_document(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        document_id: str,
        payload: AnalyzeDocumentRequest,
        settings: Settings,
    ) -> tuple[AnalysisRun, Document]:
        document = await self.document_service.get_document_detail(
            session, user_id=user_id, document_id=document_id
        )
        if not document.extracted_text:
            raise BadRequestError("This document does not contain extractable text.")

        requested_actions = list(payload.requested_actions or [])
        analysis_run = AnalysisRun(
            user_id=user_id,
            document_id=document.id,
            status=AnalysisRunStatus.RUNNING.value,
            requested_actions=[action.value for action in requested_actions],
            completed_actions=[],
            trace={},
        )
        session.add(analysis_run)
        await session.flush()

        raw_outputs: dict[str, str] = {}
        completed_actions: list[str] = []
        trace: dict[str, object] = {}

        try:
            _, api_key = await self.credential_service.get_decrypted_llm_api_key(
                session, user_id=user_id, settings=settings
            )

            if requested_actions:
                intent_result = IntentResult(
                    actions=requested_actions,
                    confidence=1.0,
                    reasoning_summary="Actions were explicitly requested by the user.",
                )
            else:
                intent_result, raw_intent = await self.intent_service.classify_intent(
                    api_key=api_key,
                    document_text=document.extracted_text,
                )
                raw_outputs["intent"] = raw_intent
            trace["intent"] = intent_result.model_dump(mode="json")
            resolved_actions = list(intent_result.actions)
            analysis_run.requested_actions = [action.value for action in resolved_actions]

            should_generate_note = any(
                action in resolved_actions
                for action in (
                    AssistantAction.SUMMARIZE,
                    AssistantAction.EXTRACT_KEY_POINTS,
                    AssistantAction.SAVE_NOTES,
                )
            )
            if should_generate_note:
                note_result, raw_note = await self.note_service.generate_note(
                    api_key=api_key,
                    document_text=document.extracted_text,
                )
                raw_outputs["note"] = raw_note
                trace["note"] = note_result.model_dump(mode="json")
                if payload.save_notes or AssistantAction.SAVE_NOTES in resolved_actions:
                    await self.note_service.save_note(
                        session,
                        user_id=user_id,
                        document_id=document.id,
                        generated_note=note_result,
                    )
                completed_actions.extend(
                    [
                        action.value
                        for action in resolved_actions
                        if action
                        in (
                            AssistantAction.SUMMARIZE,
                            AssistantAction.EXTRACT_KEY_POINTS,
                            AssistantAction.SAVE_NOTES,
                        )
                    ]
                )

            if AssistantAction.EXTRACT_SCHEDULE_EVENTS in resolved_actions:
                events, raw_events = await self.calendar_service.extract_and_store_events(
                    session,
                    user_id=user_id,
                    document_id=document.id,
                    document_text=document.extracted_text,
                    api_key=api_key,
                )
                raw_outputs["events"] = raw_events
                trace["events"] = [event.id for event in events]
                completed_actions.append(AssistantAction.EXTRACT_SCHEDULE_EVENTS.value)

            if payload.archive_to_drive or AssistantAction.ARCHIVE_FILE in resolved_actions:
                archived_document = await self.drive_service.archive_document(
                    session,
                    user_id=user_id,
                    document_id=document.id,
                    settings=settings,
                )
                trace["drive"] = {
                    "drive_file_id": archived_document.drive_file_id,
                    "drive_folder_id": archived_document.drive_folder_id,
                }
                completed_actions.append(AssistantAction.ARCHIVE_FILE.value)

            if document.processing_status != DocumentProcessingStatus.ARCHIVED.value:
                document.processing_status = DocumentProcessingStatus.ANALYZED.value

            analysis_run.status = AnalysisRunStatus.COMPLETED.value
            analysis_run.completed_actions = completed_actions
            analysis_run.raw_llm_output = json.dumps(raw_outputs)
            analysis_run.trace = trace
            await session.commit()
        except Exception as exc:
            document.processing_status = DocumentProcessingStatus.ANALYSIS_FAILED.value
            analysis_run.status = AnalysisRunStatus.FAILED.value
            analysis_run.completed_actions = completed_actions
            analysis_run.raw_llm_output = json.dumps(raw_outputs) if raw_outputs else None
            analysis_run.trace = trace
            analysis_run.error_message = str(exc)
            await session.commit()
            raise

        refreshed_document = await self.document_service.get_document_detail(
            session, user_id=user_id, document_id=document.id
        )
        refreshed_analysis_result = await session.execute(
            select(AnalysisRun).where(AnalysisRun.id == analysis_run.id)
        )
        refreshed_analysis = refreshed_analysis_result.scalar_one()
        return refreshed_analysis, refreshed_document
