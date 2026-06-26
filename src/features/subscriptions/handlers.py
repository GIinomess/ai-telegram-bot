from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from src.config.settings import settings as app_settings
from src.features.payments.service import PaymentService
from src.features.subscriptions.keyboards import (
    PremiumCallback,
    premium_keyboard,
    premium_text,
)
from src.features.subscriptions.service import SubscriptionService
from src.features.users.service import UserService
from src.services.localization import LocalizationService

logger = structlog.get_logger(__name__)

router = Router(name="subscriptions")

_PLAN_PRICES: dict[str, int] = {
    "monthly": app_settings.premium_monthly_stars,
    "quarterly": app_settings.premium_quarterly_stars,
    "yearly": app_settings.premium_yearly_stars,
}


# ── Premium screen ─────────────────────────────────────────────────────────


async def _show_premium(
    message: Message,
    user_service: UserService,
    subscription_service: SubscriptionService,
    localization: LocalizationService,
    language: str,
    *,
    edit: bool = False,
) -> None:
    if message.from_user is None:
        return

    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        return

    subscription = await subscription_service.get_active_subscription(user.id)
    lang = user.language if user else language

    text = premium_text(subscription, localization, lang)
    keyboard = premium_keyboard(localization, lang)

    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.message(Command("premium"))
async def cmd_premium(
    message: Message,
    user_service: UserService,
    subscription_service: SubscriptionService,
    localization: LocalizationService,
    language: str,
) -> None:
    await _show_premium(
        message, user_service, subscription_service, localization, language
    )


@router.callback_query(PremiumCallback.filter(F.action == "show"))
async def cb_premium_show(
    callback: CallbackQuery,
    user_service: UserService,
    subscription_service: SubscriptionService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    await _show_premium(
        callback.message,
        user_service,
        subscription_service,
        localization,
        language,
        edit=True,
    )
    await callback.answer()


# ── Invoice ────────────────────────────────────────────────────────────────


@router.callback_query(PremiumCallback.filter(F.action == "buy"))
async def cb_premium_buy(
    callback: CallbackQuery,
    callback_data: PremiumCallback,
    user_service: UserService,
    subscription_service: SubscriptionService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return
    if callback.message.bot is None:
        return

    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer()
        return

    lang = user.language if user else language
    plan = callback_data.plan

    if await subscription_service.is_premium(user.id):
        await callback.answer(
            localization.get("premium.already_active", lang), show_alert=True
        )
        return

    price = _PLAN_PRICES.get(plan, 0)
    if price == 0:
        await callback.answer()
        return

    plan_key = f"premium.plan_{plan}"
    plan_label = localization.get(plan_key, lang, price=price)

    await callback.message.bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=localization.get("premium.title", lang),
        description=localization.get("premium.description", lang),
        payload=f"premium:{plan}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=plan_label, amount=price)],
    )
    await callback.answer()


# ── Payment processing ─────────────────────────────────────────────────────


@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(
    message: Message,
    user_service: UserService,
    payment_service: PaymentService,
    subscription_service: SubscriptionService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None or message.successful_payment is None:
        return

    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return

    lang = user.language
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload  # "premium:{plan}"

    parts = payload.split(":")
    plan = parts[1] if len(parts) >= 2 else "monthly"

    try:
        await payment_service.process_successful_payment(
            user_id=user.id,
            plan=plan,
            telegram_payment_id=payment_info.telegram_payment_charge_id,
            amount=payment_info.total_amount,
            currency=payment_info.currency,
        )
        logger.info(
            "payment_processed",
            user_id=str(user.id),
            plan=plan,
            amount=payment_info.total_amount,
            currency=payment_info.currency,
        )
    except Exception:
        logger.exception("payment_processing_error", user_id=str(user.id), plan=plan)
        await message.answer(localization.get("errors.unknown", lang))
        return

    subscription = await subscription_service.get_active_subscription(user.id)
    text = (
        f"{localization.get('premium.payment_success', lang)}\n\n"
        f"{premium_text(subscription, localization, lang)}"
    )
    await message.answer(text)
