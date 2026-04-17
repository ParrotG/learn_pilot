from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.enums import AssistantRunExecutionStatus
from app.models.user import User
from app.schemas.export import ExportArtifactResponse, ExportRequestCreate, ExportRequestResponse
from app.schemas.run import AssistantRunResponse
from app.services import build_services

router = APIRouter(tags=["exports"])


@router.get("/conversations/{conversation_id}/exports", response_model=list[ExportArtifactResponse])
async def list_conversation_exports(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[ExportArtifactResponse]:
    services = build_services(settings)
    artifacts = await services.export_service.list_conversation_exports(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return [services.export_service.to_response(artifact) for artifact in artifacts]


@router.post("/conversations/{conversation_id}/exports", response_model=ExportRequestResponse)
async def request_conversation_export(
    conversation_id: str,
    payload: ExportRequestCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ExportRequestResponse:
    services = build_services(settings)
    system_message = await services.message_service.create_system_message(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
        content=f"Requested export of the current session note as {payload.target_format.upper()}.",
    )
    run = await services.assistant_runtime_service.create_run(
        session,
        user_id=current_user.id,
        conversation_id=conversation_id,
        message_id=system_message.id,
    )
    tool_call = await services.tool_gateway_service.create_export_tool_call(
        session,
        run=run,
        target_format=payload.target_format,
        note_id=payload.note_id,
    )
    run.status = AssistantRunExecutionStatus.WAITING_FOR_APPROVAL.value
    run.pending_tool_call_id = tool_call.id
    await session.commit()
    return ExportRequestResponse(
        assistant_run=AssistantRunResponse.model_validate(run),
        tool_call=services.tool_gateway_service.to_response(tool_call),
    )


@router.get("/exports", response_model=list[ExportArtifactResponse])
async def list_recent_exports(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> list[ExportArtifactResponse]:
    services = build_services(settings)
    artifacts = await services.export_service.list_recent_exports(
        session,
        user_id=current_user.id,
        limit=max(1, min(limit, 20)),
    )
    return [services.export_service.to_response(artifact) for artifact in artifacts]


@router.get("/exports/{artifact_id}", response_model=ExportArtifactResponse)
async def get_export_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ExportArtifactResponse:
    services = build_services(settings)
    artifact = await services.export_service.get_export_artifact(
        session,
        user_id=current_user.id,
        artifact_id=artifact_id,
    )
    return services.export_service.to_response(artifact)


@router.get("/exports/{artifact_id}/download")
async def download_export_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    services = build_services(settings)
    artifact = await services.export_service.get_export_artifact(
        session,
        user_id=current_user.id,
        artifact_id=artifact_id,
    )
    return FileResponse(
        Path(artifact.storage_path),
        filename=artifact.filename,
        media_type="application/octet-stream",
    )
