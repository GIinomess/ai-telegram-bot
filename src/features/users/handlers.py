from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.features.settings.keyboards import MODEL_LABELS, model_keyboard
from src.features.settings.service import SettingsService
from src.features.subscriptions.keyboards import premium_keyboard, premium_text
from src.features.subscriptions.service import SubscriptionService
from src.features.users.keyboards import (
    MENU_BUTTONS,
    ImageCallback,
    LanguageCallback,
    image_after_keyboard,
    language_keyboard,
    main_menu_keyboard,
)
from src.features.users.service import UserService
from src.services.image import ImageService
from src.services.localization import LocalizationService
from src.shared.exceptions import ProviderUnavailableError

router = Router(name="users")


class ImageStates(StatesGroup):
    waiting_prompt = State()


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
            localization.get("welcome.capabilities", lang),
            reply_markup=main_menu_keyboard(),
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

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        localization.get("welcome.capabilities", lang),
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.message(F.text == "🚀 Премиум")
async def msg_premium(
    message: Message,
    user_service: UserService,
    subscription_service: SubscriptionService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None:
        return
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return
    subscription = await subscription_service.get_active_subscription(user.id)
    lang = user.language
    await message.answer(
        premium_text(subscription, localization, lang),
        reply_markup=premium_keyboard(localization, lang),
    )


@router.message(Command("account"))
@router.message(F.text == "👤 Мой профиль")
async def msg_my_profile(
    message: Message,
    user_service: UserService,
    settings_service: SettingsService,
    subscription_service: SubscriptionService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None:
        return
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return
    user_settings = await settings_service.get_or_create(user.id)
    is_premium = await subscription_service.is_premium(user.id)

    lang = user_settings.language
    name = user.first_name
    if user.username:
        name = f"{name} (@{user.username})"
    model_label = MODEL_LABELS.get(
        user_settings.default_model, user_settings.default_model
    )
    premium_key = "profile.premium_yes" if is_premium else "profile.premium_no"

    await message.answer(
        localization.get(
            "profile.text",
            lang,
            name=name,
            model=model_label,
            premium=localization.get(premium_key, lang),
        ),
    )


@router.message(Command("model"))
@router.message(F.text == "📝 Выбрать модель")
async def msg_choose_model(
    message: Message,
    user_service: UserService,
    settings_service: SettingsService,
    localization: LocalizationService,
    language: str,
) -> None:
    if message.from_user is None:
        return
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(localization.get("errors.user_not_found", language))
        return
    user_settings = await settings_service.get_or_create(user.id)
    lang = user_settings.language
    await message.answer(
        localization.get("settings.choose_model", lang),
        reply_markup=model_keyboard(user_settings.default_model, localization, lang),
    )


@router.message(Command("help"))
async def cmd_help(
    message: Message,
    localization: LocalizationService,
    language: str,
) -> None:
    await message.answer(
        f"<b>{localization.get('help.title', language)}</b>\n\n"
        f"{localization.get('help.text', language, support='@support')}",
    )


@router.message(Command("deletecontext", "video", "music", "slides", "s", "privacy"))
async def cmd_stub(
    message: Message,
    localization: LocalizationService,
    language: str,
) -> None:
    await message.answer(localization.get("common.coming_soon", language))


@router.message(Command("photo"))
@router.message(F.text == "🎨 Создать картинку")
async def msg_image(
    message: Message,
    state: FSMContext,
    localization: LocalizationService,
    language: str,
) -> None:
    await state.set_state(ImageStates.waiting_prompt)
    await message.answer(localization.get("image.text", language))


@router.message(ImageStates.waiting_prompt)
async def msg_image_prompt(
    message: Message,
    state: FSMContext,
    image_service: ImageService,
    localization: LocalizationService,
    language: str,
) -> None:
    if not message.text:
        await message.answer(localization.get("image.prompt_required", language))
        return

    prompt = message.text
    await state.clear()
    await message.answer(localization.get("image.generating", language))

    try:
        result = await image_service.generate(prompt)
        photo: BufferedInputFile | str
        if isinstance(result, bytes):
            photo = BufferedInputFile(result, filename="image.png")
        else:
            photo = result
        await message.answer_photo(
            photo=photo,
            caption=html.escape(prompt[:1024]),
            reply_markup=image_after_keyboard(localization, language),
        )
    except ProviderUnavailableError:
        await message.answer(localization.get("image.error", language))


@router.callback_query(ImageCallback.filter(F.action == "create_another"))
async def cb_image_create_another(
    callback: CallbackQuery,
    state: FSMContext,
    localization: LocalizationService,
    language: str,
) -> None:
    if not isinstance(callback.message, Message):
        return
    await state.set_state(ImageStates.waiting_prompt)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(localization.get("image.text", language))
    await callback.answer()


@router.message(F.text == "💻 Разработка")
async def msg_development(
    message: Message,
    localization: LocalizationService,
    language: str,
) -> None:
    await message.answer(localization.get("dev.text", language))


@router.message(F.text.in_(MENU_BUTTONS))
async def msg_menu_stub(
    message: Message,
    localization: LocalizationService,
    language: str,
) -> None:
    await message.answer(localization.get("common.coming_soon", language))
