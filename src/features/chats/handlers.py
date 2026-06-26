from __future__ import annotations

import time
from uuid import UUID

import structlog
from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.config.constants import CHAT_TITLE_MAX_LENGTH
from src.config.settings import settings as app_settings
from src.database.models.chat import Chat
from src.database.models.settings import Settings
from src.database.models.user import User
from src.features.chats.keyboards import (
    ChatCallback,
    chat_delete_confirm_keyboard,
    chat_delete_confirm_text,
    chat_manage_keyboard,
    chat_manage_text,
    chat_open_keyboard,
    chat_open_text,
    chats_list_keyboard,
    chats_list_text,
)
from src.features.chats.service import ChatService
from src.features.settings.service import SettingsService
from src.features.subscriptions.keyboards import limit_reached_keyboard
from src.features.users.service import UserService
from src.services.ai import AIService
from src.services.localization import LocalizationService
from src.shared.exceptions import DailyLimitExceededError, ProviderUnavailableError

logger = structlog.get_logger(__name__)

_STREAM_EDIT_INTERVAL = 1.5  # seconds between Telegram message edits during stream

router = Router(name="chats")


class ChatStates(StatesGroup):
    active = State()
    waiting_rename = State()


# ── Helpers ────────────────────────────────────────────────────────────────


async def _get_user_and_settings(
    telegram_id: int,
    user_service: UserService,
    settings_service: SettingsService,
) -> tuple[User, Settings] | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    if user is None:
        return None
    user_settings = await settings_service.get_or_create(user.id)
    return user, user_settings


async def _get_user_and_chat(
    telegram_id: int,
    chat_id_str: str,
    user_service: UserService,
    chat_service: ChatService,
) -> tuple[User, Chat] | None:
    user = await user_service.get_by_telegram_id(telegram_id)
    if user is None:
        return None
    try:
        chat_id = UUID(chat_id_str)
    except ValueError:
        return None
    chat = await chat_service.get_by_id(chat_id)
    if chat is None or chat.user_id != user.id:
        return None
    return user, chat


# ── Command handlers ───────────────────────────────────────────────────────


