from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

from src.config.constants import (
    DEFAULT_CONTEXT_ENABLED,
    DEFAULT_CONVERSATION_STYLE,
    DEFAULT_CREATIVITY,
    DEFAULT_MODEL,
)
from src.features.settings.service import SettingsService
from tests.conftest import make_settings


def make_service(repo: AsyncMock) -> SettingsService:
    return SettingsService(settings_repo=repo)


def make_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_user_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    return repo


class TestGetOrCreate:
    async def test_returns_existing_settings(self) -> None:
        user_id = uuid4()
        existing = make_settings(user_id)
        repo = make_repo()
        repo.get_by_user_id.return_value = existing

        svc = make_service(repo)
        result = await svc.get_or_create(user_id)

        repo.get_by_user_id.assert_awaited_once_with(user_id)
        repo.create.assert_not_awaited()
        assert result is existing

    async def test_creates_settings_when_none_exist(self) -> None:
        user_id = uuid4()
        new_settings = make_settings(user_id)
        repo = make_repo()
        repo.get_by_user_id.return_value = None
        repo.create.return_value = new_settings

        svc = make_service(repo)
        result = await svc.get_or_create(user_id, language="ru")

        repo.create.assert_awaited_once_with(user_id=user_id, language="ru")
        assert result is new_settings


class TestUpdate:
    async def test_delegates_to_repo(self) -> None:
        user_id = uuid4()
        settings = make_settings(user_id)
        repo = make_repo()
        repo.update.return_value = settings

        svc = make_service(repo)
        result = await svc.update(settings)

        repo.update.assert_awaited_once_with(settings)
        assert result is settings


class TestReset:
    async def test_resets_all_fields_to_defaults(self) -> None:
        user_id = uuid4()
        settings = make_settings(user_id)
        settings.default_model = "some-other-model"
        settings.conversation_style = "creative"
        settings.creativity = 1.0
        settings.context_enabled = False

        repo = make_repo()
        repo.get_by_user_id.return_value = settings
        repo.update.return_value = settings

        svc = make_service(repo)
        await svc.reset(user_id)

        assert settings.default_model == DEFAULT_MODEL
        assert settings.conversation_style == DEFAULT_CONVERSATION_STYLE
        assert settings.creativity == DEFAULT_CREATIVITY
        assert settings.context_enabled == DEFAULT_CONTEXT_ENABLED
        repo.update.assert_awaited_once()
