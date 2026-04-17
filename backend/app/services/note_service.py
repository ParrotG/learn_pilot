from __future__ import annotations

import json

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ExternalServiceError
from app.integrations.openai_client import OpenAIStructuredClient
from app.models.note import Note
from app.schemas.domain import GeneratedNote

NOTE_SYSTEM_PROMPT = """
Generate structured study notes for the provided document.
Return JSON with:
- summary: concise summary
- key_points: array of important learning points
- action_items: array of concrete student actions
""".strip()


class NoteService:
    def __init__(self, llm_client: OpenAIStructuredClient) -> None:
        self.llm_client = llm_client

    async def generate_note(self, *, api_key: str, document_text: str) -> tuple[GeneratedNote, str]:
        raw_json = await self.llm_client.generate_json(
            api_key=api_key,
            system_prompt=NOTE_SYSTEM_PROMPT,
            user_prompt=f"Document text:\n{document_text[:20000]}",
        )
        try:
            parsed = GeneratedNote.model_validate(json.loads(raw_json))
        except (ValidationError, json.JSONDecodeError) as exc:
            raise ExternalServiceError("The note generation response could not be validated.", raw_json) from exc
        return parsed, raw_json

    async def save_note(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        document_id: str,
        generated_note: GeneratedNote,
    ) -> Note:
        result = await session.execute(select(Note).where(Note.document_id == document_id))
        note = result.scalar_one_or_none()
        if note is None:
            note = Note(
                user_id=user_id,
                document_id=document_id,
                summary=generated_note.summary,
                key_points=generated_note.key_points,
                action_items=generated_note.action_items,
            )
            session.add(note)
        else:
            note.summary = generated_note.summary
            note.key_points = generated_note.key_points
            note.action_items = generated_note.action_items
        await session.flush()
        return note

    async def list_notes(self, session: AsyncSession, *, user_id: str) -> list[Note]:
        result = await session.execute(select(Note).where(Note.user_id == user_id).order_by(Note.created_at.desc()))
        return list(result.scalars().all())

