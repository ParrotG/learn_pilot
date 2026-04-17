from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.assistant_run import AssistantRun
    from app.models.session_note import SessionNote


class SessionNoteRevision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "session_note_revisions"

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
    patch_format: Mapped[str] = mapped_column(String(50), nullable=False, default="unified_diff")
    patch_text: Mapped[str] = mapped_column(Text, nullable=False)
    result_markdown: Mapped[str] = mapped_column(Text, nullable=False)

    note: Mapped["SessionNote"] = relationship(back_populates="revisions")
    assistant_run: Mapped["AssistantRun"] = relationship(back_populates="note_revisions")
