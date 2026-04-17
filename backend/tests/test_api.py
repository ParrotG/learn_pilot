from __future__ import annotations

from datetime import UTC, datetime
import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_record import CalendarRecord
from app.models.candidate_event import CandidateEvent
from app.models.conversation import Conversation
from app.models.enums import AssistantAction, CandidateEventStatus
from app.models.session_note import SessionNote
from app.models.user_credential import UserCredential
from app.integrations.openai_client import OpenAIStructuredClient
from app.schemas.domain import GeneratedNote, IntentResult
from app.services.assistant_runtime_service import AssistantRuntimeService
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

    async def fake_validate_api_key(self, api_key: str) -> None:
        return None

    monkeypatch.setattr(IntentService, "classify_intent", fake_classify_intent)
    monkeypatch.setattr(NoteService, "generate_note", fake_generate_note)
    monkeypatch.setattr(CalendarService, "extract_and_store_events", fake_extract_and_store_events)
    monkeypatch.setattr(OpenAIStructuredClient, "validate_api_key", fake_validate_api_key)

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


@pytest.mark.asyncio
async def test_conversation_message_and_run_flow(
    client: AsyncClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_validate_api_key(self, api_key: str) -> None:
        return None

    async def fake_generate_markdown_reply(
        self,
        *,
        api_key: str,
        system_prompt: str,
        conversation_messages: list[dict[str, str]],
        additional_context: dict[str, object] | None = None,
    ) -> str:
        assert api_key == "sk-test-chat-123"
        assert any(message["role"] == "user" for message in conversation_messages)
        return "## Study Summary\n\n- This is the generated assistant reply."

    async def fake_generate_json(self, *, api_key: str, system_prompt: str, user_prompt: str) -> str:
        assert api_key == "sk-test-chat-123"
        return (
            '{"decision_type":"assistant_reply","assistant_reply":"## Study Summary\\n\\n- This is the generated '
            'assistant reply.","tool_request":null}'
        )

    monkeypatch.setattr(OpenAIStructuredClient, "validate_api_key", fake_validate_api_key)
    monkeypatch.setattr(OpenAIStructuredClient, "generate_json", fake_generate_json)
    monkeypatch.setattr(OpenAIStructuredClient, "generate_markdown_reply", fake_generate_markdown_reply)

    llm_response = await client.post(
        "/api/credentials/llm",
        headers=auth_headers,
        json={"provider": "openai", "api_key": "sk-test-chat-123"},
    )
    assert llm_response.status_code == 200

    conversation_response = await client.post("/api/conversations", headers=auth_headers, json={})
    assert conversation_response.status_code == 200
    conversation_id = conversation_response.json()["id"]

    upload_response = await client.post(
        f"/api/conversations/{conversation_id}/documents",
        headers=auth_headers,
        files={"file": ("syllabus.pdf", build_pdf_bytes("Exam date is 2026-06-01."), "application/pdf")},
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["document"]["id"]

    message_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "Please summarize the attached syllabus."},
    )
    assert message_response.status_code == 200
    run = message_response.json()["assistant_run"]
    assert run is not None
    run_id = run["id"]

    for _ in range(5):
        run_response = await client.get(f"/api/runs/{run_id}", headers=auth_headers)
        assert run_response.status_code == 200
        if run_response.json()["status"] in {"completed", "failed"}:
            break
        await asyncio.sleep(0.05)
    assert run_response.json()["status"] == "completed"

    messages_response = await client.get(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers,
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) >= 3
    assert any(message["role"] == "assistant" for message in messages)
    assert any("Study Summary" in message["content_markdown"] for message in messages if message["role"] == "assistant")

    documents_response = await client.get(
        f"/api/conversations/{conversation_id}/documents",
        headers=auth_headers,
    )
    assert documents_response.status_code == 200
    documents = documents_response.json()
    assert len(documents) == 1
    assert documents[0]["document"]["id"] == document_id


