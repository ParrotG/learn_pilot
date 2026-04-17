from __future__ import annotations

import json

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, AuthenticationError, PermissionDeniedError

from app.core.config import Settings
from app.core.errors import BadRequestError, ExternalServiceError


class OpenAIStructuredClient:
    """Wrapper around the OpenAI-compatible API for JSON outputs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def validate_api_key(self, *, api_key: str) -> None:
        client = AsyncOpenAI(api_key=api_key, base_url=self.settings.openai_base_url)
        try:
            await client.models.list()
        except (AuthenticationError, PermissionDeniedError) as exc:
            raise BadRequestError(
                "The provided OpenAI API key could not be verified. Please check the key and try again.",
                details=str(exc),
            ) from exc
        except APIConnectionError as exc:
            raise ExternalServiceError(
                "LearnPilot could not reach the OpenAI API while verifying the key.",
                details=str(exc),
            ) from exc
        except APIStatusError as exc:
            raise ExternalServiceError(
                "OpenAI rejected the verification request.",
                details=str(exc),
            ) from exc
        except Exception as exc:  # pragma: no cover - external client errors vary
            raise ExternalServiceError("OpenAI key verification failed.", details=str(exc)) from exc
        finally:
            await client.close()

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

    async def generate_markdown_reply(
        self,
        *,
        api_key: str,
        system_prompt: str,
        conversation_messages: list[dict[str, str]],
        additional_context: dict[str, object] | None = None,
    ) -> str:
        client = AsyncOpenAI(api_key=api_key, base_url=self.settings.openai_base_url)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if additional_context:
            messages.append(
                {
                    "role": "system",
                    "content": f"Additional context:\n{json.dumps(additional_context, ensure_ascii=False)}",
                }
            )
        messages.extend(conversation_messages)
        try:
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                temperature=0.2,
                messages=messages,
            )
        except Exception as exc:  # pragma: no cover - external client errors vary
            raise ExternalServiceError("OpenAI request failed.", details=str(exc)) from exc
        finally:
            await client.close()

        content = response.choices[0].message.content
        if not content:
            raise ExternalServiceError("OpenAI returned an empty response.")
        return content.strip()
