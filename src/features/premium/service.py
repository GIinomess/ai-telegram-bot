from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis.asyncio import Redis

from src.config.constants import PLAN_DURATIONS
from src.config.settings import settings as app_settings
from src.database.models.subscription import Subscription
from src.database.repositories.subscription import SubscriptionRepository


class SubscriptionService:
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        redis: Redis,
    ) -> None:
        self._subscription_repo = subscription_repo
        self._redis = redis

    async def is_premium(self, user_id: UUID) -> bool:
        subscription = await self._subscription_repo.get_active_by_user_id(user_id)
        if subscription is None:
            return False
        if (
            subscription.expires_at is not None
            and subscription.expires_at < datetime.now(UTC)
        ):
            await self._subscription_repo.deactivate(subscription)
            return False
        return True

    async def get_active_subscription(self, user_id: UUID) -> Subscription | None:
        return await self._subscription_repo.get_active_by_user_id(user_id)

    async def activate(
        self,
        user_id: UUID,
        plan: str,
        started_at: datetime,
        expires_at: datetime | None = None,
    ) -> Subscription:
        if expires_at is None:
            days = PLAN_DURATIONS.get(plan, 30)
            expires_at = started_at + timedelta(days=days)
        subscription = await self._subscription_repo.create(
            user_id=user_id,
            plan=plan,
            started_at=started_at,
            expires_at=expires_at,
        )
        return await self._subscription_repo.activate(subscription)

    async def deactivate(self, subscription: Subscription) -> Subscription:
        return await self._subscription_repo.deactivate(subscription)

    async def check_daily_limit(self, user_id: UUID) -> bool:
        if await self.is_premium(user_id):
            return True
        usage = await self.get_daily_usage(user_id)
        return usage < app_settings.free_daily_limit

    async def increment_usage(self, user_id: UUID) -> None:
        key = self._daily_key(user_id)
        await self._redis.incr(key)
        now = datetime.now(UTC)
        tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        ttl = int((tomorrow - now).total_seconds())
        await self._redis.expire(key, ttl)

    async def get_daily_usage(self, user_id: UUID) -> int:
        key = self._daily_key(user_id)
        raw = await self._redis.get(key)
        if raw is None:
            return 0
        return int(raw.decode() if isinstance(raw, bytes) else raw)

    def _daily_key(self, user_id: UUID) -> str:
        date = datetime.now(UTC).strftime("%Y-%m-%d")
        return f"usage:{user_id}:{date}"
