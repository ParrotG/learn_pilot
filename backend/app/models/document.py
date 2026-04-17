from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.candidate_event import CandidateEvent
    from app.models.conversation_document import ConversationDocument
    from app.models.message_attachment import MessageAttachment
    from app.models.note import Note
    from app.models.user import User


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded")
    drive_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    drive_folder_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="documents")
    note: Mapped["Note | None"] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )
    candidate_events: Mapped[list["CandidateEvent"]] = relationship(
        foreign_keys="CandidateEvent.document_id",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["ConversationDocument"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    message_attachments: Mapped[list["MessageAttachment"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
