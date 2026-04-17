from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_event import CandidateEvent
from app.models.enums import AssistantAction, CandidateEventStatus
from app.models.user_credential import UserCredential
from app.schemas.domain import GeneratedNote, IntentResult
from app.services.calendar_service import CalendarService
from app.services.intent_service import IntentService
from app.services.note_service import NoteService
from tests.conftest import build_pdf_bytes


@pytest.mark.asyncio
async def test_auth_register_login_and_me(client: AsyncClient) -> None:
    register_payload = {
        "email": "student@example.com",
        "password": "VerySecure123",
        "full_name": "Test Student",
    }
    register_response = await client.post("/api/auth/register", json=register_payload)
    assert register_response.status_code == 201
    assert register_response.json()["email"] == register_payload["email"]

    login_response = await client.post(
        "/api/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["full_name"] == register_payload["full_name"]


@pytest.mark.asyncio
async def test_document_upload_rejects_non_pdf(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"


@pytest.mark.asyncio
async def test_analyze_document_requires_llm_credentials(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    pdf_bytes = build_pdf_bytes("Assignment deadline is on 2026-05-01 18:00.")
    upload_response = await client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("assignment.pdf", pdf_bytes, "application/pdf")},
    )
    document_id = upload_response.json()["id"]

    analyze_response = await client.post(
        f"/api/documents/{document_id}/analyze",
        headers=auth_headers,
        json={"requested_actions": ["summarize"]},
    )
    assert analyze_response.status_code == 409
    assert analyze_response.json()["code"] == "external_service_not_configured"


@pytest.mark.asyncio
async def test_upload_and_analyze_document_flow(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_classify_intent(self, *, api_key: str, document_text: str):
        return (
            IntentResult(
                actions=[
                    AssistantAction.SUMMARIZE,
                    AssistantAction.EXTRACT_SCHEDULE_EVENTS,
                    AssistantAction.SAVE_NOTES,
                ],
                confidence=0.99,
                reasoning_summary="The document includes deadlines and study notes.",
            ),
            '{"actions":["summarize","extract_schedule_events","save_notes"],"confidence":0.99,"reasoning_summary":"The document includes deadlines and study notes."}',
        )

    async def fake_generate_note(self, *, api_key: str, document_text: str):
        return (
            GeneratedNote(
                summary="This is a concise study summary.",
                key_points=["Submission is required.", "There is a deadline."],
                action_items=["Prepare the assignment draft.", "Submit before the deadline."],
            ),
            '{"summary":"This is a concise study summary.","key_points":["Submission is required.","There is a deadline."],"action_items":["Prepare the assignment draft.","Submit before the deadline."]}',
        )

    async def fake_extract_and_store_events(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        document_id: str,
        document_text: str,
        api_key: str,
    ):
        event = CandidateEvent(
            user_id=user_id,
            document_id=document_id,
            title="Assignment Deadline",
            start_time=datetime(2026, 5, 1, 18, 0, tzinfo=UTC),
            end_time=datetime(2026, 5, 1, 19, 0, tzinfo=UTC),
            description="Final submission deadline.",
            location=None,
            source_excerpt="Deadline is 2026-05-01 18:00.",
            status=CandidateEventStatus.PENDING.value,
        )
        session.add(event)
        await session.flush()
        return [event], '{"events":[{"title":"Assignment Deadline"}]}'

    monkeypatch.setattr(IntentService, "classify_intent", fake_classify_intent)
    monkeypatch.setattr(NoteService, "generate_note", fake_generate_note)
    monkeypatch.setattr(CalendarService, "extract_and_store_events", fake_extract_and_store_events)

    llm_response = await client.post(
        "/api/credentials/llm",
        headers=auth_headers,
        json={"provider": "openai", "api_key": "sk-test-1234567890"},
    )
    assert llm_response.status_code == 200

    pdf_bytes = build_pdf_bytes("Assignment deadline is on 2026-05-01 18:00.")
    upload_response = await client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("assignment.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]

    analyze_response = await client.post(
        f"/api/documents/{document_id}/analyze",
        headers=auth_headers,
        json={},
    )
    assert analyze_response.status_code == 200
    body = analyze_response.json()
    assert body["note"]["summary"] == "This is a concise study summary."
    assert len(body["candidate_events"]) == 1
    assert body["analysis_run"]["status"] == "completed"

    detail_response = await client.get(f"/api/documents/{document_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["note"]["action_items"] == [
        "Prepare the assignment draft.",
        "Submit before the deadline.",
    ]
    assert detail_body["candidate_events"][0]["title"] == "Assignment Deadline"


@pytest.mark.asyncio
async def test_google_oauth_flow_persists_and_reuses_pkce_verifier(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCredentials:
        def __init__(self) -> None:
            self.token = "google-access-token"
            self.refresh_token = "google-refresh-token"
            self.expiry = datetime(2026, 5, 1, 18, 0, tzinfo=UTC)

    class FakeFlow:
        def __init__(self, state: str | None, code_verifier: str | None = None) -> None:
            self.state = state
            self.code_verifier = code_verifier
            self.credentials = FakeCredentials()

        def authorization_url(self, **kwargs):
            self.code_verifier = self.code_verifier or "pkce-verifier-123"
            return f"https://accounts.google.com/o/oauth2/auth?state={self.state}", self.state

        def fetch_token(self, **kwargs):
            assert kwargs["code"] == "auth-code"
            assert self.code_verifier == "pkce-verifier-123"
            return {"access_token": self.credentials.token}

    def fake_build_google_flow(settings, *, state=None, code_verifier=None):
        return FakeFlow(state=state, code_verifier=code_verifier)

    async def fake_fetch_google_account_email(access_token: str):
        assert access_token == "google-access-token"
        return "student@gmail.com"

    monkeypatch.setattr("app.services.credential_service.build_google_flow", fake_build_google_flow)
    monkeypatch.setattr(
        "app.services.credential_service.fetch_google_account_email",
        fake_fetch_google_account_email,
    )

    connect_response = await client.post("/api/credentials/google/connect", headers=auth_headers)
    assert connect_response.status_code == 200
    authorization_url = connect_response.json()["authorization_url"]
    assert "state=" in authorization_url
    state = authorization_url.split("state=", maxsplit=1)[1]

    credential_result = await db_session.execute(select(UserCredential))
    credential = credential_result.scalar_one()
    assert credential.google_oauth_pending_state == state
    assert credential.google_oauth_code_verifier_encrypted is not None

    callback_response = await client.get(
        "/api/credentials/google/callback",
        params={"state": state, "code": "auth-code"},
    )
    assert callback_response.status_code == 200
    assert callback_response.json()["google_connected"] is True
    assert callback_response.json()["google_account_email"] == "student@gmail.com"

    await db_session.refresh(credential)
    assert credential.google_account_email == "student@gmail.com"
    assert credential.google_oauth_pending_state is None
    assert credential.google_oauth_code_verifier_encrypted is None
