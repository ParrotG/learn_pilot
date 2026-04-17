from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_credentials"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_api_key_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    google_access_token_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    google_refresh_token_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    google_token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    google_account_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_oauth_pending_state: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    google_oauth_code_verifier_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship(back_populates="credential")
