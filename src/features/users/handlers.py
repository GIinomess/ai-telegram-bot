from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from src.features.users.keyboards import LanguageCallback, language_keyboard
from src.features.users.service import UserService
from src.services.localization import LocalizationService

router = Router(name="users")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    user_service: UserService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None:
        return

    tg_user = message.from_user
    existing_user = await user_service.get_by_telegram_id(tg_user.id)

    if existing_user is None:
        await message.answer(
            localization.get("start.select_language", language),
            reply_markup=language_keyboard(),
        )
    else:
        lang = existing_user.language
        await message.answer(
            f"<b>{localization.get('welcome.title', lang)}</b>\n\n"
            f"{localization.get('welcome.description', lang)}",
        )


@router.callback_query(LanguageCallback.filter())
async def cb_language_selected(
    callback: CallbackQuery,
    callback_data: LanguageCallback,
    user_service: UserService,
    localization: LocalizationService,
) -> None:
    if callback.from_user is None:
        return
    if not isinstance(callback.message, Message):
        return

    tg_user = callback.from_user
    lang = callback_data.code

    await user_service.get_or_create(
        telegram_id=tg_user.id,
        first_name=tg_user.first_name,
        username=tg_user.username,
        last_name=tg_user.last_name,
        language=lang,
    )

    await callback.message.edit_text(
        f"<b>{localization.get('welcome.title', lang)}</b>\n\n"
        f"{localization.get('welcome.description', lang)}",
    )
    await callback.answer()
