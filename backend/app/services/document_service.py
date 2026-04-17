from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import fitz
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.errors import BadRequestError, NotFoundError
from app.models.document import Document
from app.models.enums import DocumentProcessingStatus


class DocumentService:
    async def upload_document(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        upload: UploadFile,
        settings: Settings,
    ) -> Document:
        if upload.content_type != "application/pdf" and not upload.filename.lower().endswith(".pdf"):
            raise BadRequestError("Only PDF documents are supported.")

        file_bytes = await upload.read()
        if not file_bytes:
            raise BadRequestError("The uploaded file is empty.")

        extracted_text = self.extract_text(file_bytes)
        user_directory = settings.resolved_upload_dir / user_id
        user_directory.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid4()}-{Path(upload.filename).name}"
        storage_path = user_directory / safe_name
        storage_path.write_bytes(file_bytes)

        document = Document(
            user_id=user_id,
            filename=upload.filename,
            storage_path=str(storage_path),
            mime_type=upload.content_type or "application/pdf",
            file_size=len(file_bytes),
            extracted_text=extracted_text,
            processing_status=DocumentProcessingStatus.UPLOADED.value,
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document

    def extract_text(self, file_bytes: bytes) -> str:
        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            raise BadRequestError("The uploaded file is not a valid PDF.") from exc

        text_chunks = [page.get_text("text").strip() for page in document]
        extracted_text = "\n\n".join(chunk for chunk in text_chunks if chunk)
        return extracted_text.strip()

    async def list_documents(self, session: AsyncSession, *, user_id: str) -> list[Document]:
        result = await session.execute(
            select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_document_detail(self, session: AsyncSession, *, user_id: str, document_id: str) -> Document:
        query = (
            select(Document)
            .where(Document.id == document_id, Document.user_id == user_id)
            .options(
                selectinload(Document.note),
                selectinload(Document.candidate_events),
                selectinload(Document.analysis_runs),
            )
            .execution_options(populate_existing=True)
        )
        result = await session.execute(query)
        document = result.scalar_one_or_none()
        if document is None:
            raise NotFoundError("Document not found.")
        return document

    async def get_document(self, session: AsyncSession, *, user_id: str, document_id: str) -> Document:
        result = await session.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )
        document = result.scalar_one_or_none()
        if document is None:
            raise NotFoundError("Document not found.")
        return document
