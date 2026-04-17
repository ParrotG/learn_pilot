from __future__ import annotations

import json
from collections.abc import Iterable

from pydantic import BaseModel, ValidationError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import BadRequestError, ExternalServiceError, NotFoundError
from app.integrations.google import build_calendar_resource, build_user_credentials
from app.integrations.openai_client import OpenAIStructuredClient
from app.models.calendar_record import CalendarRecord
from app.models.candidate_event import CandidateEvent
from app.models.enums import CandidateEventStatus
from app.schemas.domain import CandidateEventPayload
from app.services.credential_service import CredentialService

CALENDAR_EXTRACTION_PROMPT = """
Extract schedule-related candidate events from the provided academic document.
Return JSON with a single field:
- events: array of objects with title, start_time, end_time, description, location, source_excerpt

Use ISO 8601 datetimes. If no timezone is given in the source, assume local time and still return a valid datetime string.
Return an empty array when no actionable events are present.
""".strip()


class CandidateEventList(BaseModel):
    events: list[CandidateEventPayload]


class CalendarService:
    def __init__(self, llm_client: OpenAIStructuredClient, credential_service: CredentialService) -> None:
        self.llm_client = llm_client
        self.credential_service = credential_service

    async def extract_and_store_events(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        document_id: str,
        document_text: str,
        api_key: str,
    ) -> tuple[list[CandidateEvent], str]:
        raw_json = await self.llm_client.generate_json(
            api_key=api_key,
            system_prompt=CALENDAR_EXTRACTION_PROMPT,
            user_prompt=f"Document text:\n{document_text[:20000]}",
        )
        try:
            parsed = CandidateEventList.model_validate(json.loads(raw_json))
        except (ValidationError, json.JSONDecodeError) as exc:
            raise ExternalServiceError("The event extraction response could not be validated.", raw_json) from exc

        synced_signatures = await self._get_synced_signatures(session, document_id=document_id)
        await session.execute(
            delete(CandidateEvent).where(
                CandidateEvent.document_id == document_id,
                CandidateEvent.status != CandidateEventStatus.SYNCED.value,
            )
        )

        events: list[CandidateEvent] = []
        for item in parsed.events:
            signature = self._signature(item.title, item.start_time.isoformat(), item.end_time.isoformat() if item.end_time else None)
            if signature in synced_signatures:
                continue
            event = CandidateEvent(
                user_id=user_id,
                document_id=document_id,
                title=item.title,
                start_time=item.start_time,
                end_time=item.end_time,
                description=item.description,
                location=item.location,
                source_excerpt=item.source_excerpt,
                status=CandidateEventStatus.PENDING.value,
            )
            session.add(event)
            events.append(event)
        await session.flush()
        return events, raw_json

    async def create_calendar_events(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        candidate_event_ids: Iterable[str],
        settings: Settings,
    ) -> list[CalendarRecord]:
        ids = list(candidate_event_ids)
        if not ids:
            raise BadRequestError("At least one candidate event ID must be provided.")

        result = await session.execute(
            select(CandidateEvent).where(
                CandidateEvent.user_id == user_id, CandidateEvent.id.in_(ids)
            )
        )
        events = list(result.scalars().all())
        if len(events) != len(ids):
            raise NotFoundError("One or more candidate events were not found.")

        access_token, refresh_token, expiry = await self.credential_service.get_google_tokens(
            session, user_id=user_id, settings=settings
        )
        credentials = build_user_credentials(
            settings=settings,
            access_token=access_token,
            refresh_token=refresh_token,
            expiry=expiry,
        )
        calendar_service = build_calendar_resource(credentials)

        records: list[CalendarRecord] = []
        for event in events:
            event.status = CandidateEventStatus.APPROVED.value
            body = {
                "summary": event.title,
                "description": event.description,
                "location": event.location,
                "start": {"dateTime": event.start_time.isoformat()},
                "end": {"dateTime": (event.end_time or event.start_time).isoformat()},
            }
            try:
                created = calendar_service.events().insert(calendarId="primary", body=body).execute()
            except Exception as exc:  # pragma: no cover - external client errors vary
                event.status = CandidateEventStatus.FAILED.value
                event.error_message = str(exc)
                continue

            event.status = CandidateEventStatus.SYNCED.value
            event.error_message = None
            record = CalendarRecord(
                user_id=user_id,
                candidate_event_id=event.id,
                google_event_id=created["id"],
            )
            session.add(record)
            records.append(record)

        await session.commit()
        for record in records:
            await session.refresh(record)
        return records

    async def _get_synced_signatures(self, session: AsyncSession, *, document_id: str) -> set[str]:
        result = await session.execute(
            select(CandidateEvent).where(
                CandidateEvent.document_id == document_id,
                CandidateEvent.status == CandidateEventStatus.SYNCED.value,
            )
        )
        return {
            self._signature(event.title, event.start_time.isoformat(), event.end_time.isoformat() if event.end_time else None)
            for event in result.scalars().all()
        }

    def _signature(self, title: str, start_time: str, end_time: str | None) -> str:
        return f"{title}::{start_time}::{end_time or ''}"

