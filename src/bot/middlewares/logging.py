from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        event_user = data.get("event_from_user")
        user_id: int | None = getattr(event_user, "id", None)
        update_type = type(event).__name__

        logger.info("update_received", update_type=update_type, user_id=user_id)
        start = time.monotonic()

        result = await handler(event, data)

        logger.info(
            "update_processed",
            update_type=update_type,
            user_id=user_id,
            elapsed_ms=round((time.monotonic() - start) * 1000, 2),
        )
        return result
