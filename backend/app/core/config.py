from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "LearnPilot"
    app_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./data/learnpilot.db"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    app_encryption_key: str = "replace-with-a-valid-fernet-key"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"
    upload_dir: str = "data/uploads"
    export_dir: str = "data/exports"
    pandoc_binary: str = "pandoc"
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/api/credentials/google/callback"
    google_oauth_state_secret: str = "change-me-google-state"
    google_drive_root_folder_name: str = "LearnPilot"
    google_oauth_scopes: list[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/drive.file",
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
        ]
    )

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def resolved_upload_dir(self) -> Path:
        upload_dir = Path(self.upload_dir)
        if upload_dir.is_absolute():
            return upload_dir
        return self.backend_dir / upload_dir

    @property
    def resolved_export_dir(self) -> Path:
        export_dir = Path(self.export_dir)
        if export_dir.is_absolute():
            return export_dir
        return self.backend_dir / export_dir

    @property
    def sync_database_url(self) -> str:
        if self.database_url.startswith("sqlite+aiosqlite"):
            return self.database_url.replace("sqlite+aiosqlite", "sqlite", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
