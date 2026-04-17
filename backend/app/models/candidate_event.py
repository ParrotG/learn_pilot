from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.calendar_record import CalendarRecord
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.message import Message
    from app.models.tool_call import ToolCall
    from app.models.user import User


class CandidateEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_events"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    tool_call_id: Mapped[str | None] = mapped_column(
        ForeignKey("tool_calls.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    source_message_id: Mapped[str | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_year_defaulted: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="candidate_events")
    document: Mapped["Document | None"] = relationship(
        foreign_keys=[document_id],
        back_populates="candidate_events",
    )
    conversation: Mapped["Conversation | None"] = relationship(back_populates="candidate_events")
    tool_call: Mapped["ToolCall | None"] = relationship(back_populates="candidate_events")
    source_message: Mapped["Message | None"] = relationship(
        foreign_keys=[source_message_id],
        back_populates="candidate_events",
    )
    source_document: Mapped["Document | None"] = relationship(foreign_keys=[source_document_id])
    calendar_records: Mapped[list["CalendarRecord"]] = relationship(
        back_populates="candidate_event", cascade="all, delete-orphan"
    )
