from __future__ import annotations

import json

from pydantic import ValidationError

from app.core.errors import ExternalServiceError
from app.integrations.openai_client import OpenAIStructuredClient
from app.schemas.domain import IntentResult

INTENT_SYSTEM_PROMPT = """
You are classifying study-document actions for a learning assistant.
Return JSON with:
- actions: array of supported action strings
- confidence: number from 0 to 1
- reasoning_summary: short explanation

Supported actions:
- summarize
- extract_key_points
- extract_schedule_events
- archive_file
- save_notes

Only include relevant actions.
""".strip()


class IntentService:
    def __init__(self, llm_client: OpenAIStructuredClient) -> None:
        self.llm_client = llm_client

    async def classify_intent(self, *, api_key: str, document_text: str) -> tuple[IntentResult, str]:
        user_prompt = f"Document text:\n{document_text[:12000]}"
        raw_json = await self.llm_client.generate_json(
            api_key=api_key,
            system_prompt=INTENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        try:
            parsed = IntentResult.model_validate(json.loads(raw_json))
        except (ValidationError, json.JSONDecodeError) as exc:
            raise ExternalServiceError("The intent classification response could not be validated.", raw_json) from exc
        return parsed, raw_json

