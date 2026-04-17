from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.session_note_revision import SessionNoteRevision
    from app.models.user import User


class SessionNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "session_notes"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Study Note")
    current_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")

    conversation: Mapped["Conversation"] = relationship(back_populates="session_note")
    user: Mapped["User"] = relationship(back_populates="session_notes")
    revisions: Mapped[list["SessionNoteRevision"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan",
        order_by="SessionNoteRevision.created_at",
    )
