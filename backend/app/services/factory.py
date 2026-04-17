from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.integrations.openai_client import OpenAIStructuredClient
from app.services.calendar_service import CalendarService
from app.services.credential_service import CredentialService
from app.services.document_service import DocumentService
from app.services.drive_service import DriveService
from app.services.intent_service import IntentService
from app.services.note_service import NoteService
from app.services.orchestrator_service import OrchestratorService


@dataclass
class ServiceBundle:
    credential_service: CredentialService
    document_service: DocumentService
    note_service: NoteService
    intent_service: IntentService
    calendar_service: CalendarService
    drive_service: DriveService
    orchestrator_service: OrchestratorService


def build_services(settings: Settings) -> ServiceBundle:
    credential_service = CredentialService()
    document_service = DocumentService()
    llm_client = OpenAIStructuredClient(settings)
    note_service = NoteService(llm_client)
    intent_service = IntentService(llm_client)
    calendar_service = CalendarService(llm_client, credential_service)
    drive_service = DriveService(credential_service, document_service)
    orchestrator_service = OrchestratorService(
        credential_service=credential_service,
        document_service=document_service,
        intent_service=intent_service,
        note_service=note_service,
        calendar_service=calendar_service,
        drive_service=drive_service,
    )
    return ServiceBundle(
        credential_service=credential_service,
        document_service=document_service,
        note_service=note_service,
        intent_service=intent_service,
        calendar_service=calendar_service,
        drive_service=drive_service,
        orchestrator_service=orchestrator_service,
    )

