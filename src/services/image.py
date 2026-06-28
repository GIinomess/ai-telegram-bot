from __future__ import annotations

from src.providers.openai import OpenAIProvider


class ImageService:
    def __init__(self, provider: OpenAIProvider) -> None:
        self._provider = provider

    async def generate(self, prompt: str) -> str | bytes:
        return await self._provider.generate_image(prompt)
