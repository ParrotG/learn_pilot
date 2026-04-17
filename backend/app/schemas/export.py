from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedModel
from app.schemas.run import AssistantRunResponse
from app.schemas.tool_call import ToolCallResponse


class ExportArtifactResponse(TimestampedModel):
    conversation_id: str
    note_id: str
    assistant_run_id: str
    tool_call_id: str | None
    user_id: str
    source_format: str
    target_format: str
    filename: str
    storage_path: str
    file_size: int
    status: str
    drive_file_id: str | None
    drive_folder_id: str | None
    error_message: str | None


class ExportRequestCreate(BaseModel):
    target_format: str = Field(pattern="^(docx|pptx)$")
    note_id: str | None = None


class ExportRequestResponse(BaseModel):
    assistant_run: AssistantRunResponse
    tool_call: ToolCallResponse
