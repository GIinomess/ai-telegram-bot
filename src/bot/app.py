from __future__ import annotations

import structlog
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.dispatcher import create_dispatcher
from src.config.settings import settings
from src.core.redis import redis
from src.database.session import AsyncSessionFactory
from src.providers.base import BaseProvider
from src.providers.gemini import GeminiProvider
from src.providers.openai import OpenAIProvider
from src.services.localization import LocalizationService

logger = structlog.get_logger(__name__)


async def on_startup(bot: Bot) -> None:
    bot_info = await bot.get_me()
    logger.info("bot_started", bot_id=bot_info.id, username=bot_info.username)


async def on_shutdown(bot: Bot) -> None:
    logger.info("bot_stopped")


async def start_polling() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    providers: dict[str, BaseProvider] = {
        "openai": OpenAIProvider(api_key=settings.openai_api_key),
        "gemini": GeminiProvider(api_key=settings.gemini_api_key),
    }

    dp = create_dispatcher(
        session_factory=AsyncSessionFactory,
        redis=redis,
        providers=providers,
        localization=LocalizationService(),
    )

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
