from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.message import Message


class ConversationDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversation_documents"
    __table_args__ = (UniqueConstraint("conversation_id", "document_id"),)

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attached_by_message_id: Mapped[str | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="documents")
    document: Mapped["Document"] = relationship(back_populates="conversations")
    attached_by_message: Mapped["Message | None"] = relationship()
