from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assistant_run import AssistantRun
    from app.models.candidate_event import CandidateEvent
    from app.models.conversation import Conversation
    from app.models.tool_approval_decision import ToolApprovalDecision


class ToolCall(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tool_calls"

    assistant_run_id: Mapped[str] = mapped_column(
        ForeignKey("assistant_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending_approval")
    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approval_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    assistant_run: Mapped["AssistantRun"] = relationship(back_populates="tool_calls")
    conversation: Mapped["Conversation"] = relationship(back_populates="tool_calls")
    approval_decisions: Mapped[list["ToolApprovalDecision"]] = relationship(
        back_populates="tool_call",
        cascade="all, delete-orphan",
        order_by="ToolApprovalDecision.created_at",
    )
    candidate_events: Mapped[list["CandidateEvent"]] = relationship(
        back_populates="tool_call",
        cascade="all, delete-orphan",
    )
