from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.enums import AssistantRunExecutionStatus
from app.models.user import User
from app.schemas.tool_call import ToolApprovalRequest, ToolApprovalResponse, ToolCallResponse
from app.services import build_services

router = APIRouter(prefix="/tool-calls", tags=["tool-calls"])


@router.get("/{tool_call_id}", response_model=ToolCallResponse)
async def get_tool_call(
    tool_call_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ToolCallResponse:
    services = build_services(settings)
    tool_call = await services.tool_gateway_service.get_tool_call(
        session,
        user_id=current_user.id,
        tool_call_id=tool_call_id,
    )
    return services.tool_gateway_service.to_response(tool_call)


@router.post("/{tool_call_id}/approve", response_model=ToolApprovalResponse)
async def approve_tool_call(
    tool_call_id: str,
    payload: ToolApprovalRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ToolApprovalResponse:
    services = build_services(settings)
    tool_call = await services.tool_gateway_service.get_tool_call(
        session,
        user_id=current_user.id,
        tool_call_id=tool_call_id,
    )
    await services.tool_gateway_service.approve_tool_call(
        session,
        tool_call=tool_call,
        user_id=current_user.id,
        comment=payload.decision_comment,
    )
    run = await services.assistant_runtime_service.get_run(
        session,
        user_id=current_user.id,
        run_id=tool_call.assistant_run_id,
    )
    run.status = AssistantRunExecutionStatus.QUEUED.value
    await session.commit()
    background_tasks.add_task(services.assistant_runtime_service.process_run, run.id, settings)
    return ToolApprovalResponse(tool_call_id=tool_call.id, status=tool_call.status, assistant_run_id=run.id)


@router.post("/{tool_call_id}/reject", response_model=ToolApprovalResponse)
async def reject_tool_call(
    tool_call_id: str,
    payload: ToolApprovalRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ToolApprovalResponse:
    services = build_services(settings)
    tool_call = await services.tool_gateway_service.get_tool_call(
        session,
        user_id=current_user.id,
        tool_call_id=tool_call_id,
    )
    await services.tool_gateway_service.reject_tool_call(
        session,
        tool_call=tool_call,
        user_id=current_user.id,
        comment=payload.decision_comment,
    )
    run = await services.assistant_runtime_service.get_run(
        session,
        user_id=current_user.id,
        run_id=tool_call.assistant_run_id,
    )
    run.status = AssistantRunExecutionStatus.QUEUED.value
    await session.commit()
    background_tasks.add_task(services.assistant_runtime_service.process_run, run.id, settings)
    return ToolApprovalResponse(tool_call_id=tool_call.id, status=tool_call.status, assistant_run_id=run.id)
