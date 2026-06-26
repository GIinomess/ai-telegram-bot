from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.config.constants import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from src.services.localization import LocalizationService


def _detect_language(telegram_lang: str | None) -> str:
    if not telegram_lang:
        return DEFAULT_LANGUAGE
    code = telegram_lang.lower().split("-")[0]
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


class LocalizationMiddleware(BaseMiddleware):
    def __init__(self, localization: LocalizationService) -> None:
        self._localization = localization

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        event_user = data.get("event_from_user")
        telegram_lang: str | None = getattr(event_user, "language_code", None)

        data["language"] = _detect_language(telegram_lang)
        data["localization"] = self._localization

        return await handler(event, data)
