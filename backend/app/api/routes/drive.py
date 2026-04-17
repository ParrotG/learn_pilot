from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.drive import DriveArchiveRequest, DriveArchiveResponse
from app.services import build_services
from app.services.document_service import DocumentService

router = APIRouter(prefix="/drive", tags=["drive"])
document_service = DocumentService()


@router.post("/archive", response_model=DriveArchiveResponse)
async def archive_document(
    payload: DriveArchiveRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DriveArchiveResponse:
    services = build_services(settings)
    document = await services.drive_service.archive_document(
        session,
        user_id=current_user.id,
        document_id=payload.document_id,
        settings=settings,
    )
    return services.drive_service.get_archive_response(document)


@router.get("/files/{document_id}", response_model=DriveArchiveResponse)
async def get_drive_file_info(
    document_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DriveArchiveResponse:
    services = build_services(settings)
    document = await document_service.get_document(session, user_id=current_user.id, document_id=document_id)
    return services.drive_service.get_archive_response(document)
