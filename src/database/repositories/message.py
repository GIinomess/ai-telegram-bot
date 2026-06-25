from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.message import Message
from src.database.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Message, session)

    async def create(
        self,
        chat_id: UUID,
        role: str,
        content: str,
        token_count: int | None = None,
    ) -> Message:
        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            token_count=token_count,
        )
        return await self.save(message)

    async def get_chat_messages(
        self,
        chat_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_chat_id(self, chat_id: UUID) -> None:
        stmt = delete(Message).where(Message.chat_id == chat_id)
        await self._session.execute(stmt)
        await self._session.flush()
