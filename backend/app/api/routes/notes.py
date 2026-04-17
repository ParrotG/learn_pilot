from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.domain import GeneratedNote
from app.schemas.note import NoteResponse, NoteSaveRequest
from app.schemas.session_note import SessionNoteResponse, SessionNoteRevisionResponse
from app.services import build_services
from app.services.document_service import DocumentService

router = APIRouter(prefix="/notes", tags=["notes"])
document_service = DocumentService()


@router.get("", response_model=list[SessionNoteResponse])
async def list_notes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[SessionNoteResponse]:
    services = build_services(settings)
    notes = await services.session_note_service.list_notes(session, user_id=current_user.id)
    return [services.session_note_service.to_response(note) for note in notes]


@router.get("/{note_id}/revisions", response_model=list[SessionNoteRevisionResponse])
async def list_note_revisions(
    note_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[SessionNoteRevisionResponse]:
    services = build_services(settings)
    revisions = await services.session_note_service.list_revisions(
        session,
        user_id=current_user.id,
        note_id=note_id,
    )
    return [services.session_note_service.to_revision_response(revision) for revision in revisions]


@router.post("/save", response_model=NoteResponse, status_code=status.HTTP_200_OK)
async def save_note(
    payload: NoteSaveRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> NoteResponse:
    await document_service.get_document(session, user_id=current_user.id, document_id=payload.document_id)
    services = build_services(settings)
    note = await services.note_service.save_note(
        session,
        user_id=current_user.id,
        document_id=payload.document_id,
        generated_note=GeneratedNote(
            summary=payload.summary,
            key_points=payload.key_points,
            action_items=payload.action_items,
        ),
    )
    await session.commit()
    await session.refresh(note)
    return NoteResponse.model_validate(note)
