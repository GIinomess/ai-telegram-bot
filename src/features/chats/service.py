from __future__ import annotations

from uuid import UUID

from src.config.constants import CHAT_TITLE_MAX_LENGTH
from src.database.models.chat import Chat
from src.database.repositories.chat import ChatRepository
from src.database.repositories.message import MessageRepository
from src.services.context import ContextService


class ChatService:
    def __init__(
        self,
        chat_repo: ChatRepository,
        message_repo: MessageRepository,
        context_service: ContextService,
    ) -> None:
        self._chat_repo = chat_repo
        self._message_repo = message_repo
        self._context_service = context_service

    async def create(self, user_id: UUID, model: str) -> Chat:
        return await self._chat_repo.create(
            user_id=user_id, title="New Chat", model=model
        )

    async def get_by_id(self, chat_id: UUID) -> Chat | None:
        return await self._chat_repo.get_by_id(chat_id)

    async def get_user_chats(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Chat]:
        return await self._chat_repo.get_user_chats(user_id, limit=limit, offset=offset)

    async def rename(self, chat: Chat, title: str) -> Chat:
        chat.title = title
        return await self._chat_repo.update(chat)

    async def rename_from_first_message(self, chat: Chat, message: str) -> Chat:
        title = message[:CHAT_TITLE_MAX_LENGTH].strip() or "New Chat"
        return await self.rename(chat, title)

    async def archive(self, chat: Chat) -> Chat:
        archived = await self._chat_repo.soft_delete(chat)
        await self._context_service.clear(chat.id)
        return archived

    async def delete(self, chat: Chat) -> None:
        await self._message_repo.delete_by_chat_id(chat.id)
        await self._context_service.clear(chat.id)
        await self._chat_repo.delete(chat)

    async def update_summary(self, chat: Chat, summary: str) -> Chat:
        return await self._context_service.save_summary(chat, summary)
