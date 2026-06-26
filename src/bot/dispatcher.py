from __future__ import annotations

from aiogram import Dispatcher
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.bot.middlewares import (
    DIMiddleware,
    ErrorMiddleware,
    LocalizationMiddleware,
    LoggingMiddleware,
)
from src.bot.routers import main_router
from src.providers.base import BaseProvider
from src.services.localization import LocalizationService


def create_dispatcher(
    session_factory: async_sessionmaker[AsyncSession],
    redis: Redis,
    providers: dict[str, BaseProvider],
    localization: LocalizationService,
) -> Dispatcher:
    dp = Dispatcher()

    # Outer middlewares — first registered is outermost (wraps everything below it)
    dp.update.outer_middleware(ErrorMiddleware())
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(LocalizationMiddleware(localization))
    dp.update.outer_middleware(DIMiddleware(session_factory, redis, providers))

    dp.include_router(main_router)

    return dp
