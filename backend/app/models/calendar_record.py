from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.candidate_event import CandidateEvent
    from app.models.user import User


class CalendarRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calendar_records"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_event_id: Mapped[str] = mapped_column(
        ForeignKey("candidate_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    google_event_id: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped["User"] = relationship(back_populates="calendar_records")
    candidate_event: Mapped["CandidateEvent"] = relationship(back_populates="calendar_records")

