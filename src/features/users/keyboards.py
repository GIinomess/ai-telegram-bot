from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class LanguageCallback(CallbackData, prefix="lang"):
    code: str


class StartCallback(CallbackData, prefix="onboard"):
    action: str


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


def start_screen_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 START", callback_data=StartCallback(action="go"))
    return builder.as_markup()


MENU_BUTTONS: frozenset[str] = frozenset(
    {
        "📝 Выбрать модель",
        "🎨 Создать картинку",
        "🔎 Интернет-поиск",
        "🎬 Создать видео",
        "📄 Документ",
        "🎸 Создать песню",
        "🚀 Премиум",
        "👤 Мой профиль",
    }
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Выбрать модель"),
                KeyboardButton(text="🎨 Создать картинку"),
            ],
            [
                KeyboardButton(text="🔎 Интернет-поиск"),
                KeyboardButton(text="🎬 Создать видео"),
            ],
            [
                KeyboardButton(text="📄 Документ"),
                KeyboardButton(text="🎸 Создать песню"),
            ],
            [
                KeyboardButton(text="🚀 Премиум"),
                KeyboardButton(text="👤 Мой профиль"),
            ],
        ],
        resize_keyboard=True,
    )
