from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.localization import LocalizationService


class LanguageCallback(CallbackData, prefix="lang"):
    code: str


class StartCallback(CallbackData, prefix="onboard"):
    action: str


class ImageCallback(CallbackData, prefix="img"):
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


def image_prompt_keyboard(
    localization: LocalizationService, language: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=localization.get("image.cancel", language),
        callback_data=ImageCallback(action="cancel"),
    )
    return builder.as_markup()


def image_after_keyboard(
    localization: LocalizationService, language: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=localization.get("image.create_another", language),
        callback_data=ImageCallback(action="create_another"),
    )
    return builder.as_markup()


MENU_BUTTONS: frozenset[str] = frozenset(
    {
        "🔎 Интернет-поиск",
        "🎬 Создать видео",
        "📄 Документ",
    }
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Выбрать модель"),
                KeyboardButton(text="💻 Разработка"),
            ],
            [
                KeyboardButton(text="🎨 Создать картинку"),
                KeyboardButton(text="🔎 Интернет-поиск"),
            ],
            [
                KeyboardButton(text="🎬 Создать видео"),
                KeyboardButton(text="📄 Документ"),
            ],
            [
                KeyboardButton(text="🚀 Премиум"),
                KeyboardButton(text="👤 Мой профиль"),
            ],
        ],
        resize_keyboard=True,
    )
