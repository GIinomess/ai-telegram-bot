from __future__ import annotations

from collections.abc import AsyncGenerator

import openai
import structlog
from openai import AsyncOpenAI

from src.providers.base import BaseProvider
from src.shared.exceptions import ProviderUnavailableError

logger = structlog.get_logger(__name__)

# Output token pricing in USD per token (OpenAI pricing as of 2025)
_COST_PER_TOKEN: dict[str, float] = {
    "gpt-4o-mini": 0.60 / 1_000_000,
    "gpt-4o": 10.00 / 1_000_000,
}


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except openai.RateLimitError as e:
            logger.warning("openai_rate_limit", model=model)
            raise ProviderUnavailableError("OpenAI rate limit reached") from e
        except openai.APIConnectionError as e:
            logger.error("openai_connection_error", model=model, error=str(e))
            raise ProviderUnavailableError("OpenAI connection failed") from e
        except openai.OpenAIError as e:
            logger.error("openai_api_error", model=model, error=str(e))
            raise ProviderUnavailableError(f"OpenAI error: {e}") from e

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
        try:
            openai_stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                stream=True,
            )
            async for chunk in openai_stream:  # type: ignore[union-attr]
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except openai.RateLimitError as e:
            logger.warning("openai_rate_limit_stream", model=model)
            raise ProviderUnavailableError("OpenAI rate limit reached") from e
        except openai.APIConnectionError as e:
            logger.error("openai_connection_error_stream", model=model, error=str(e))
            raise ProviderUnavailableError("OpenAI connection failed") from e
        except openai.OpenAIError as e:
            logger.error("openai_stream_error", model=model, error=str(e))
            raise ProviderUnavailableError(f"OpenAI stream error: {e}") from e

    async def count_tokens(self, text: str, model: str) -> int:
        # Approximation: ~4 characters per token on average
        return max(1, len(text) // 4)

    def estimate_cost(self, token_count: int, model: str) -> float:
        rate = _COST_PER_TOKEN.get(model, _COST_PER_TOKEN["gpt-4o-mini"])
        return round(token_count * rate, 8)
