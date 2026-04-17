from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.models.enums import AssistantAction
from app.schemas.calendar import CandidateEventResponse
from app.schemas.common import TimestampedModel
from app.schemas.note import NoteResponse


class AnalyzeDocumentRequest(BaseModel):
    requested_actions: list[AssistantAction] | None = None
    archive_to_drive: bool = False
    save_notes: bool = True


class DocumentListItem(TimestampedModel):
    user_id: str
    filename: str
    mime_type: str
    file_size: int
    processing_status: str
    drive_file_id: str | None
    drive_folder_id: str | None


class AnalysisRunResponse(TimestampedModel):
    user_id: str
    document_id: str
    status: str
    requested_actions: list[str]
    completed_actions: list[str]
    raw_llm_output: str | None
    trace: dict[str, Any]
    error_message: str | None


class DocumentDetailResponse(DocumentListItem):
    extracted_text: str | None
    note: NoteResponse | None
    candidate_events: list[CandidateEventResponse]
    analysis_runs: list[AnalysisRunResponse]


class AnalysisSummaryResponse(BaseModel):
    document_id: str
    analysis_run: AnalysisRunResponse
    note: NoteResponse | None
    candidate_events: list[CandidateEventResponse]


class AssistantExecuteRequest(BaseModel):
    document_id: str
    requested_actions: list[AssistantAction] | None = None
    archive_to_drive: bool = False
    save_notes: bool = True
