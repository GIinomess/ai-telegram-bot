from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

from src.features.subscriptions.service import SubscriptionService
from tests.conftest import make_subscription


def make_service(repo: AsyncMock, redis: AsyncMock) -> SubscriptionService:
    return SubscriptionService(subscription_repo=repo, redis=redis)


def make_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_active_by_user_id = AsyncMock()
    repo.create = AsyncMock()
    repo.activate = AsyncMock()
    repo.deactivate = AsyncMock()
    return repo


def make_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.incr = AsyncMock()
    redis.expire = AsyncMock()
    return redis


class TestIsPremium:
    async def test_returns_true_for_active_non_expired_subscription(self) -> None:
        user_id = uuid4()
        sub = make_subscription(user_id, status="active", days_until_expiry=10)
        repo = make_repo()
        repo.get_active_by_user_id.return_value = sub

        svc = make_service(repo, make_redis())
        assert await svc.is_premium(user_id) is True

    async def test_returns_false_when_no_subscription(self) -> None:
        user_id = uuid4()
        repo = make_repo()
        repo.get_active_by_user_id.return_value = None

        svc = make_service(repo, make_redis())
        assert await svc.is_premium(user_id) is False

    async def test_deactivates_and_returns_false_for_expired_subscription(self) -> None:
        user_id = uuid4()
        sub = make_subscription(user_id, status="active", days_until_expiry=-1)
        repo = make_repo()
        repo.get_active_by_user_id.return_value = sub
        repo.deactivate.return_value = sub

        svc = make_service(repo, make_redis())
        result = await svc.is_premium(user_id)

        assert result is False
        repo.deactivate.assert_awaited_once_with(sub)

    async def test_returns_false_when_expires_at_is_none(self) -> None:
        user_id = uuid4()
        sub = make_subscription(user_id, status="active")
        sub.expires_at = None
        repo = make_repo()
        repo.get_active_by_user_id.return_value = sub

        svc = make_service(repo, make_redis())
        assert await svc.is_premium(user_id) is True


class TestCheckDailyLimit:
    async def test_premium_user_always_passes(self) -> None:
        user_id = uuid4()
        sub = make_subscription(user_id, days_until_expiry=30)
        repo = make_repo()
        repo.get_active_by_user_id.return_value = sub
        redis = make_redis()
        redis.get.return_value = b"999"

        svc = make_service(repo, redis)
        assert await svc.check_daily_limit(user_id) is True

    async def test_free_user_passes_when_under_limit(self) -> None:
        user_id = uuid4()
        repo = make_repo()
        repo.get_active_by_user_id.return_value = None
        redis = make_redis()
        redis.get.return_value = b"5"

        svc = make_service(repo, redis)
        assert await svc.check_daily_limit(user_id) is True

    async def test_free_user_blocked_when_at_limit(self) -> None:
        user_id = uuid4()
        repo = make_repo()
        repo.get_active_by_user_id.return_value = None
        redis = make_redis()
        redis.get.return_value = b"40"  # free_daily_limit default

        svc = make_service(repo, redis)
        assert await svc.check_daily_limit(user_id) is False


class TestIncrementUsage:
    async def test_increments_redis_counter_and_sets_expiry(self) -> None:
        user_id = uuid4()
        repo = make_repo()
        redis = make_redis()

        svc = make_service(repo, redis)
        await svc.increment_usage(user_id)

        redis.incr.assert_awaited_once()
        redis.expire.assert_awaited_once()

    async def test_uses_daily_key_with_user_id(self) -> None:
        user_id = uuid4()
        repo = make_repo()
        redis = make_redis()

        svc = make_service(repo, redis)
        await svc.increment_usage(user_id)

        key_arg = redis.incr.call_args[0][0]
        assert str(user_id) in key_arg
        assert "usage" in key_arg


class TestGetDailyUsage:
    async def test_returns_zero_when_no_redis_key(self) -> None:
        user_id = uuid4()
        redis = make_redis()
        redis.get.return_value = None

        svc = make_service(make_repo(), redis)
        assert await svc.get_daily_usage(user_id) == 0

    async def test_returns_count_from_redis(self) -> None:
        user_id = uuid4()
        redis = make_redis()
        redis.get.return_value = b"17"

        svc = make_service(make_repo(), redis)
        assert await svc.get_daily_usage(user_id) == 17
