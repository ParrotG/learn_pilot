from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assistant_run import AssistantRun
    from app.models.conversation import Conversation
    from app.models.session_note import SessionNote
    from app.models.user import User


class ExportArtifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "export_artifacts"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    note_id: Mapped[str] = mapped_column(
        ForeignKey("session_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assistant_run_id: Mapped[str] = mapped_column(
        ForeignKey("assistant_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_call_id: Mapped[str] = mapped_column(
        ForeignKey("tool_calls.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_format: Mapped[str] = mapped_column(String(50), nullable=False, default="markdown")
    target_format: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    drive_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    drive_folder_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="export_artifacts")
    note: Mapped["SessionNote"] = relationship(back_populates="export_artifacts")
    assistant_run: Mapped["AssistantRun"] = relationship(back_populates="export_artifacts")
    user: Mapped["User"] = relationship(back_populates="export_artifacts")
