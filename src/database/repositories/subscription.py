from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.subscription import Subscription
from src.database.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Subscription, session)

    async def create(
        self,
        user_id: UUID,
        plan: str,
        started_at: datetime,
        expires_at: datetime | None = None,
    ) -> Subscription:
        subscription = Subscription(
            user_id=user_id,
            plan=plan,
            status="inactive",
            started_at=started_at,
            expires_at=expires_at,
        )
        return await self.save(subscription)

    async def get_active_by_user_id(self, user_id: UUID) -> Subscription | None:
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == "active")
            .order_by(Subscription.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_subscriptions(self, user_id: UUID) -> list[Subscription]:
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def activate(self, subscription: Subscription) -> Subscription:
        subscription.status = "active"
        return await self.save(subscription)

    async def deactivate(self, subscription: Subscription) -> Subscription:
        subscription.status = "inactive"
        return await self.save(subscription)

    async def update(self, subscription: Subscription) -> Subscription:
        return await self.save(subscription)
