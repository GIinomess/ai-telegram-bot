from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class LanguageCallback(CallbackData, prefix="lang"):
    code: str


_LANGUAGE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("🇬🇧 English", "en"),
    ("🇷🇺 Русский", "ru"),
    ("🇺🇦 Українська", "uk"),
    ("🇨🇿 Čeština", "cs"),
)


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, code in _LANGUAGE_OPTIONS:
        builder.button(text=label, callback_data=LanguageCallback(code=code))
    builder.adjust(2)
    return builder.as_markup()
