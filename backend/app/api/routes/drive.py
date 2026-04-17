from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.enums import AssistantRunExecutionStatus
from app.models.user import User
from app.schemas.drive import DriveArchiveRequest, DriveArchiveResponse, DriveArtifactUploadRequest
from app.schemas.export import ExportRequestResponse
from app.schemas.run import AssistantRunResponse
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


@router.post("/upload-artifact", response_model=ExportRequestResponse)
async def request_drive_upload_artifact(
    payload: DriveArtifactUploadRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ExportRequestResponse:
    services = build_services(settings)
    artifact = await services.export_service.get_export_artifact(
        session,
        user_id=current_user.id,
        artifact_id=payload.artifact_id,
    )
    system_message = await services.message_service.create_system_message(
        session,
        user_id=current_user.id,
        conversation_id=artifact.conversation_id,
        content=f"Requested upload of export artifact {artifact.filename} to Google Drive.",
    )
    run = await services.assistant_runtime_service.create_run(
        session,
        user_id=current_user.id,
        conversation_id=artifact.conversation_id,
        message_id=system_message.id,
    )
    tool_call = await services.tool_gateway_service.create_drive_upload_tool_call(
        session,
        run=run,
        artifact_id=artifact.id,
    )
    run.status = AssistantRunExecutionStatus.WAITING_FOR_APPROVAL.value
    run.pending_tool_call_id = tool_call.id
    await session.commit()
    return ExportRequestResponse(
        assistant_run=AssistantRunResponse.model_validate(run),
        tool_call=services.tool_gateway_service.to_response(tool_call),
    )
