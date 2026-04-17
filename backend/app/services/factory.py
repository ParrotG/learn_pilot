from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.integrations.openai_client import OpenAIStructuredClient
from app.services.assistant_runtime_service import AssistantRuntimeService
from app.services.calendar_service import CalendarService
from app.services.conversation_service import ConversationService
from app.services.credential_service import CredentialService
from app.services.document_service import DocumentService
from app.services.drive_service import DriveService
from app.services.intent_service import IntentService
from app.services.message_service import MessageService
from app.services.note_service import NoteService
from app.services.orchestrator_service import OrchestratorService
from app.services.workspace_document_service import WorkspaceDocumentService


@dataclass
class ServiceBundle:
    credential_service: CredentialService
    document_service: DocumentService
    conversation_service: ConversationService
    message_service: MessageService
    workspace_document_service: WorkspaceDocumentService
    assistant_runtime_service: AssistantRuntimeService
    note_service: NoteService
    intent_service: IntentService
    calendar_service: CalendarService
    drive_service: DriveService
    orchestrator_service: OrchestratorService


def build_services(settings: Settings) -> ServiceBundle:
    credential_service = CredentialService()
    document_service = DocumentService()
    conversation_service = ConversationService()
    message_service = MessageService(conversation_service)
    llm_client = OpenAIStructuredClient(settings)
    workspace_document_service = WorkspaceDocumentService(
        document_service=document_service,
        conversation_service=conversation_service,
        message_service=message_service,
    )
    assistant_runtime_service = AssistantRuntimeService(
        llm_client=llm_client,
        credential_service=credential_service,
        conversation_service=conversation_service,
        message_service=message_service,
    )
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
        conversation_service=conversation_service,
        message_service=message_service,
        workspace_document_service=workspace_document_service,
        assistant_runtime_service=assistant_runtime_service,
        note_service=note_service,
        intent_service=intent_service,
        calendar_service=calendar_service,
        drive_service=drive_service,
        orchestrator_service=orchestrator_service,
    )
