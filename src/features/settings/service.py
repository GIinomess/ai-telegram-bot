from __future__ import annotations

from uuid import UUID

from src.config.constants import (
    DEFAULT_CONTEXT_ENABLED,
    DEFAULT_CONVERSATION_STYLE,
    DEFAULT_CREATIVITY,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
)
from src.database.models.settings import Settings
from src.database.repositories.settings import SettingsRepository


class SettingsService:
    def __init__(self, settings_repo: SettingsRepository) -> None:
        self._settings_repo = settings_repo

    async def get_or_create(
        self, user_id: UUID, language: str = DEFAULT_LANGUAGE
    ) -> Settings:
        settings = await self._settings_repo.get_by_user_id(user_id)
        if settings is None:
            settings = await self._settings_repo.create(
                user_id=user_id, language=language
            )
        return settings

    async def update(self, settings: Settings) -> Settings:
        return await self._settings_repo.update(settings)

    async def reset(self, user_id: UUID) -> Settings:
        settings = await self.get_or_create(user_id)
        settings.default_model = DEFAULT_MODEL
        settings.conversation_style = DEFAULT_CONVERSATION_STYLE
        settings.creativity = DEFAULT_CREATIVITY
        settings.context_enabled = DEFAULT_CONTEXT_ENABLED
        return await self._settings_repo.update(settings)
