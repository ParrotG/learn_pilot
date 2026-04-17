# ruff: noqa: E402

from __future__ import annotations

import sys
from pathlib import Path

import fitz
import pytest_asyncio
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import configure_database, dispose_database, get_engine, get_session_factory
from app.main import create_app


def build_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


@pytest_asyncio.fixture
async def test_settings(tmp_path: Path) -> Settings:
    database_path = tmp_path / "test.db"
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{database_path}",
        jwt_secret_key="test-secret",
        google_oauth_state_secret="test-google-state",
        app_encryption_key=Fernet.generate_key().decode("utf-8"),
        upload_dir=str(tmp_path / "uploads"),
    )
    configure_database(settings.database_url)
    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield settings
    await dispose_database()


@pytest_asyncio.fixture
async def app(test_settings: Settings):
    application = create_app(test_settings)
    application.dependency_overrides[get_settings] = lambda: test_settings
    return application


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    register_payload = {
        "email": "student@example.com",
        "password": "VerySecure123",
        "full_name": "Test Student",
    }
    await client.post("/api/auth/register", json=register_payload)
    response = await client.post(
        "/api/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
