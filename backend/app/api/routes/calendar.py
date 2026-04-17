from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.calendar import (
    CalendarRecordResponse,
    CandidateEventResponse,
    CreateCalendarEventsRequest,
    ExtractEventsRequest,
)
from app.services import build_services
from app.services.document_service import DocumentService

router = APIRouter(prefix="/calendar", tags=["calendar"])
document_service = DocumentService()


@router.post("/extract-events", response_model=list[CandidateEventResponse])
async def extract_events(
    payload: ExtractEventsRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[CandidateEventResponse]:
    services = build_services(settings)
    document = await document_service.get_document(session, user_id=current_user.id, document_id=payload.document_id)
    _, api_key = await services.credential_service.get_decrypted_llm_api_key(
        session, user_id=current_user.id, settings=settings
    )
    events, _ = await services.calendar_service.extract_and_store_events(
        session,
        user_id=current_user.id,
        document_id=document.id,
        document_text=document.extracted_text or "",
        api_key=api_key,
    )
    await session.commit()
    return [CandidateEventResponse.model_validate(event) for event in events]


@router.post("/create-events", response_model=list[CalendarRecordResponse])
async def create_calendar_events(
    payload: CreateCalendarEventsRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[CalendarRecordResponse]:
    services = build_services(settings)
    records = await services.calendar_service.create_calendar_events(
        session,
        user_id=current_user.id,
        candidate_event_ids=payload.candidate_event_ids,
        settings=settings,
    )
    return [CalendarRecordResponse.model_validate(record) for record in records]
