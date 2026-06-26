from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database.repositories.chat import ChatRepository
from src.database.repositories.message import MessageRepository
from src.database.repositories.payment import PaymentRepository
from src.database.repositories.settings import SettingsRepository
from src.database.repositories.subscription import SubscriptionRepository
from src.database.repositories.user import UserRepository
from src.features.chats.service import ChatService
from src.features.payments.service import PaymentService
from src.features.settings.service import SettingsService
from src.features.subscriptions.service import SubscriptionService
from src.features.users.service import UserService
from src.providers.base import BaseProvider
from src.services.ai import AIService
from src.services.context import ContextService
from src.services.model import ModelService
from src.services.prompt import PromptService

logger = structlog.get_logger(__name__)


class DIMiddleware(BaseMiddleware):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        redis: Redis,
        providers: dict[str, BaseProvider],
    ) -> None:
        self._session_factory = session_factory
        self._redis = redis
        self._providers = providers
        # Stateless — create once, reuse per request
        self._prompt_service = PromptService()
        self._model_service = ModelService()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            chat_repo = ChatRepository(session)
            message_repo = MessageRepository(session)
            settings_repo = SettingsRepository(session)
            subscription_repo = SubscriptionRepository(session)
            payment_repo = PaymentRepository(session)

            settings_service = SettingsService(settings_repo)
            subscription_service = SubscriptionService(subscription_repo, self._redis)
            context_service = ContextService(message_repo, chat_repo)

            data["session"] = session
            data["user_service"] = UserService(user_repo, settings_service)
            data["chat_service"] = ChatService(chat_repo, message_repo, context_service)
            data["ai_service"] = AIService(
                message_repo=message_repo,
                context_service=context_service,
                prompt_service=self._prompt_service,
                model_service=self._model_service,
                subscription_service=subscription_service,
                providers=self._providers,
            )
            data["settings_service"] = settings_service
            data["subscription_service"] = subscription_service
            data["payment_service"] = PaymentService(payment_repo, subscription_service)

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
