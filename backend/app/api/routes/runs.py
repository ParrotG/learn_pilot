from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.run import AssistantRunResponse, AssistantRunStartRequest, AssistantRunStartResponse
from app.services import build_services

router = APIRouter(tags=["runs"])


@router.post("/conversations/{conversation_id}/runs", response_model=AssistantRunStartResponse)
async def create_run(
    conversation_id: str,
    payload: AssistantRunStartRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AssistantRunStartResponse:
    services = build_services(settings)
    if payload.message_id:
        message = await services.message_service.get_message(
            session,
            user_id=current_user.id,
            conversation_id=conversation_id,
            message_id=payload.message_id,
        )
    else:
        message = await services.message_service.get_latest_user_message(
            session,
            user_id=current_user.id,
            conversation_id=conversation_id,
        )

    run = await services.assistant_runtime_service.create_run(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
        message_id=message.id,
    )
    background_tasks.add_task(services.assistant_runtime_service.process_run, run.id, settings)
    return AssistantRunStartResponse(assistant_run=AssistantRunResponse.model_validate(run))


@router.get("/runs/{run_id}", response_model=AssistantRunResponse)
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AssistantRunResponse:
    services = build_services(settings)
    run = await services.assistant_runtime_service.get_run(session, user_id=current_user.id, run_id=run_id)
    return AssistantRunResponse.model_validate(run)
