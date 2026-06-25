from __future__ import annotations

from src.config.constants import DEFAULT_LANGUAGE
from src.database.models.message import Message
from src.database.models.settings import Settings


class PromptService:
    def build_system_prompt(self, settings: Settings) -> str:
        parts: list[str] = []
        if settings.language != DEFAULT_LANGUAGE:
            parts.append(
                f"Always reply in the following language: {settings.language}."
            )
        style_map = {
            "balanced": "Be helpful, accurate, and balanced in your responses.",
            "creative": "Be creative, imaginative, and think outside the box.",
            "precise": "Be precise, concise, and factual in your responses.",
        }
        instruction = style_map.get(settings.conversation_style, style_map["balanced"])
        parts.append(instruction)
        return " ".join(parts)

    def build_messages(
        self,
        system_prompt: str,
        history: list[Message],
        user_message: str,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})
        return messages
