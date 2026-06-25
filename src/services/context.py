from __future__ import annotations

from uuid import UUID

from src.config.constants import CONTEXT_MESSAGE_LIMIT, CONTEXT_SUMMARY_THRESHOLD
from src.database.models.chat import Chat
from src.database.models.message import Message
from src.database.repositories.chat import ChatRepository
from src.database.repositories.message import MessageRepository


class ContextService:
    def __init__(
        self,
        message_repo: MessageRepository,
        chat_repo: ChatRepository,
    ) -> None:
        self._message_repo = message_repo
        self._chat_repo = chat_repo

    async def load_context(self, chat: Chat) -> list[Message]:
        if not chat.context_enabled:
            return []
        return await self._message_repo.get_chat_messages(
            chat.id, limit=CONTEXT_MESSAGE_LIMIT
        )

    async def needs_summarization(
        self,
        chat_id: UUID,
        threshold: int = CONTEXT_SUMMARY_THRESHOLD,
    ) -> bool:
        messages = await self._message_repo.get_chat_messages(chat_id, limit=200)
        total_tokens = sum(m.token_count or 0 for m in messages)
        return total_tokens > threshold

    async def save_summary(self, chat: Chat, summary: str) -> Chat:
        chat.summary = summary
        return await self._chat_repo.update(chat)

    async def clear(self, chat_id: UUID) -> None:
        pass  # Placeholder for future Redis context cache invalidation
