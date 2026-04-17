from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.document import AnalysisSummaryResponse, AnalyzeDocumentRequest, AssistantExecuteRequest
from app.services import build_services

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/execute", response_model=AnalysisSummaryResponse)
async def execute_assistant(
    payload: AssistantExecuteRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AnalysisSummaryResponse:
    services = build_services(settings)
    analysis_run, document = await services.orchestrator_service.analyze_document(
        session,
        user_id=current_user.id,
        document_id=payload.document_id,
        payload=AnalyzeDocumentRequest(
            requested_actions=payload.requested_actions,
            archive_to_drive=payload.archive_to_drive,
            save_notes=payload.save_notes,
        ),
        settings=settings,
    )
    return AnalysisSummaryResponse(
        document_id=document.id,
        analysis_run=analysis_run,
        note=document.note,
        candidate_events=document.candidate_events,
    )
