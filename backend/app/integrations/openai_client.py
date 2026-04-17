from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.core.config import Settings
from app.core.errors import ExternalServiceError


class OpenAIStructuredClient:
    """Wrapper around the OpenAI-compatible API for JSON outputs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_json(self, *, api_key: str, system_prompt: str, user_prompt: str) -> str:
        client = AsyncOpenAI(api_key=api_key, base_url=self.settings.openai_base_url)
        try:
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                response_format={"type": "json_object"},
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # pragma: no cover - external client errors vary
            raise ExternalServiceError("OpenAI request failed.", details=str(exc)) from exc
        finally:
            await client.close()

        content = response.choices[0].message.content
        if not content:
            raise ExternalServiceError("OpenAI returned an empty response.")

        try:
            json.loads(content)
        except json.JSONDecodeError as exc:
            raise ExternalServiceError("OpenAI response was not valid JSON.", details=content) from exc
        return content

