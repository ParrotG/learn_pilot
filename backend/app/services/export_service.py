from __future__ import annotations

import asyncio
from pathlib import Path
import re
import shutil
import tempfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import BadRequestError, ExternalConfigurationError, ExternalServiceError, NotFoundError
from app.models.enums import ExportArtifactStatus
from app.models.export_artifact import ExportArtifact
from app.schemas.export import ExportArtifactResponse
from app.services.session_note_service import SessionNoteService


class ExportService:
    def __init__(self, session_note_service: SessionNoteService | None) -> None:
        self.session_note_service = session_note_service

    def is_pandoc_available(self, settings: Settings) -> bool:
        return self.resolve_pandoc_binary(settings) is not None

    def resolve_pandoc_binary(self, settings: Settings) -> str | None:
        binary = settings.pandoc_binary.strip()
        if not binary:
            return None
        binary_path = Path(binary)
        if binary_path.is_absolute() and binary_path.exists():
            return str(binary_path)
        return shutil.which(binary)

    def ensure_pandoc_available(self, settings: Settings) -> str:
        pandoc_binary = self.resolve_pandoc_binary(settings)
        if pandoc_binary is None:
            raise ExternalConfigurationError(
                "Pandoc is not installed or not reachable. Install it with `sudo apt-get update && sudo apt-get install -y pandoc`, then verify `pandoc --version`, or set PANDOC_BINARY to the correct executable path."
            )
        return pandoc_binary

    async def list_conversation_exports(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
    ) -> list[ExportArtifact]:
        result = await session.execute(
            select(ExportArtifact)
            .where(
                ExportArtifact.user_id == user_id,
                ExportArtifact.conversation_id == conversation_id,
            )
            .order_by(ExportArtifact.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_recent_exports(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        limit: int = 5,
    ) -> list[ExportArtifact]:
        result = await session.execute(
            select(ExportArtifact)
            .where(ExportArtifact.user_id == user_id)
            .order_by(ExportArtifact.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_export_artifact(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        artifact_id: str,
    ) -> ExportArtifact:
        result = await session.execute(
            select(ExportArtifact).where(
                ExportArtifact.id == artifact_id,
                ExportArtifact.user_id == user_id,
            )
        )
        artifact = result.scalar_one_or_none()
        if artifact is None:
            raise NotFoundError("Export artifact not found.")
        return artifact

    async def generate_export_artifact(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        assistant_run_id: str,
        tool_call_id: str,
        target_format: str,
        note_id: str | None,
        settings: Settings,
    ) -> ExportArtifact:
        if target_format not in {"docx", "pptx"}:
            raise BadRequestError("Only docx and pptx exports are supported.")
        if self.session_note_service is None:
            raise ExternalConfigurationError("The export service is not fully configured.")

        pandoc_binary = self.ensure_pandoc_available(settings)
        if note_id:
            note = await self.session_note_service.get_note(session, user_id=user_id, note_id=note_id)
            if note.conversation_id != conversation_id:
                raise BadRequestError("The selected note does not belong to this conversation.")
        else:
            note = await self.session_note_service.get_note_for_conversation(
                session,
                user_id=user_id,
                conversation_id=conversation_id,
            )
            if note is None:
                raise BadRequestError("This conversation does not have a session note to export.")

        artifact = ExportArtifact(
            conversation_id=conversation_id,
            note_id=note.id,
            assistant_run_id=assistant_run_id,
            tool_call_id=tool_call_id,
            user_id=user_id,
            source_format="markdown",
            target_format=target_format,
            filename=f"pending.{target_format}",
            storage_path="",
            file_size=0,
            status=ExportArtifactStatus.GENERATING.value,
        )
        session.add(artifact)
        await session.flush()

        settings.resolved_export_dir.mkdir(parents=True, exist_ok=True)
        filename = self._build_output_filename(note.title, artifact.id, target_format)
        output_path = settings.resolved_export_dir / filename
        artifact.filename = filename
        artifact.storage_path = str(output_path)

        with tempfile.TemporaryDirectory(prefix="learnpilot-export-") as temp_dir:
            source_path = Path(temp_dir) / f"source-{artifact.id}.md"
            source_path.write_text(note.current_markdown, encoding="utf-8")
            await self._run_pandoc(
                pandoc_binary=pandoc_binary,
                source_path=source_path,
                output_path=output_path,
            )

        artifact.file_size = output_path.stat().st_size
        artifact.status = ExportArtifactStatus.COMPLETED.value
        artifact.error_message = None
        await session.flush()
        return artifact

    async def mark_artifact_failed(
        self,
        session: AsyncSession,
        *,
        artifact: ExportArtifact,
        message: str,
    ) -> None:
        artifact.status = ExportArtifactStatus.FAILED.value
        artifact.error_message = message
        await session.flush()

    def to_response(self, artifact: ExportArtifact) -> ExportArtifactResponse:
        return ExportArtifactResponse.model_validate(artifact)

    async def _run_pandoc(
        self,
        *,
        pandoc_binary: str,
        source_path: Path,
        output_path: Path,
    ) -> None:
        process = await asyncio.create_subprocess_exec(
            pandoc_binary,
            str(source_path),
            "--from",
            "markdown",
            "--to",
            output_path.suffix.lstrip("."),
            "--output",
            str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            details = stderr.decode("utf-8", errors="ignore").strip() or stdout.decode(
                "utf-8", errors="ignore"
            ).strip()
            raise ExternalServiceError(
                "Pandoc failed to generate the export artifact.",
                details=details or "Pandoc exited with a non-zero status.",
            )

    def _build_output_filename(self, note_title: str, artifact_id: str, target_format: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", note_title.strip().lower()).strip("-")
        safe_slug = slug or "session-note"
        short_id = artifact_id.split("-", maxsplit=1)[0]
        return f"{safe_slug}-{short_id}.{target_format}"
