from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.credentials import (
    CredentialStatusResponse,
    GoogleCallbackResponse,
    GoogleConnectResponse,
    LLMCredentialUpsertRequest,
)
from app.services.credential_service import CredentialService

router = APIRouter(prefix="/credentials", tags=["credentials"])
credential_service = CredentialService()


@router.post("/llm", response_model=CredentialStatusResponse)
async def save_llm_credential(
    payload: LLMCredentialUpsertRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> CredentialStatusResponse:
    return await credential_service.upsert_llm_credential(
        session,
        user_id=current_user.id,
        payload=payload,
        settings=settings,
    )


@router.post("/google/connect", response_model=GoogleConnectResponse)
async def google_connect(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> GoogleConnectResponse:
    return await credential_service.build_google_connect_response(
        session,
        user_id=current_user.id,
        settings=settings,
    )


@router.get("/google/callback", response_model=GoogleCallbackResponse)
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> GoogleCallbackResponse:
    return await credential_service.handle_google_callback(
        session,
        code=code,
        state=state,
        settings=settings,
    )


@router.get("/status", response_model=CredentialStatusResponse)
async def credential_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CredentialStatusResponse:
    return await credential_service.get_status(session, user_id=current_user.id)
