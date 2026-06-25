from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.payment import Payment
from src.database.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Payment, session)

    async def create(
        self,
        user_id: UUID,
        subscription_id: UUID,
        telegram_payment_id: str,
        amount: int,
        currency: str,
        status: str,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            telegram_payment_id=telegram_payment_id,
            amount=amount,
            currency=currency,
            status=status,
        )
        return await self.save(payment)

    async def get_by_telegram_payment_id(
        self, telegram_payment_id: str
    ) -> Payment | None:
        stmt = select(Payment).where(Payment.telegram_payment_id == telegram_payment_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_payments(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, payment: Payment) -> Payment:
        return await self.save(payment)
