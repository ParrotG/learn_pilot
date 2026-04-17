from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import Flow

from app.core.config import Settings
from app.core.errors import ExternalConfigurationError, ExternalServiceError

GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def get_google_client_config(settings: Settings) -> dict[str, Any]:
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise ExternalConfigurationError(
            "Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET first."
        )

    return {
        "web": {
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "auth_uri": GOOGLE_AUTH_URI,
            "token_uri": GOOGLE_TOKEN_URI,
        }
    }


def build_google_flow(
    settings: Settings,
    *,
    state: str | None = None,
    code_verifier: str | None = None,
) -> Flow:
    flow = Flow.from_client_config(
        get_google_client_config(settings),
        scopes=settings.google_oauth_scopes,
        state=state,
        code_verifier=code_verifier,
    )
    flow.redirect_uri = settings.google_oauth_redirect_uri
    return flow


def build_user_credentials(
    *,
    settings: Settings,
    access_token: str,
    refresh_token: str | None,
    expiry: datetime | None,
) -> Credentials:
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        scopes=settings.google_oauth_scopes,
        expiry=expiry,
    )


def build_calendar_resource(credentials: Credentials) -> Resource:
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def build_drive_resource(credentials: Credentials) -> Resource:
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


async def fetch_google_account_email(access_token: str) -> str | None:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
    if response.status_code >= 400:
        raise ExternalServiceError(
            "Failed to fetch the Google account profile.",
            details=response.text,
        )
    payload = response.json()
    return payload.get("email")


def ensure_drive_folder(drive_service: Resource, folder_name: str) -> str:
    try:
        result = (
            drive_service.files()
            .list(
                q=f"mimeType = 'application/vnd.google-apps.folder' and trashed = false and name = '{folder_name}'",
                spaces="drive",
                fields="files(id, name)",
                pageSize=1,
            )
            .execute()
        )
        files = result.get("files", [])
        if files:
            return files[0]["id"]

        folder = (
            drive_service.files()
            .create(
                body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"},
                fields="id",
            )
            .execute()
        )
        return folder["id"]
    except Exception as exc:  # pragma: no cover - external client errors vary
        raise ExternalServiceError("Failed to ensure the Google Drive folder.", details=str(exc)) from exc


def upload_file_to_drive(
    drive_service: Resource,
    *,
    folder_id: str,
    filename: str,
    file_path: str,
    mime_type: str,
) -> str:
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=False)
    try:
        file_metadata = {"name": filename, "parents": [folder_id]}
        uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return uploaded["id"]
    except Exception as exc:  # pragma: no cover - external client errors vary
        raise ExternalServiceError("Failed to upload the file to Google Drive.", details=str(exc)) from exc
