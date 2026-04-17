from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.calendar import CandidateEventResponse
from app.schemas.common import TimestampedModel


class ToolApprovalRequest(BaseModel):
    decision_comment: str | None = None


class ToolApprovalDecisionResponse(TimestampedModel):
    tool_call_id: str
    decided_by_user_id: str
    decision: str
    comment: str | None


class ToolCallResponse(TimestampedModel):
    assistant_run_id: str
    conversation_id: str
    tool_name: str
    arguments_json: dict[str, Any]
    status: str
    approval_required: bool
    approval_reason: str | None
    result_json: dict[str, Any] | None
    error_message: str | None
    candidate_events: list[CandidateEventResponse]
    approval_decisions: list[ToolApprovalDecisionResponse]


class ToolApprovalResponse(BaseModel):
    tool_call_id: str
    status: str
    assistant_run_id: str
