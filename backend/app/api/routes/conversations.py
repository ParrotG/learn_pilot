from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.conversation import ConversationCreateRequest, ConversationDetailResponse, ConversationResponse
from app.schemas.run import AssistantRunResponse
from app.schemas.session_note import SessionNoteResponse
from app.services import build_services

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    payload: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ConversationResponse:
    services = build_services(settings)
    conversation = await services.conversation_service.create_conversation(
        session,
        user_id=current_user.id,
        title=payload.title,
        initial_document_ids=payload.initial_document_ids,
    )
    return ConversationResponse.model_validate(conversation)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[ConversationResponse]:
    services = build_services(settings)
    conversations = await services.conversation_service.list_conversations(session, user_id=current_user.id)
    return [ConversationResponse.model_validate(conversation) for conversation in conversations]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ConversationDetailResponse:
    services = build_services(settings)
    conversation = await services.conversation_service.get_conversation(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    latest_run = await services.conversation_service.get_latest_run(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    latest_note = await services.session_note_service.get_note_for_conversation(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    pending_tool_call = await services.tool_gateway_service.get_pending_tool_call_for_conversation(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return ConversationDetailResponse(
        **ConversationResponse.model_validate(conversation).model_dump(),
        latest_run=AssistantRunResponse.model_validate(latest_run) if latest_run else None,
        latest_note=services.session_note_service.to_summary(latest_note) if latest_note else None,
        pending_tool_call=services.tool_gateway_service.to_response(pending_tool_call) if pending_tool_call else None,
    )


@router.get("/{conversation_id}/note", response_model=SessionNoteResponse | None)
async def get_conversation_note(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> SessionNoteResponse | None:
    services = build_services(settings)
    note = await services.session_note_service.get_note_for_conversation(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    if note is None:
        return None
    return services.session_note_service.to_response(note)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    services = build_services(settings)
    await services.conversation_service.delete_conversation(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