@router.message(Command("new"))
async def cmd_new(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None:
        return

    result = await _get_user_and_settings(
        message.from_user.id, user_service, settings_service
    )
    if result is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return
    user, user_settings = result

    title = localization.get("chat.new_title", language)
    chat = await chat_service.create(user.id, user_settings.default_model, title=title)

    await state.set_state(ChatStates.active)
    await state.update_data(chat_id=str(chat.id), is_new=True)

    await message.answer(
        chat_open_text(chat, localization, language),
        reply_markup=chat_open_keyboard(localization, language),
    )


@router.message(Command("history"))
async def cmd_history(
    message: Message,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None:
        return

    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return

    chats = await chat_service.get_user_chats(user.id)
    await message.answer(
        chats_list_text(localization, language, is_empty=not chats),
        reply_markup=chats_list_keyboard(chats, localization, language),
    )


# ── Callback handlers ──────────────────────────────────────────────────────


@router.callback_query(ChatCallback.filter(F.action == "list"))
async def cb_chat_list(
    callback: CallbackQuery,
    state: FSMContext,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    await state.clear()

    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer()
        return

    chats = await chat_service.get_user_chats(user.id)
    await callback.message.edit_text(
        chats_list_text(localization, language, is_empty=not chats),
        reply_markup=chats_list_keyboard(chats, localization, language),
    )
    await callback.answer()


@router.callback_query(ChatCallback.filter(F.action == "new"))
async def cb_chat_new(
    callback: CallbackQuery,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_and_settings(
        callback.from_user.id, user_service, settings_service
    )
    if result is None:
        await callback.answer()
        return
    user, user_settings = result

    title = localization.get("chat.new_title", language)
    chat = await chat_service.create(user.id, user_settings.default_model, title=title)

    await state.set_state(ChatStates.active)
    await state.update_data(chat_id=str(chat.id), is_new=True)

    await callback.message.edit_text(
        chat_open_text(chat, localization, language),
        reply_markup=chat_open_keyboard(localization, language),
    )
    await callback.answer()


@router.callback_query(ChatCallback.filter(F.action == "open"))
async def cb_chat_open(
    callback: CallbackQuery,
    callback_data: ChatCallback,
    state: FSMContext,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_and_chat(
        callback.from_user.id, callback_data.chat_id, user_service, chat_service
    )
    if result is None:
        await callback.answer()
        return
    _, chat = result

    await state.set_state(ChatStates.active)
    await state.update_data(chat_id=str(chat.id), is_new=False)

    await callback.message.edit_text(
        chat_open_text(chat, localization, language),
        reply_markup=chat_open_keyboard(localization, language),
    )
    await callback.answer()


@router.callback_query(ChatCallback.filter(F.action == "manage"))
async def cb_chat_manage(
    callback: CallbackQuery,
    callback_data: ChatCallback,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_and_chat(
        callback.from_user.id, callback_data.chat_id, user_service, chat_service
    )
    if result is None:
        await callback.answer()
        return
    _, chat = result

    await callback.message.edit_text(
        chat_manage_text(chat),
        reply_markup=chat_manage_keyboard(str(chat.id), localization, language),
    )
    await callback.answer()


@router.callback_query(ChatCallback.filter(F.action == "rename"))
async def cb_chat_rename(
    callback: CallbackQuery,
    callback_data: ChatCallback,
    state: FSMContext,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_and_chat(
        callback.from_user.id, callback_data.chat_id, user_service, chat_service
    )
    if result is None:
        await callback.answer()
        return
    _, chat = result

    await state.set_state(ChatStates.waiting_rename)
    await state.update_data(chat_id=str(chat.id))

    await callback.message.edit_text(localization.get("history.enter_title", language))
    await callback.answer()


@router.callback_query(ChatCallback.filter(F.action == "archive"))
async def cb_chat_archive(
    callback: CallbackQuery,
    callback_data: ChatCallback,
    state: FSMContext,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_and_chat(
        callback.from_user.id, callback_data.chat_id, user_service, chat_service
    )
    if result is None:
        await callback.answer()
        return
    user, chat = result

    await chat_service.archive(chat)

    state_data = await state.get_data()
    if state_data.get("chat_id") == str(chat.id):
        await state.clear()

    chats = await chat_service.get_user_chats(user.id)
    await callback.message.edit_text(
        chats_list_text(localization, language, is_empty=not chats),
        reply_markup=chats_list_keyboard(chats, localization, language),
    )
    await callback.answer(localization.get("history.archived", language))


@router.callback_query(ChatCallback.filter(F.action == "del_ask"))
async def cb_chat_del_ask(
    callback: CallbackQuery,
    callback_data: ChatCallback,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_and_chat(
        callback.from_user.id, callback_data.chat_id, user_service, chat_service
    )
    if result is None:
        await callback.answer()
        return

    await callback.message.edit_text(
        chat_delete_confirm_text(localization, language),
        reply_markup=chat_delete_confirm_keyboard(
            callback_data.chat_id, localization, language
        ),
    )
    await callback.answer()


@router.callback_query(ChatCallback.filter(F.action == "delete"))
async def cb_chat_delete(
    callback: CallbackQuery,
    callback_data: ChatCallback,
    state: FSMContext,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if callback.from_user is None or not isinstance(callback.message, Message):
        return

    result = await _get_user_and_chat(
        callback.from_user.id, callback_data.chat_id, user_service, chat_service
    )
    if result is None:
        await callback.answer()
        return
    user, chat = result

    state_data = await state.get_data()
    if state_data.get("chat_id") == str(chat.id):
        await state.clear()

    await chat_service.delete(chat)

    chats = await chat_service.get_user_chats(user.id)
    await callback.message.edit_text(
        chats_list_text(localization, language, is_empty=not chats),
        reply_markup=chats_list_keyboard(chats, localization, language),
    )
    await callback.answer(localization.get("history.deleted", language))


# ── AI conversation handler ────────────────────────────────────────────────


async def _do_ai_stream(
    message: Message,
    state: FSMContext,
    user: User,
    chat: Chat,
    user_text: str,
    is_new: bool,
    user_settings: Settings,
    ai_service: AIService,
    chat_service: ChatService,
    localization: LocalizationService,
    lang: str,
) -> None:
    if message.bot:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    placeholder = await message.answer(localization.get("chat.generating", lang))

    accumulated = ""
    last_edit_at = time.monotonic()

    try:
        async for chunk in ai_service.stream(user, chat, user_text, user_settings):
            accumulated += chunk
            now = time.monotonic()
            if now - last_edit_at >= _STREAM_EDIT_INTERVAL and accumulated:
                try:
                    await placeholder.edit_text(accumulated)
                    last_edit_at = now
                except Exception:
                    pass
    except DailyLimitExceededError:
        limit = app_settings.free_daily_limit
        await placeholder.edit_text(
            localization.get("chat.limit_reached", lang, limit=limit),
            reply_markup=limit_reached_keyboard(localization, lang),
        )
        return
    except ProviderUnavailableError:
        await placeholder.edit_text(
            localization.get("errors.provider_unavailable", lang)
        )
        return
    except Exception:
        logger.exception("ai_stream_error", chat_id=str(chat.id))
        await placeholder.edit_text(localization.get("chat.error", lang))
        return

    if accumulated:
        try:
            await placeholder.edit_text(accumulated)
        except Exception:
            pass

    if is_new and accumulated:
        await chat_service.rename_from_first_message(chat, user_text)
        await state.update_data(is_new=False)


@router.message(ChatStates.active)
async def msg_chat_active(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    chat_service: ChatService,
    ai_service: AIService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None or not message.text:
        return

    user_text = message.text.strip()
    if not user_text:
        return

    data = await state.get_data()
    chat_id_str: str = data.get("chat_id") or ""
    is_new: bool = data.get("is_new", False)

    user_settings_result = await _get_user_and_settings(
        message.from_user.id, user_service, settings_service
    )
    if user_settings_result is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return
    user, user_settings = user_settings_result

    chat_result = await _get_user_and_chat(
        message.from_user.id, chat_id_str, user_service, chat_service
    )
    if chat_result is None:
        await message.answer(localization.get("errors.chat_not_found", language))
        return
    _, chat = chat_result

    await _do_ai_stream(
        message,
        state,
        user,
        chat,
        user_text,
        is_new,
        user_settings,
        ai_service,
        chat_service,
        localization,
        user_settings.language,
    )


# ── FSM message handler ────────────────────────────────────────────────────


@router.message(ChatStates.waiting_rename)
async def msg_rename_chat(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    chat_service: ChatService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None:
        return

    if not message.text:
        await state.clear()
        return

    data = await state.get_data()
    chat_id_str: str = data.get("chat_id") or ""

    result = await _get_user_and_chat(
        message.from_user.id, chat_id_str, user_service, chat_service
    )
    if result is None:
        await state.clear()
        return
    user, chat = result

    new_title = message.text.strip()[:CHAT_TITLE_MAX_LENGTH]
    if not new_title:
        new_title = localization.get("chat.new_title", language)
    renamed = await chat_service.rename(chat, new_title)
    await state.clear()

    await message.answer(
        localization.get("chat.renamed", language, title=renamed.title)
    )

    chats = await chat_service.get_user_chats(user.id)
    await message.answer(
        chats_list_text(localization, language, is_empty=not chats),
        reply_markup=chats_list_keyboard(chats, localization, language),
    )


# ── Auto-create chat for first message ────────────────────────────────────


@router.message(F.text & ~F.text.startswith("/"))
async def msg_auto_new_chat(
    message: Message,
    state: FSMContext,
    user_service: UserService,
    settings_service: SettingsService,
    chat_service: ChatService,
    ai_service: AIService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None or not message.text:
        return

    user_text = message.text.strip()
    if not user_text:
        return

    result = await _get_user_and_settings(
        message.from_user.id, user_service, settings_service
    )
    if result is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return
    user, user_settings = result

    lang = user_settings.language
    title = localization.get("chat.new_title", lang)
    chat = await chat_service.create(user.id, user_settings.default_model, title=title)

    await state.set_state(ChatStates.active)
    await state.update_data(chat_id=str(chat.id), is_new=True)

    await _do_ai_stream(
        message,
        state,
        user,
        chat,
        user_text,
        True,
        user_settings,
        ai_service,
        chat_service,
        localization,
        lang,
    )
