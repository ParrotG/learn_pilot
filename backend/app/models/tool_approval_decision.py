from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.tool_call import ToolCall
    from app.models.user import User


class ToolApprovalDecision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tool_approval_decisions"

    tool_call_id: Mapped[str] = mapped_column(
        ForeignKey("tool_calls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decided_by_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    tool_call: Mapped["ToolCall"] = relationship(back_populates="approval_decisions")
    user: Mapped["User"] = relationship(back_populates="tool_approval_decisions")
