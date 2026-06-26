from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config.constants import FREE_MODELS, SUPPORTED_LANGUAGES
from src.database.models.settings import Settings
from src.services.localization import LocalizationService

# ── Callback data ──────────────────────────────────────────────────────────


class SettingsCallback(CallbackData, prefix="s"):
    action: str
    value: str = ""


# ── Display constants ──────────────────────────────────────────────────────

LANGUAGE_LABELS: dict[str, str] = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "uk": "🇺🇦 Українська",
    "cs": "🇨🇿 Čeština",
}

MODEL_LABELS: dict[str, str] = {
    "gpt-4o-mini": "GPT-4o mini",
    "gemini-2.0-flash": "Gemini 2.0 Flash",
}

STYLES: tuple[str, ...] = ("balanced", "creative", "precise")

CREATIVITY_VALUES: dict[str, float] = {
    "low": 0.3,
    "medium": 0.7,
    "high": 1.0,
}


def _creativity_level(creativity: float) -> str:
    v = round(creativity, 1)
    if v <= 0.3:
        return "low"
    if v <= 0.7:
        return "medium"
    return "high"


def _display_values(
    user_settings: Settings,
    localization: LocalizationService,
    language: str,
) -> tuple[str, str, str, str, str]:
    """Return (lang_label, model_label, style_label, cr_label, context_status)."""
    lang_label = LANGUAGE_LABELS.get(user_settings.language, user_settings.language)
    model_label = MODEL_LABELS.get(
        user_settings.default_model, user_settings.default_model
    )
    style_label = localization.get(
        f"settings.style.{user_settings.conversation_style}", language
    )
    cr_label = localization.get(
        f"settings.creativity.{_creativity_level(user_settings.creativity)}", language
    )
    if user_settings.context_enabled:
        status_key = "settings.context_on"
    else:
        status_key = "settings.context_off"
    context_status = localization.get(status_key, language)
    return lang_label, model_label, style_label, cr_label, context_status


# ── Text formatter ─────────────────────────────────────────────────────────


def settings_text(
    user_settings: Settings,
    localization: LocalizationService,
    language: str,
) -> str:
    lang_label, model_label, style_label, cr_label, status = _display_values(
        user_settings, localization, language
    )
    return "\n".join(
        [
            f"<b>{localization.get('settings.title', language)}</b>",
            "",
            localization.get("settings.current_model", language, model=model_label),
            localization.get(
                "settings.current_language", language, language=lang_label
            ),
            localization.get("settings.current_style", language, style=style_label),
            localization.get("settings.current_creativity", language, level=cr_label),
            localization.get("settings.current_context", language, status=status),
        ]
    )


# ── Keyboard builders ──────────────────────────────────────────────────────


def settings_keyboard(
    user_settings: Settings,
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    lang_label, model_label, style_label, cr_label, status = _display_values(
        user_settings, localization, language
    )
    builder = InlineKeyboardBuilder()
    builder.button(
        text=localization.get(
            "settings.current_language", language, language=lang_label
        ),
        callback_data=SettingsCallback(action="lang"),
    )
    builder.button(
        text=localization.get("settings.current_model", language, model=model_label),
        callback_data=SettingsCallback(action="model"),
    )
    builder.button(
        text=localization.get("settings.current_style", language, style=style_label),
        callback_data=SettingsCallback(action="style"),
    )
    builder.button(
        text=localization.get("settings.current_creativity", language, level=cr_label),
        callback_data=SettingsCallback(action="creativity"),
    )
    builder.button(
        text=localization.get("settings.current_context", language, status=status),
        callback_data=SettingsCallback(action="context"),
    )
    builder.button(
        text=localization.get("settings.reset", language),
        callback_data=SettingsCallback(action="reset"),
    )
    builder.adjust(1)
    return builder.as_markup()


def language_settings_keyboard(
    current: str,
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code in SUPPORTED_LANGUAGES:
        label = LANGUAGE_LABELS.get(code, code)
        if code == current:
            label = f"{label} ✓"
        builder.button(
            text=label,
            callback_data=SettingsCallback(action="set_lang", value=code),
        )
    builder.button(
        text=localization.get("common.back", language),
        callback_data=SettingsCallback(action="show"),
    )
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def model_keyboard(
    current: str,
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for model_id in FREE_MODELS:
        label = MODEL_LABELS.get(model_id, model_id)
        if model_id == current:
            label = f"{label} ✓"
        builder.button(
            text=label,
            callback_data=SettingsCallback(action="set_model", value=model_id),
        )
    builder.button(
        text=localization.get("common.back", language),
        callback_data=SettingsCallback(action="show"),
    )
    builder.adjust(1)
    return builder.as_markup()


def style_keyboard(
    current: str,
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for style in STYLES:
        label = localization.get(f"settings.style.{style}", language)
        if style == current:
            label = f"{label} ✓"
        builder.button(
            text=label,
            callback_data=SettingsCallback(action="set_style", value=style),
        )
    builder.button(
        text=localization.get("common.back", language),
        callback_data=SettingsCallback(action="show"),
    )
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def creativity_keyboard(
    current: float,
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    current_level = _creativity_level(current)
    for level in ("low", "medium", "high"):
        label = localization.get(f"settings.creativity.{level}", language)
        if level == current_level:
            label = f"{label} ✓"
        builder.button(
            text=label,
            callback_data=SettingsCallback(action="set_cr", value=level),
        )
    builder.button(
        text=localization.get("common.back", language),
        callback_data=SettingsCallback(action="show"),
    )
    builder.adjust(3, 1)
    return builder.as_markup()
