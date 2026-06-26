from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.database.models.settings import Settings
from src.database.models.user import User
from src.features.chats.service import ChatService
from src.features.settings.keyboards import (
    CREATIVITY_VALUES,
    SettingsCallback,
    chats_list_for_model_keyboard,
    creativity_keyboard,
    language_settings_keyboard,
    model_keyboard,
    settings_keyboard,
    settings_text,
    style_keyboard,
)
from src.features.settings.service import SettingsService
from src.features.users.service import UserService
from src.services.localization import LocalizationService

router = Router(name="settings")


async def _get_user_settings(
    telegram_id: int,
    user_service: UserService,
    settings_service: SettingsService,
) -> tuple[User, Settings] | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    if user is None:
        return None
    user_settings = await settings_service.get_or_create(user.id)
    return user, user_settings


@router.message(Command("settings"))
async def cmd_settings(
    message: Message,
    user_service: UserService,
    settings_service: SettingsService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None:
        return

    result = await _get_user_settings(
        message.from_user.id, user_service, settings_service
    )
    if result is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return
    _, user_settings = result

    lang = user_settings.language
    await message.answer(
        settings_text(user_settings, localization, lang),
        reply_markup=settings_keyboard(user_settings, localization, lang),
    )


@router.callback_query(SettingsCallback.filter(F.action == "show"))
async def cb_settings_show(
    callback: CallbackQuery,
    user_service: UserService,
    settings_service: SettingsService,
    localization: LocalizationService,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_settings(
        callback.from_user.id, user_service, settings_service
    )
    if result is None:
        await callback.answer()
        return
    _, user_settings = result

    lang = user_settings.language
    await callback.message.edit_text(
        settings_text(user_settings, localization, lang),
        reply_markup=settings_keyboard(user_settings, localization, lang),
    )
    await callback.answer()


@router.callback_query(SettingsCallback.filter(F.action == "chat_list"))
async def cb_model_chat_list(
    callback: CallbackQuery,
    user_service: UserService,
    settings_service: SettingsService,
    chat_service: ChatService,
    localization: LocalizationService,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_settings(
        callback.from_user.id, user_service, settings_service
    )
    if result is None:
        await callback.answer()
        return
    user, user_settings = result
    lang = user_settings.language

    chats = await chat_service.get_user_chats(user.id)
    header = f"📂 <b>{localization.get('history.title', lang)}</b>"
    text = (
        f"{header}\n\n{localization.get('history.empty', lang)}"
        if not chats
        else header
    )

    await callback.message.edit_text(
        text,
        reply_markup=chats_list_for_model_keyboard(chats, localization, lang),
    )
    await callback.answer()


@router.callback_query(
    SettingsCallback.filter(F.action.in_({"lang", "model", "style", "creativity"}))
)
async def cb_settings_navigate(
    callback: CallbackQuery,
    callback_data: SettingsCallback,
    user_service: UserService,
    settings_service: SettingsService,
    localization: LocalizationService,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_settings(
        callback.from_user.id, user_service, settings_service
    )
    if result is None:
        await callback.answer()
        return
    _, user_settings = result
    lang = user_settings.language

    if callback_data.action == "lang":
        text = localization.get("settings.choose_language", lang)
        keyboard = language_settings_keyboard(
            user_settings.language, localization, lang
        )
    elif callback_data.action == "model":
        text = localization.get("settings.choose_model", lang)
        keyboard = model_keyboard(user_settings.default_model, localization, lang)
    elif callback_data.action == "style":
        text = localization.get("settings.choose_style", lang)
        keyboard = style_keyboard(user_settings.conversation_style, localization, lang)
    else:  # creativity
        text = localization.get("settings.choose_creativity", lang)
        keyboard = creativity_keyboard(user_settings.creativity, localization, lang)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(
    SettingsCallback.filter(
        F.action.in_({"set_lang", "set_model", "set_style", "set_cr"})
    )
)
async def cb_settings_set(
    callback: CallbackQuery,
    callback_data: SettingsCallback,
    user_service: UserService,
    settings_service: SettingsService,
    localization: LocalizationService,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_settings(
        callback.from_user.id, user_service, settings_service
    )
    if result is None:
        await callback.answer()
        return
    user, user_settings = result

    if callback_data.action == "set_lang":
        user_settings.language = callback_data.value
        user.language = callback_data.value
        await user_service.update(user)
    elif callback_data.action == "set_model":
        user_settings.default_model = callback_data.value
    elif callback_data.action == "set_style":
        user_settings.conversation_style = callback_data.value
    else:  # set_cr
        user_settings.creativity = CREATIVITY_VALUES.get(callback_data.value, 0.7)

    updated = await settings_service.update(user_settings)
    lang = updated.language

    await callback.message.edit_text(
        settings_text(updated, localization, lang),
        reply_markup=settings_keyboard(updated, localization, lang),
    )
    await callback.answer(localization.get("settings.saved", lang))


@router.callback_query(SettingsCallback.filter(F.action == "context"))
async def cb_settings_context(
    callback: CallbackQuery,
    user_service: UserService,
    settings_service: SettingsService,
    localization: LocalizationService,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_settings(
        callback.from_user.id, user_service, settings_service
    )
    if result is None:
        await callback.answer()
        return
    _, user_settings = result

    user_settings.context_enabled = not user_settings.context_enabled
    updated = await settings_service.update(user_settings)
    lang = updated.language

    await callback.message.edit_text(
        settings_text(updated, localization, lang),
        reply_markup=settings_keyboard(updated, localization, lang),
    )
    await callback.answer(localization.get("settings.saved", lang))


@router.callback_query(SettingsCallback.filter(F.action == "reset"))
async def cb_settings_reset(
    callback: CallbackQuery,
    user_service: UserService,
    settings_service: SettingsService,
    localization: LocalizationService,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_settings(
        callback.from_user.id, user_service, settings_service
    )
    if result is None:
        await callback.answer()
        return
    _, user_settings = result

    reset = await settings_service.reset(user_settings.user_id)
    lang = reset.language

    await callback.message.edit_text(
        settings_text(reset, localization, lang),
        reply_markup=settings_keyboard(reset, localization, lang),
    )
    await callback.answer(localization.get("settings.reset_done", lang))
