from __future__ import annotations

from pydantic import BaseModel


class DriveArchiveRequest(BaseModel):
    document_id: str


class DriveArchiveResponse(BaseModel):
    document_id: str
    drive_file_id: str | None
    drive_folder_id: str | None
    archived: bool


class DriveArtifactUploadRequest(BaseModel):
    artifact_id: str
