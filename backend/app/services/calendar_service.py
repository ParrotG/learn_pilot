from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import UTC, datetime

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

_DATE_FORMATS_WITH_YEAR = (
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d %b %Y %H:%M",
    "%d %B %Y %H:%M",
    "%b %d %Y %H:%M",
    "%B %d %Y %H:%M",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d %Y",
    "%B %d %Y",
)
_DATE_FORMATS_WITHOUT_YEAR = (
    "%m-%d %H:%M",
    "%m/%d %H:%M",
    "%m-%d",
    "%m/%d",
    "%d %b %H:%M",
    "%d %B %H:%M",
    "%b %d %H:%M",
    "%B %d %H:%M",
    "%d %b",
    "%d %B",
    "%b %d",
    "%B %d",
)


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
            signature = self._signature(
                item.title,
                item.start_time.isoformat(),
                item.end_time.isoformat() if item.end_time else None,
            )
            if signature in synced_signatures:
                continue
            event = CandidateEvent(
                user_id=user_id,
                document_id=document_id,
                source_document_id=document_id,
                title=item.title,
                start_time=item.start_time,
                end_time=item.end_time,
                description=item.description,
                location=item.location,
                source_excerpt=item.source_excerpt,
                normalized_year_defaulted=False,
                status=CandidateEventStatus.PENDING.value,
            )
            session.add(event)
            events.append(event)
        await session.flush()
        return events, raw_json

    async def create_pending_events_for_tool_call(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        tool_call_id: str,
        source_message_id: str,
        events_payload: list[dict[str, object]],
    ) -> list[CandidateEvent]:
        created: list[CandidateEvent] = []
        for raw_event in events_payload:
            normalized_start, start_year_defaulted = self.normalize_datetime(
                str(raw_event["start_text"]),
                default_year=datetime.now(UTC).year,
            )
            normalized_end = None
            end_year_defaulted = False
            if raw_event.get("end_text"):
                normalized_end, end_year_defaulted = self.normalize_datetime(
                    str(raw_event["end_text"]),
                    default_year=normalized_start.year,
                )
            source_document_id = raw_event.get("source_document_id")
            event = CandidateEvent(
                user_id=user_id,
                conversation_id=conversation_id,
                tool_call_id=tool_call_id,
                source_message_id=source_message_id,
                source_document_id=str(source_document_id) if source_document_id else None,
                document_id=str(source_document_id) if source_document_id else None,
                title=str(raw_event["title"]).strip(),
                start_time=normalized_start,
                end_time=normalized_end,
                description=self._optional_str(raw_event.get("description")),
                location=self._optional_str(raw_event.get("location")),
                source_excerpt=self._optional_str(raw_event.get("source_excerpt")),
                normalized_year_defaulted=start_year_defaulted or end_year_defaulted,
                status=CandidateEventStatus.PENDING.value,
            )
            session.add(event)
            created.append(event)
        await session.flush()
        return created

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
                CandidateEvent.user_id == user_id,
                CandidateEvent.id.in_(ids),
            )
        )
        events = list(result.scalars().all())
        if len(events) != len(ids):
            raise NotFoundError("One or more candidate events were not found.")

        access_token, refresh_token, expiry = await self.credential_service.get_google_tokens(
            session,
            user_id=user_id,
            settings=settings,
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
            body = self._build_calendar_event_body(event)
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

        if not records and events:
            first_error = next((event.error_message for event in events if event.error_message), None)
            raise ExternalServiceError(
                "Google Calendar rejected the event creation request.",
                details=first_error or "No calendar records were created.",
            )

        await session.flush()
        return records

    async def reject_calendar_events(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        candidate_event_ids: Iterable[str],
    ) -> list[CandidateEvent]:
        ids = list(candidate_event_ids)
        if not ids:
            return []
        result = await session.execute(
            select(CandidateEvent).where(
                CandidateEvent.user_id == user_id,
                CandidateEvent.id.in_(ids),
            )
        )
        events = list(result.scalars().all())
        for event in events:
            event.status = CandidateEventStatus.REJECTED.value
            event.error_message = None
        await session.flush()
        return events

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

    def normalize_datetime(self, value: str, *, default_year: int) -> tuple[datetime, bool]:
        text = value.strip()
        if not text:
            raise BadRequestError("Event date text cannot be empty.")
        normalized_text = self._normalize_date_text(text)

        try:
            parsed = datetime.fromisoformat(normalized_text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed, False
        except ValueError:
            pass

        for fmt in _DATE_FORMATS_WITH_YEAR:
            try:
                parsed = datetime.strptime(normalized_text, fmt).replace(tzinfo=UTC)
                return parsed, False
            except ValueError:
                continue

        for fmt in _DATE_FORMATS_WITHOUT_YEAR:
            try:
                parsed = datetime.strptime(normalized_text, fmt).replace(year=default_year, tzinfo=UTC)
                return parsed, True
            except ValueError:
                continue

        month_day_match = re.fullmatch(r"(?P<month>\d{1,2})-(?P<day>\d{1,2})", normalized_text)
        if month_day_match:
            parsed = datetime(
                default_year,
                int(month_day_match.group("month")),
                int(month_day_match.group("day")),
                tzinfo=UTC,
            )
            return parsed, True

        raise BadRequestError(f"Could not parse event date text: {value}")

    def _signature(self, title: str, start_time: str, end_time: str | None) -> str:
        return f"{title}::{start_time}::{end_time or ''}"

    def _optional_str(self, value: object | None) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _normalize_date_text(self, value: str) -> str:
        text = value.strip()
        text = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*,\s*", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _build_calendar_event_body(self, event: CandidateEvent) -> dict[str, object]:
        start_time = self._ensure_utc(event.start_time)
        end_time = self._ensure_utc(event.end_time or event.start_time)
        return {
            "summary": event.title,
            "description": event.description,
            "location": event.location,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
        }

    def _ensure_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
