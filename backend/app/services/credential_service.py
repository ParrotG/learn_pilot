from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ExternalConfigurationError, UnauthorizedError
from app.core.security import create_signed_state, decrypt_value, encrypt_value, verify_signed_state
from app.integrations.google import build_google_flow, fetch_google_account_email
from app.models.user_credential import UserCredential
from app.schemas.credentials import (
    CredentialStatusResponse,
    GoogleCallbackResponse,
    GoogleConnectResponse,
    LLMCredentialUpsertRequest,
)


class CredentialService:
    async def get_optional(self, session: AsyncSession, user_id: str) -> UserCredential | None:
        result = await session.execute(select(UserCredential).where(UserCredential.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, session: AsyncSession, user_id: str) -> UserCredential:
        credential = await self.get_optional(session, user_id)
        if credential is None:
            credential = UserCredential(user_id=user_id)
            session.add(credential)
            await session.flush()
        return credential

    async def upsert_llm_credential(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        payload: LLMCredentialUpsertRequest,
        settings: Settings,
    ) -> CredentialStatusResponse:
        credential = await self.get_or_create(session, user_id)
        credential.llm_provider = payload.provider
        credential.llm_api_key_encrypted = encrypt_value(payload.api_key, settings)
        await session.commit()
        await session.refresh(credential)
        return self._to_status(credential)

    async def get_status(self, session: AsyncSession, *, user_id: str) -> CredentialStatusResponse:
        credential = await self.get_optional(session, user_id)
        if credential is None:
            return CredentialStatusResponse(
                llm_configured=False,
                llm_provider=None,
                google_connected=False,
                google_account_email=None,
                google_token_expiry=None,
            )
        return self._to_status(credential)

    async def build_google_connect_response(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        settings: Settings,
    ) -> GoogleConnectResponse:
        credential = await self.get_or_create(session, user_id)
        state = create_signed_state(user_id=user_id, settings=settings)
        flow = build_google_flow(settings, state=state)
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        if not flow.code_verifier:
            raise ExternalConfigurationError("Failed to initialize the Google OAuth PKCE verifier.")
        credential.google_oauth_pending_state = state
        credential.google_oauth_code_verifier_encrypted = encrypt_value(flow.code_verifier, settings)
        await session.commit()
        return GoogleConnectResponse(authorization_url=authorization_url)

    async def handle_google_callback(
        self,
        session: AsyncSession,
        *,
        code: str,
        state: str,
        settings: Settings,
    ) -> GoogleCallbackResponse:
        user_id = verify_signed_state(state, settings)
        credential = await self.get_optional(session, user_id)
        if (
            credential is None
            or credential.google_oauth_pending_state != state
            or not credential.google_oauth_code_verifier_encrypted
        ):
            raise UnauthorizedError("The Google OAuth session is missing or no longer valid. Please reconnect.")

        code_verifier = decrypt_value(credential.google_oauth_code_verifier_encrypted, settings)
        flow = build_google_flow(settings, state=state, code_verifier=code_verifier)
        try:
            flow.fetch_token(code=code)
        except Exception as exc:  # pragma: no cover - external client errors vary
            raise ExternalConfigurationError("Failed to exchange the Google OAuth code.", str(exc)) from exc

        credentials = flow.credentials
        email = await fetch_google_account_email(credentials.token)

        credential.google_access_token_encrypted = encrypt_value(credentials.token, settings)
        credential.google_refresh_token_encrypted = (
            encrypt_value(credentials.refresh_token, settings) if credentials.refresh_token else None
        )
        credential.google_token_expiry = credentials.expiry
        credential.google_account_email = email
        credential.google_oauth_pending_state = None
        credential.google_oauth_code_verifier_encrypted = None
        await session.commit()
        return GoogleCallbackResponse(google_connected=True, google_account_email=email)

    async def get_decrypted_llm_api_key(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        settings: Settings,
    ) -> tuple[str, str]:
        credential = await self.get_optional(session, user_id)
        if credential is None or not credential.llm_api_key_encrypted or not credential.llm_provider:
            raise ExternalConfigurationError("No LLM API key has been configured for this user.")
        return credential.llm_provider, decrypt_value(credential.llm_api_key_encrypted, settings)

    async def get_google_tokens(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        settings: Settings,
    ) -> tuple[str, str | None, datetime | None]:
        credential = await self.get_optional(session, user_id)
        if credential is None or not credential.google_access_token_encrypted:
            raise ExternalConfigurationError("Google OAuth has not been configured for this user.")
        access_token = decrypt_value(credential.google_access_token_encrypted, settings)
        refresh_token = (
            decrypt_value(credential.google_refresh_token_encrypted, settings)
            if credential.google_refresh_token_encrypted
            else None
        )
        return access_token, refresh_token, credential.google_token_expiry

    def _to_status(self, credential: UserCredential) -> CredentialStatusResponse:
        return CredentialStatusResponse(
            llm_configured=bool(credential.llm_api_key_encrypted),
            llm_provider=credential.llm_provider,
            google_connected=bool(credential.google_access_token_encrypted),
            google_account_email=credential.google_account_email,
            google_token_expiry=credential.google_token_expiry,
        )
