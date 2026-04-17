from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.workspace import ConversationDocumentResponse, ConversationDocumentUploadResponse
from app.services import build_services

router = APIRouter(prefix="/conversations/{conversation_id}/documents", tags=["workspace"])


@router.get("", response_model=list[ConversationDocumentResponse])
async def list_conversation_documents(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[ConversationDocumentResponse]:
    services = build_services(settings)
    documents = await services.workspace_document_service.list_conversation_documents(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return [services.workspace_document_service.to_response(item) for item in documents]


@router.post("", response_model=ConversationDocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_conversation_document(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ConversationDocumentUploadResponse:
    services = build_services(settings)
    uploaded = await services.workspace_document_service.upload_to_conversation(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
        upload=file,
        settings=settings,
    )
    return ConversationDocumentUploadResponse(
        document=uploaded["document"],
        conversation_document=uploaded["conversation_document"],
        system_message=uploaded["system_message"],
    )
