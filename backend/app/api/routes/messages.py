from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.message import MessageCreateRequest, MessageCreateResponse, MessageResponse
from app.schemas.run import AssistantRunResponse
from app.services import build_services

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["messages"])


@router.get("", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[MessageResponse]:
    services = build_services(settings)
    messages = await services.message_service.list_messages(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return [services.message_service.to_response(message) for message in messages]


@router.post("", response_model=MessageCreateResponse)
async def create_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> MessageCreateResponse:
    services = build_services(settings)
    message = await services.message_service.create_user_message(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
        content=payload.content,
        attachment_document_ids=payload.attachment_document_ids,
    )
    run = None
    if payload.auto_create_run:
        run = await services.assistant_runtime_service.create_run(
            session,
            user_id=current_user.id,
            conversation_id=conversation_id,
            message_id=message.id,
        )
        background_tasks.add_task(services.assistant_runtime_service.process_run, run.id, settings)

    return MessageCreateResponse(
        message=services.message_service.to_response(message),
        assistant_run=AssistantRunResponse.model_validate(run) if run else None,
    )
