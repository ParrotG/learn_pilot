from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.document import (
    AnalysisSummaryResponse,
    AnalyzeDocumentRequest,
    DocumentDetailResponse,
    DocumentListItem,
)
from app.services import build_services

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentListItem, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentListItem:
    services = build_services(settings)
    document = await services.document_service.upload_document(
        session, user_id=current_user.id, upload=file, settings=settings
    )
    return DocumentListItem.model_validate(document)


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[DocumentListItem]:
    services = build_services(settings)
    documents = await services.document_service.list_documents(session, user_id=current_user.id)
    return [DocumentListItem.model_validate(document) for document in documents]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_detail(
    document_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentDetailResponse:
    services = build_services(settings)
    document = await services.document_service.get_document_detail(
        session, user_id=current_user.id, document_id=document_id
    )
    return DocumentDetailResponse.model_validate(document)


@router.post("/{document_id}/analyze", response_model=AnalysisSummaryResponse)
async def analyze_document(
    document_id: str,
    payload: AnalyzeDocumentRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AnalysisSummaryResponse:
    services = build_services(settings)
    analysis_run, document = await services.orchestrator_service.analyze_document(
        session,
        user_id=current_user.id,
        document_id=document_id,
        payload=payload,
        settings=settings,
    )
    return AnalysisSummaryResponse(
        document_id=document.id,
        analysis_run=analysis_run,
        note=document.note,
        candidate_events=document.candidate_events,
    )
