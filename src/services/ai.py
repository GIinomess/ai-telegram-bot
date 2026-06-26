from __future__ import annotations

from collections.abc import AsyncGenerator

from src.database.models.chat import Chat
from src.database.models.message import Message
from src.database.models.settings import Settings
from src.database.models.user import User
from src.database.repositories.message import MessageRepository
from src.features.subscriptions.service import SubscriptionService
from src.providers.base import BaseProvider
from src.services.context import ContextService
from src.services.model import ModelService
from src.services.prompt import PromptService
from src.shared.exceptions import DailyLimitExceededError, ProviderUnavailableError


class AIService:
    def __init__(
        self,
        message_repo: MessageRepository,
        context_service: ContextService,
        prompt_service: PromptService,
        model_service: ModelService,
        subscription_service: SubscriptionService,
        providers: dict[str, BaseProvider],
    ) -> None:
        self._message_repo = message_repo
        self._context_service = context_service
        self._prompt_service = prompt_service
        self._model_service = model_service
        self._subscription_service = subscription_service
        self._providers = providers

    async def generate(
        self,
        user: User,
        chat: Chat,
        user_message: str,
        settings: Settings,
    ) -> str:
        if not await self._subscription_service.check_daily_limit(user.id):
            raise DailyLimitExceededError()

        await self._message_repo.create(chat.id, "user", user_message)

        context = await self._context_service.load_context(chat)

        if await self._context_service.needs_summarization(chat.id):
            await self._run_summarization(chat, context, settings)
            context = await self._context_service.load_context(chat)

        system_prompt = self._prompt_service.build_system_prompt(settings)
        messages = self._prompt_service.build_messages(
            system_prompt, context, user_message
        )

        provider = self._get_provider(chat.model)
        response = await provider.generate(
            messages, chat.model, temperature=settings.creativity
        )

        token_count = await provider.count_tokens(response, chat.model)
        await self._message_repo.create(chat.id, "assistant", response, token_count)
        await self._subscription_service.increment_usage(user.id)

        return response

    async def stream(
        self,
        user: User,
        chat: Chat,
        user_message: str,
        settings: Settings,
    ) -> AsyncGenerator[str, None]:
        if not await self._subscription_service.check_daily_limit(user.id):
            raise DailyLimitExceededError()

        await self._message_repo.create(chat.id, "user", user_message)

        context = await self._context_service.load_context(chat)

        if await self._context_service.needs_summarization(chat.id):
            await self._run_summarization(chat, context, settings)
            context = await self._context_service.load_context(chat)

        system_prompt = self._prompt_service.build_system_prompt(settings)
        messages = self._prompt_service.build_messages(
            system_prompt, context, user_message
        )

        provider = self._get_provider(chat.model)
        chunks: list[str] = []

        gen = await provider.stream(
            messages, chat.model, temperature=settings.creativity
        )
        async for chunk in gen:
            chunks.append(chunk)
            yield chunk

        full_response = "".join(chunks)
        token_count = await provider.count_tokens(full_response, chat.model)
        await self._message_repo.create(
            chat.id, "assistant", full_response, token_count
        )
        await self._subscription_service.increment_usage(user.id)

    def count_tokens_estimate(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, token_count: int, model: str) -> float:
        provider = self._get_provider(model)
        return provider.estimate_cost(token_count, model)

    def _get_provider(self, model: str) -> BaseProvider:
        provider_name = self._model_service.get_provider_name(model)
        provider = self._providers.get(provider_name)
        if provider is None:
            raise ProviderUnavailableError(
                f"Provider '{provider_name}' is not configured"
            )
        return provider

    async def _run_summarization(
        self,
        chat: Chat,
        context: list[Message],
        settings: Settings,
    ) -> None:
        if not context:
            return
        provider = self._get_provider(chat.model)
        history_text = "\n".join(f"{m.role}: {m.content}" for m in context)
        summary_prompt: list[dict[str, str]] = [
            {
                "role": "user",
                "content": f"Summarize this conversation concisely:\n\n{history_text}",
            }
        ]
        summary = await provider.generate(summary_prompt, chat.model, temperature=0.3)
        await self._context_service.save_summary(chat, summary)
