from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config.settings import settings as app_settings
from src.database.models.subscription import Subscription
from src.services.localization import LocalizationService


class PremiumCallback(CallbackData, prefix="pm"):
    action: str
    plan: str = ""


# ── Text formatter ─────────────────────────────────────────────────────────


def premium_text(
    subscription: Subscription | None,
    localization: LocalizationService,
    language: str,
) -> str:
    lines = [
        f"<b>{localization.get('premium.title', language)}</b>",
        "",
        localization.get("premium.description", language),
        "",
        localization.get("premium.features", language),
        "",
    ]
    if subscription is not None:
        lines.append(localization.get("premium.active", language))
        if subscription.expires_at is not None:
            date_str = subscription.expires_at.strftime("%Y-%m-%d")
            lines.append(localization.get("premium.expires", language, date=date_str))
    return "\n".join(lines)


# ── Keyboard builders ──────────────────────────────────────────────────────


def premium_keyboard(
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    plans = [
        (
            "monthly",
            localization.get(
                "premium.plan_monthly",
                language,
                price=app_settings.premium_monthly_stars,
            ),
        ),
        (
            "quarterly",
            localization.get(
                "premium.plan_quarterly",
                language,
                price=app_settings.premium_quarterly_stars,
            ),
        ),
        (
            "yearly",
            localization.get(
                "premium.plan_yearly",
                language,
                price=app_settings.premium_yearly_stars,
            ),
        ),
    ]
    for plan, label in plans:
        builder.button(
            text=label,
            callback_data=PremiumCallback(action="buy", plan=plan),
        )
    builder.adjust(1)
    return builder.as_markup()


def limit_reached_keyboard(
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=localization.get("menu.premium", language),
        callback_data=PremiumCallback(action="show"),
    )
    return builder.as_markup()
