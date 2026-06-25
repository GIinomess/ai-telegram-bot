from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.settings import Settings
from src.database.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Settings, session)

    async def create(
        self,
        user_id: UUID,
        default_model: str = "gpt-4o-mini",
        language: str = "en",
        conversation_style: str = "balanced",
        creativity: float = 0.7,
        context_enabled: bool = True,
    ) -> Settings:
        settings = Settings(
            user_id=user_id,
            default_model=default_model,
            language=language,
            conversation_style=conversation_style,
            creativity=creativity,
            context_enabled=context_enabled,
        )
        return await self.save(settings)

    async def get_by_user_id(self, user_id: UUID) -> Settings | None:
        stmt = select(Settings).where(Settings.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, settings: Settings) -> Settings:
        return await self.save(settings)
