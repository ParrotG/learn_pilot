from __future__ import annotations

from enum import StrEnum


class LLMProvider(StrEnum):
    OPENAI = "openai"


class AssistantAction(StrEnum):
    SUMMARIZE = "summarize"
    EXTRACT_KEY_POINTS = "extract_key_points"
    EXTRACT_SCHEDULE_EVENTS = "extract_schedule_events"
    ARCHIVE_FILE = "archive_file"
    SAVE_NOTES = "save_notes"


class DocumentProcessingStatus(StrEnum):
    UPLOADED = "uploaded"
    ANALYZED = "analyzed"
    ANALYSIS_FAILED = "analysis_failed"
    ARCHIVED = "archived"


class CandidateEventStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SYNCED = "synced"
    FAILED = "failed"


class AnalysisRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageStatus(StrEnum):
    COMPLETE = "complete"
    ERROR = "error"


class AssistantRunExecutionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolCallStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportArtifactStatus(StrEnum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    UPLOADED = "uploaded"