@pytest.mark.asyncio
async def test_chat_patch_note_tool_creates_session_note(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_validate_api_key(self, api_key: str) -> None:
        return None

    async def fake_generate_json(self, *, api_key: str, system_prompt: str, user_prompt: str) -> str:
        return (
            '{"decision_type":"tool_request","assistant_reply":"","tool_request":{"tool_name":"patch_note",'
            '"arguments":{"title":"Exam Prep Note","full_markdown":"# Exam Prep\\n\\n- Review the final chapter.",'
            '"change_summary":"Created a concise exam prep note."}}}'
        )

    async def fake_generate_markdown_reply(
        self,
        *,
        api_key: str,
        system_prompt: str,
        conversation_messages: list[dict[str, str]],
        additional_context: dict[str, object] | None = None,
    ) -> str:
        assert additional_context is not None
        assert additional_context["tool_result"]["tool_name"] == "patch_note"
        return "The session note is ready in the side panel."

    monkeypatch.setattr(OpenAIStructuredClient, "validate_api_key", fake_validate_api_key)
    monkeypatch.setattr(OpenAIStructuredClient, "generate_json", fake_generate_json)
    monkeypatch.setattr(OpenAIStructuredClient, "generate_markdown_reply", fake_generate_markdown_reply)

    llm_response = await client.post(
        "/api/credentials/llm",
        headers=auth_headers,
        json={"provider": "openai", "api_key": "sk-test-note-123"},
    )
    assert llm_response.status_code == 200

    conversation_response = await client.post("/api/conversations", headers=auth_headers, json={})
    conversation_id = conversation_response.json()["id"]

    message_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "Please turn this conversation into an exam prep note."},
    )
    assert message_response.status_code == 200
    run_id = message_response.json()["assistant_run"]["id"]

    for _ in range(5):
        run_response = await client.get(f"/api/runs/{run_id}", headers=auth_headers)
        if run_response.json()["status"] in {"completed", "failed"}:
            break
        await asyncio.sleep(0.05)
    assert run_response.json()["status"] == "completed"

    note_response = await client.get(
        f"/api/conversations/{conversation_id}/note",
        headers=auth_headers,
    )
    assert note_response.status_code == 200
    note = note_response.json()
    assert note["title"] == "Exam Prep Note"
    assert "# Exam Prep" in note["current_markdown"]

    revisions_response = await client.get(f"/api/notes/{note['id']}/revisions", headers=auth_headers)
    assert revisions_response.status_code == 200
    revisions = revisions_response.json()
    assert len(revisions) == 1
    assert "before.md" in revisions[0]["patch_text"]

    messages_response = await client.get(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers,
    )
    messages = messages_response.json()
    assert any(message["role"] == "tool" for message in messages)
    assert any(message["role"] == "assistant" for message in messages)

    note_result = await db_session.execute(select(SessionNote))
    assert note_result.scalar_one().conversation_id == conversation_id


