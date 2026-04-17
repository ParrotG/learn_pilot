from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import BadRequestError
from app.integrations.google import (
    build_drive_resource,
    build_user_credentials,
    ensure_drive_folder,
    upload_file_to_drive,
)
from app.models.document import Document
from app.models.enums import DocumentProcessingStatus, ExportArtifactStatus
from app.models.export_artifact import ExportArtifact
from app.schemas.drive import DriveArchiveResponse
from app.services.credential_service import CredentialService
from app.services.document_service import DocumentService
from app.services.export_service import ExportService


class DriveService:
    def __init__(
        self,
        credential_service: CredentialService,
        document_service: DocumentService,
        export_service: ExportService,
    ) -> None:
        self.credential_service = credential_service
        self.document_service = document_service
        self.export_service = export_service

    async def archive_document(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        document_id: str,
        settings: Settings,
    ) -> Document:
        document = await self.document_service.get_document(session, user_id=user_id, document_id=document_id)
        if document.drive_file_id and document.drive_folder_id:
            return document

        access_token, refresh_token, expiry = await self.credential_service.get_google_tokens(
            session, user_id=user_id, settings=settings
        )
        credentials = build_user_credentials(
            settings=settings,
            access_token=access_token,
            refresh_token=refresh_token,
            expiry=expiry,
        )
        drive_service = build_drive_resource(credentials)
        folder_name = f"{settings.google_drive_root_folder_name}-{user_id}"
        folder_id = ensure_drive_folder(drive_service, folder_name)
        file_id = upload_file_to_drive(
            drive_service,
            folder_id=folder_id,
            filename=document.filename,
            file_path=document.storage_path,
            mime_type=document.mime_type,
        )
        document.drive_folder_id = folder_id
        document.drive_file_id = file_id
        document.processing_status = DocumentProcessingStatus.ARCHIVED.value
        await session.commit()
        await session.refresh(document)
        return document

    async def upload_export_artifact(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        artifact_id: str,
        settings: Settings,
    ) -> ExportArtifact:
        artifact = await self.export_service.get_export_artifact(session, user_id=user_id, artifact_id=artifact_id)
        if artifact.status not in {
            ExportArtifactStatus.COMPLETED.value,
            ExportArtifactStatus.UPLOADED.value,
        }:
            raise BadRequestError("Only completed export artifacts can be uploaded to Google Drive.")
        if artifact.drive_file_id and artifact.drive_folder_id:
            artifact.status = ExportArtifactStatus.UPLOADED.value
            await session.flush()
            return artifact

        access_token, refresh_token, expiry = await self.credential_service.get_google_tokens(
            session,
            user_id=user_id,
            settings=settings,
        )
        credentials = build_user_credentials(
            settings=settings,
            access_token=access_token,
            refresh_token=refresh_token,
            expiry=expiry,
        )
        drive_service = build_drive_resource(credentials)
        folder_name = f"{settings.google_drive_root_folder_name}-{user_id}"
        folder_id = ensure_drive_folder(drive_service, folder_name)
        file_id = upload_file_to_drive(
            drive_service,
            folder_id=folder_id,
            filename=artifact.filename,
            file_path=artifact.storage_path,
            mime_type=self._resolve_export_mime_type(artifact.target_format),
        )
        artifact.drive_folder_id = folder_id
        artifact.drive_file_id = file_id
        artifact.status = ExportArtifactStatus.UPLOADED.value
        artifact.error_message = None
        await session.flush()
        return artifact

    def get_archive_response(self, document: Document) -> DriveArchiveResponse:
        return DriveArchiveResponse(
            document_id=document.id,
            drive_file_id=document.drive_file_id,
            drive_folder_id=document.drive_folder_id,
            archived=bool(document.drive_file_id),
        )

    def _resolve_export_mime_type(self, target_format: str) -> str:
        if target_format == "docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if target_format == "pptx":
            return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        return "application/octet-stream"
