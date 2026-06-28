from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from src.providers.base import BaseProvider
from src.shared.exceptions import GeminiQuotaError, ProviderUnavailableError

logger = structlog.get_logger(__name__)

# Output token pricing in USD per token (Google pricing as of 2025)
_COST_PER_TOKEN: dict[str, float] = {
    "gemini-1.5-flash": 0.30 / 1_000_000,
    "gemini-1.5-pro": 5.00 / 1_000_000,
    "gemini-2.0-flash": 0.40 / 1_000_000,
    "gemini-2.5-flash-lite": 0.10 / 1_000_000,
    "gemini-2.5-flash": 0.30 / 1_000_000,
}

_DEFAULT_GEMINI_COST_MODEL = "gemini-2.5-flash-lite"


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
    ) -> str:
        contents, system_instruction = self._convert_messages(messages)
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            return response.text or ""
        except genai_errors.ClientError as e:
            if e.code == 429 or "RESOURCE_EXHAUSTED" in (e.status or ""):
                logger.warning("gemini_quota_exceeded", model=model, error=str(e))
                raise GeminiQuotaError("Gemini quota exceeded") from e
            logger.error("gemini_api_error", model=model, error=str(e))
            raise ProviderUnavailableError(f"Gemini error: {e}") from e
        except Exception as e:
            logger.error("gemini_api_error", model=model, error=str(e))
            raise ProviderUnavailableError(f"Gemini error: {e}") from e

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        return self._stream_chunks(messages, model, temperature)

    async def _stream_chunks(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        contents, system_instruction = self._convert_messages(messages)
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
        )
        try:
            # generate_content_stream is a coroutine returning an AsyncIterator
            stream = await self._client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except genai_errors.ClientError as e:
            if e.code == 429 or "RESOURCE_EXHAUSTED" in (e.status or ""):
                logger.warning(
                    "gemini_quota_exceeded_stream", model=model, error=str(e)
                )
                raise GeminiQuotaError("Gemini quota exceeded") from e
            logger.error("gemini_stream_error", model=model, error=str(e))
            raise ProviderUnavailableError(f"Gemini stream error: {e}") from e
        except Exception as e:
            logger.error("gemini_stream_error", model=model, error=str(e))
            raise ProviderUnavailableError(f"Gemini stream error: {e}") from e

    async def count_tokens(self, text: str, model: str) -> int:
        try:
            result = await self._client.aio.models.count_tokens(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=text)],
                    )
                ],
            )
            return result.total_tokens or 0
        except Exception:
            # Fall back to character-based approximation if API call fails
            return max(1, len(text) // 4)

    def estimate_cost(self, token_count: int, model: str) -> float:
        rate = _COST_PER_TOKEN.get(model, _COST_PER_TOKEN[_DEFAULT_GEMINI_COST_MODEL])
        return round(token_count * rate, 8)

    def _convert_messages(
        self,
        messages: list[dict[str, str]],
    ) -> tuple[list[types.Content], str | None]:
        system_instruction: str | None = None
        contents: list[types.Content] = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_instruction = content
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part(text=content)],
                    )
                )
        return contents, system_instruction
