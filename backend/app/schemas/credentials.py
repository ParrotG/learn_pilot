from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LLMCredentialUpsertRequest(BaseModel):
    provider: str = Field(default="openai", max_length=50)
    api_key: str = Field(min_length=10, max_length=500)


class CredentialStatusResponse(BaseModel):
    llm_configured: bool
    llm_provider: str | None
    google_connected: bool
    google_account_email: str | None
    google_token_expiry: datetime | None


class GoogleConnectResponse(BaseModel):
    authorization_url: str


class GoogleCallbackResponse(BaseModel):
    google_connected: bool
    google_account_email: str | None

