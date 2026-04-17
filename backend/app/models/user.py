from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.assistant_run import AssistantRun
    from app.models.calendar_record import CalendarRecord
    from app.models.candidate_event import CandidateEvent
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.export_artifact import ExportArtifact
    from app.models.message import Message
    from app.models.note import Note
    from app.models.session_note import SessionNote
    from app.models.tool_approval_decision import ToolApprovalDecision
    from app.models.user_credential import UserCredential


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    credential: Mapped["UserCredential | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    candidate_events: Mapped[list["CandidateEvent"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    calendar_records: Mapped[list["CalendarRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    assistant_runs: Mapped[list["AssistantRun"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    session_notes: Mapped[list["SessionNote"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tool_approval_decisions: Mapped[list["ToolApprovalDecision"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    export_artifacts: Mapped[list["ExportArtifact"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
