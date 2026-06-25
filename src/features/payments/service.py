from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.config.settings import settings as app_settings
from src.database.models.payment import Payment
from src.database.repositories.payment import PaymentRepository
from src.features.premium.service import SubscriptionService


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        subscription_service: SubscriptionService,
    ) -> None:
        self._payment_repo = payment_repo
        self._subscription_service = subscription_service

    async def create_invoice(self, plan: str) -> dict[str, object]:
        price = self._get_plan_price(plan)
        return {
            "title": f"Premium — {plan.capitalize()}",
            "description": f"AI Bot Premium subscription ({plan})",
            "currency": "XTR",
            "price": price,
        }

    async def process_successful_payment(
        self,
        user_id: UUID,
        plan: str,
        telegram_payment_id: str,
        amount: int,
        currency: str,
    ) -> Payment:
        now = datetime.now(UTC)
        subscription = await self._subscription_service.activate(
            user_id=user_id,
            plan=plan,
            started_at=now,
        )
        return await self._payment_repo.create(
            user_id=user_id,
            subscription_id=subscription.id,
            telegram_payment_id=telegram_payment_id,
            amount=amount,
            currency=currency,
            status="completed",
        )

    async def get_user_payments(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Payment]:
        return await self._payment_repo.get_user_payments(
            user_id, limit=limit, offset=offset
        )

    def _get_plan_price(self, plan: str) -> int:
        prices: dict[str, int] = {
            "monthly": app_settings.premium_monthly_stars,
            "quarterly": app_settings.premium_quarterly_stars,
            "yearly": app_settings.premium_yearly_stars,
        }
        return prices.get(plan, 0)
