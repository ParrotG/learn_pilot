from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.export_artifact import ExportArtifact
    from app.models.message import Message
    from app.models.session_note_revision import SessionNoteRevision
    from app.models.tool_call import ToolCall
    from app.models.user import User


class AssistantRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assistant_runs"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[str] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    pending_tool_call_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    trace: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="assistant_runs")
    message: Mapped["Message"] = relationship(back_populates="assistant_runs")
    user: Mapped["User"] = relationship(back_populates="assistant_runs")
    tool_calls: Mapped[list["ToolCall"]] = relationship(
        back_populates="assistant_run",
        cascade="all, delete-orphan",
        order_by="ToolCall.created_at",
    )
    note_revisions: Mapped[list["SessionNoteRevision"]] = relationship(
        back_populates="assistant_run",
        cascade="all, delete-orphan",
    )
    export_artifacts: Mapped[list["ExportArtifact"]] = relationship(
        back_populates="assistant_run",
        cascade="all, delete-orphan",
    )
