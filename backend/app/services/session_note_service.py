from __future__ import annotations

from difflib import unified_diff

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.session_note import SessionNote
from app.models.session_note_revision import SessionNoteRevision
from app.schemas.session_note import SessionNoteResponse, SessionNoteRevisionResponse, SessionNoteSummary


class SessionNoteService:
    async def list_notes(self, session: AsyncSession, *, user_id: str) -> list[SessionNote]:
        result = await session.execute(
            select(SessionNote).where(SessionNote.user_id == user_id).order_by(SessionNote.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_note_for_conversation(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
    ) -> SessionNote | None:
        result = await session.execute(
            select(SessionNote).where(
                SessionNote.user_id == user_id,
                SessionNote.conversation_id == conversation_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_note(self, session: AsyncSession, *, user_id: str, note_id: str) -> SessionNote:
        result = await session.execute(select(SessionNote).where(SessionNote.id == note_id, SessionNote.user_id == user_id))
        note = result.scalar_one_or_none()
        if note is None:
            raise NotFoundError("Session note not found.")
        return note

    async def list_revisions(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        note_id: str,
    ) -> list[SessionNoteRevision]:
        note = await self.get_note(session, user_id=user_id, note_id=note_id)
        result = await session.execute(
            select(SessionNoteRevision)
            .where(SessionNoteRevision.note_id == note.id)
            .order_by(SessionNoteRevision.created_at.desc())
        )
        return list(result.scalars().all())

    async def apply_patch(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        conversation_id: str,
        assistant_run_id: str,
        title: str,
        full_markdown: str,
    ) -> tuple[SessionNote, SessionNoteRevision]:
        note = await self.get_note_for_conversation(
            session,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        if note is None:
            note = SessionNote(
                user_id=user_id,
                conversation_id=conversation_id,
                title=title.strip() or "Study Note",
                current_markdown="",
            )
            session.add(note)
            await session.flush()

        previous = note.current_markdown or ""
        note.title = title.strip() or note.title or "Study Note"
        note.current_markdown = full_markdown.strip()

        revision = SessionNoteRevision(
            note_id=note.id,
            assistant_run_id=assistant_run_id,
            patch_format="unified_diff",
            patch_text=self._build_unified_diff(previous, note.current_markdown),
            result_markdown=note.current_markdown,
        )
        session.add(revision)
        await session.flush()
        return note, revision

    def to_response(self, note: SessionNote) -> SessionNoteResponse:
        return SessionNoteResponse.model_validate(note)

    def to_revision_response(self, revision: SessionNoteRevision) -> SessionNoteRevisionResponse:
        return SessionNoteRevisionResponse.model_validate(revision)

    def to_summary(self, note: SessionNote) -> SessionNoteSummary:
        return SessionNoteSummary(
            id=note.id,
            conversation_id=note.conversation_id,
            title=note.title,
            updated_at=note.updated_at,
        )

    def _build_unified_diff(self, before: str, after: str) -> str:
        return "\n".join(
            unified_diff(
                before.splitlines(),
                after.splitlines(),
                fromfile="before.md",
                tofile="after.md",
                lineterm="",
            )
        )