@pytest.mark.asyncio
async def test_chat_calendar_tool_waits_for_approval_and_resumes(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_validate_api_key(self, api_key: str) -> None:
        return None

    async def fake_generate_json(self, *, api_key: str, system_prompt: str, user_prompt: str) -> str:
        return (
            '{"decision_type":"tool_request","assistant_reply":"","tool_request":{"tool_name":"create_calendar_event",'
            '"arguments":{"events":[{"title":"Project Deadline","start_text":"2026-06-01 18:00",'
            '"description":"Final submission deadline.","source_excerpt":"Deadline is 2026-06-01 18:00."}]}}}'
        )

    async def fake_generate_markdown_reply(
        self,
        *,
        api_key: str,
        system_prompt: str,
        conversation_messages: list[dict[str, str]],
        additional_context: dict[str, object] | None = None,
    ) -> str:
        assert additional_context is not None
        return "The requested calendar events have been processed."

    async def fake_create_calendar_events(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        candidate_event_ids: list[str],
        settings,
    ) -> list[CalendarRecord]:
        result = await session.execute(select(CandidateEvent).where(CandidateEvent.id.in_(candidate_event_ids)))
        events = list(result.scalars().all())
        records: list[CalendarRecord] = []
        for event in events:
            event.status = CandidateEventStatus.SYNCED.value
            record = CalendarRecord(
                user_id=user_id,
                candidate_event_id=event.id,
                google_event_id=f"google-{event.id}",
            )
            session.add(record)
            records.append(record)
        await session.flush()
        return records

    monkeypatch.setattr(OpenAIStructuredClient, "validate_api_key", fake_validate_api_key)
    monkeypatch.setattr(OpenAIStructuredClient, "generate_json", fake_generate_json)
    monkeypatch.setattr(OpenAIStructuredClient, "generate_markdown_reply", fake_generate_markdown_reply)
    monkeypatch.setattr(CalendarService, "create_calendar_events", fake_create_calendar_events)

    llm_response = await client.post(
        "/api/credentials/llm",
        headers=auth_headers,
        json={"provider": "openai", "api_key": "sk-test-calendar-123"},
    )
    assert llm_response.status_code == 200

    conversation_response = await client.post("/api/conversations", headers=auth_headers, json={})
    conversation_id = conversation_response.json()["id"]

    message_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "Add all deadlines to my calendar."},
    )
    assert message_response.status_code == 200
    run_id = message_response.json()["assistant_run"]["id"]

    waiting_response = await client.get(f"/api/runs/{run_id}", headers=auth_headers)
    assert waiting_response.status_code == 200
    assert waiting_response.json()["status"] == "waiting_for_approval"
    tool_call_id = waiting_response.json()["pending_tool_call_id"]
    assert tool_call_id is not None

    tool_call_response = await client.get(f"/api/tool-calls/{tool_call_id}", headers=auth_headers)
    assert tool_call_response.status_code == 200
    tool_call = tool_call_response.json()
    assert tool_call["tool_name"] == "create_calendar_event"
    assert len(tool_call["candidate_events"]) == 1

    approve_response = await client.post(
        f"/api/tool-calls/{tool_call_id}/approve",
        headers=auth_headers,
        json={"decision_comment": "Please create them."},
    )
    assert approve_response.status_code == 200

    for _ in range(10):
        run_response = await client.get(f"/api/runs/{run_id}", headers=auth_headers)
        if run_response.json()["status"] in {"completed", "failed"}:
            break
        await asyncio.sleep(0.05)
    assert run_response.json()["status"] == "completed"
    assert run_response.json()["pending_tool_call_id"] is None

    messages_response = await client.get(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers,
    )
    messages = messages_response.json()
    assert any(message["role"] == "tool" for message in messages)
    assert any(message["role"] == "assistant" for message in messages)

    event_result = await db_session.execute(select(CandidateEvent))
    event = event_result.scalar_one()
    assert event.status == CandidateEventStatus.SYNCED.value


