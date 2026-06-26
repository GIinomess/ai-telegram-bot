from __future__ import annotations

from unittest.mock import AsyncMock

from src.features.users.service import UserService
from tests.conftest import make_user


def make_service(user_repo: AsyncMock, settings_service: AsyncMock) -> UserService:
    return UserService(user_repo=user_repo, settings_service=settings_service)


def make_repos() -> tuple[AsyncMock, AsyncMock]:
    user_repo = AsyncMock()
    user_repo.get_by_telegram_id = AsyncMock()
    user_repo.get_by_id = AsyncMock()
    user_repo.create = AsyncMock()
    user_repo.update = AsyncMock()

    settings_service = AsyncMock()
    settings_service.get_or_create = AsyncMock()

    return user_repo, settings_service


class TestGetOrCreate:
    async def test_returns_existing_user_without_creating(self) -> None:
        user = make_user(telegram_id=123)
        user_repo, settings_service = make_repos()
        user_repo.get_by_telegram_id.return_value = user

        svc = make_service(user_repo, settings_service)
        result = await svc.get_or_create(
            telegram_id=123, first_name="Test", language="en"
        )

        user_repo.create.assert_not_awaited()
        settings_service.get_or_create.assert_not_awaited()
        assert result is user

    async def test_creates_user_and_settings_when_new(self) -> None:
        user = make_user(telegram_id=456)
        user_repo, settings_service = make_repos()
        user_repo.get_by_telegram_id.return_value = None
        user_repo.create.return_value = user
        settings_service.get_or_create.return_value = AsyncMock()

        svc = make_service(user_repo, settings_service)
        result = await svc.get_or_create(
            telegram_id=456, first_name="New", language="ru"
        )

        user_repo.create.assert_awaited_once()
        settings_service.get_or_create.assert_awaited_once_with(user.id, language="ru")
        assert result is user

    async def test_creates_user_with_correct_fields(self) -> None:
        user = make_user(telegram_id=789)
        user_repo, settings_service = make_repos()
        user_repo.get_by_telegram_id.return_value = None
        user_repo.create.return_value = user
        settings_service.get_or_create.return_value = AsyncMock()

        svc = make_service(user_repo, settings_service)
        await svc.get_or_create(
            telegram_id=789,
            first_name="Alice",
            username="alice",
            last_name="Smith",
            language="uk",
        )

        user_repo.create.assert_awaited_once_with(
            telegram_id=789,
            first_name="Alice",
            username="alice",
            last_name="Smith",
            language="uk",
        )


class TestGetByTelegramId:
    async def test_delegates_to_repo(self) -> None:
        user = make_user(telegram_id=111)
        user_repo, settings_service = make_repos()
        user_repo.get_by_telegram_id.return_value = user

        svc = make_service(user_repo, settings_service)
        result = await svc.get_by_telegram_id(111)

        user_repo.get_by_telegram_id.assert_awaited_once_with(111)
        assert result is user

    async def test_returns_none_when_not_found(self) -> None:
        user_repo, settings_service = make_repos()
        user_repo.get_by_telegram_id.return_value = None

        svc = make_service(user_repo, settings_service)
        result = await svc.get_by_telegram_id(999)

        assert result is None


class TestUpdate:
    async def test_delegates_to_repo(self) -> None:
        user = make_user()
        user_repo, settings_service = make_repos()
        user_repo.update.return_value = user

        svc = make_service(user_repo, settings_service)
        result = await svc.update(user)

        user_repo.update.assert_awaited_once_with(user)
        assert result is user
