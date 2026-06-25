from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.chat import Chat
from src.database.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Chat, session)

    async def create(
        self,
        user_id: UUID,
        title: str,
        model: str,
    ) -> Chat:
        chat = Chat(user_id=user_id, title=title, model=model)
        return await self.save(chat)

    async def get_user_chats(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[Chat]:
        stmt = select(Chat).where(Chat.user_id == user_id)
        if not include_deleted:
            stmt = stmt.where(Chat.deleted_at.is_(None))
        stmt = stmt.order_by(Chat.updated_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, chat: Chat) -> Chat:
        return await self.save(chat)

    async def soft_delete(self, chat: Chat) -> Chat:
        chat.deleted_at = datetime.now(UTC)
        return await self.save(chat)
