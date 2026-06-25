from __future__ import annotations

from uuid import UUID

from src.config.constants import DEFAULT_LANGUAGE
from src.database.models.user import User
from src.database.repositories.user import UserRepository
from src.features.settings.service import SettingsService


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        settings_service: SettingsService,
    ) -> None:
        self._user_repo = user_repo
        self._settings_service = settings_service

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str,
        username: str | None = None,
        last_name: str | None = None,
        language: str = DEFAULT_LANGUAGE,
    ) -> User:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self._user_repo.create(
                telegram_id=telegram_id,
                first_name=first_name,
                username=username,
                last_name=last_name,
                language=language,
            )
            await self._settings_service.get_or_create(user.id, language=language)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._user_repo.get_by_id(user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self._user_repo.get_by_telegram_id(telegram_id)

    async def update(self, user: User) -> User:
        return await self._user_repo.update(user)