@pytest.mark.asyncio
async def test_conversation_run_falls_back_to_markdown_reply_when_decision_json_is_unusable(
    client: AsyncClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_validate_api_key(self, api_key: str) -> None:
        return None

    async def fake_generate_json(self, *, api_key: str, system_prompt: str, user_prompt: str) -> str:
        return '{"unexpected":"payload"}'

    async def fake_generate_markdown_reply(
        self,
        *,
        api_key: str,
        system_prompt: str,
        conversation_messages: list[dict[str, str]],
        additional_context: dict[str, object] | None = None,
    ) -> str:
        assert any(message["role"] == "user" for message in conversation_messages)
        return "Fallback reply from LearnPilot."

    monkeypatch.setattr(OpenAIStructuredClient, "validate_api_key", fake_validate_api_key)
    monkeypatch.setattr(OpenAIStructuredClient, "generate_json", fake_generate_json)
    monkeypatch.setattr(OpenAIStructuredClient, "generate_markdown_reply", fake_generate_markdown_reply)

    llm_response = await client.post(
        "/api/credentials/llm",
        headers=auth_headers,
        json={"provider": "openai", "api_key": "sk-test-fallback-123"},
    )
    assert llm_response.status_code == 200

    conversation_response = await client.post("/api/conversations", headers=auth_headers, json={})
    conversation_id = conversation_response.json()["id"]

    message_response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers,
        json={"content": "Hi there"},
    )
    assert message_response.status_code == 200
    run_id = message_response.json()["assistant_run"]["id"]

    for _ in range(10):
        run_response = await client.get(f"/api/runs/{run_id}", headers=auth_headers)
        if run_response.json()["status"] in {"completed", "failed"}:
            break
        await asyncio.sleep(0.05)

    assert run_response.json()["status"] == "completed"

    messages_response = await client.get(
        f"/api/conversations/{conversation_id}/messages",
        headers=auth_headers,
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert any(
        message["role"] == "assistant" and message["content_markdown"] == "Fallback reply from LearnPilot."
        for message in messages
    )


@pytest.mark.asyncio
async def test_delete_conversation_removes_it_from_the_workspace(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
) -> None:
    conversation_response = await client.post("/api/conversations", headers=auth_headers, json={})
    assert conversation_response.status_code == 200
    conversation_id = conversation_response.json()["id"]

    delete_response = await client.delete(
        f"/api/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    list_response = await client.get("/api/conversations", headers=auth_headers)
    assert list_response.status_code == 200
    assert all(conversation["id"] != conversation_id for conversation in list_response.json())

    conversation_result = await db_session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    assert conversation_result.scalar_one_or_none() is None


def test_calendar_normalize_datetime_accepts_ordinal_month_names() -> None:
    calendar_service = CalendarService(llm_client=None, credential_service=None)

    parsed, year_defaulted = calendar_service.normalize_datetime(
        "April 17th, 2025",
        default_year=2026,
    )

    assert parsed == datetime(2025, 4, 17, tzinfo=UTC)
    assert year_defaulted is False


def test_calendar_normalize_datetime_defaults_missing_year_to_current_year() -> None:
    calendar_service = CalendarService(llm_client=None, credential_service=None)

    parsed, year_defaulted = calendar_service.normalize_datetime(
        "April 17th",
        default_year=2026,
    )

    assert parsed == datetime(2026, 4, 17, tzinfo=UTC)
    assert year_defaulted is True


def test_calendar_event_body_includes_timezone_for_google_api() -> None:
    calendar_service = CalendarService(llm_client=None, credential_service=None)
    event = CandidateEvent(
        user_id="user-1",
        title="Project milestone",
        start_time=datetime(2026, 4, 17, 18, 0),
        end_time=datetime(2026, 4, 17, 19, 0),
        status=CandidateEventStatus.PENDING.value,
    )

    body = calendar_service._build_calendar_event_body(event)

    assert body["start"]["timeZone"] == "UTC"
    assert body["end"]["timeZone"] == "UTC"
    assert body["start"]["dateTime"].endswith("+00:00")
    assert body["end"]["dateTime"].endswith("+00:00")


def test_assistant_runtime_document_excerpt_keeps_document_tail_when_truncated() -> None:
    runtime_service = AssistantRuntimeService(
        llm_client=None,
        credential_service=None,
        conversation_service=None,
        message_service=None,
        session_note_service=None,
        tool_gateway_service=None,
    )
    text = ("A" * 7000) + ("B" * 7000)

    excerpt = runtime_service._build_document_excerpt(text)

    assert len(excerpt) > 12000
    assert "A" * 200 in excerpt
    assert "B" * 200 in excerpt
    assert "[... omitted middle section ...]" in excerpt
