from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.database.models.chat import Chat
from src.services.localization import LocalizationService


class ChatCallback(CallbackData, prefix="ch"):
    action: str
    chat_id: str = ""


def _truncate(title: str, max_len: int = 25) -> str:
    if len(title) > max_len:
        return title[:max_len] + "…"
    return title


# ── Text formatters ────────────────────────────────────────────────────────


def chats_list_text(
    localization: LocalizationService,
    language: str,
    *,
    is_empty: bool = False,
) -> str:
    header = f"📂 <b>{localization.get('history.title', language)}</b>"
    if is_empty:
        return f"{header}\n\n{localization.get('history.empty', language)}"
    return header


def chat_open_text(
    chat: Chat,
    localization: LocalizationService,
    language: str,
) -> str:
    return (
        f"💬 <b>{chat.title}</b>\n\n"
        f"{localization.get('chat.type_message', language)}"
    )


def chat_manage_text(chat: Chat) -> str:
    return f"⚙️ <b>{chat.title}</b>"


def chat_delete_confirm_text(
    localization: LocalizationService,
    language: str,
) -> str:
    return localization.get("history.confirm_delete", language)


# ── Keyboard builders ──────────────────────────────────────────────────────


def chats_list_keyboard(
    chats: list[Chat],
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for chat in chats:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💬 {_truncate(chat.title)}",
                    callback_data=ChatCallback(
                        action="open", chat_id=str(chat.id)
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="⚙️",
                    callback_data=ChatCallback(
                        action="manage", chat_id=str(chat.id)
                    ).pack(),
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=localization.get("menu.new_chat", language),
                callback_data=ChatCallback(action="new").pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def chat_open_keyboard(
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=localization.get("menu.my_chats", language),
                    callback_data=ChatCallback(action="list").pack(),
                )
            ]
        ]
    )


def chat_manage_keyboard(
    chat_id: str,
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✏️ {localization.get('history.rename', language)}",
                    callback_data=ChatCallback(action="rename", chat_id=chat_id).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📦 {localization.get('history.archive', language)}",
                    callback_data=ChatCallback(
                        action="archive", chat_id=chat_id
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🗑 {localization.get('history.delete', language)}",
                    callback_data=ChatCallback(
                        action="del_ask", chat_id=chat_id
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=localization.get("common.back", language),
                    callback_data=ChatCallback(action="list").pack(),
                )
            ],
        ]
    )


def chat_delete_confirm_keyboard(
    chat_id: str,
    localization: LocalizationService,
    language: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ {localization.get('common.confirm', language)}",
                    callback_data=ChatCallback(action="delete", chat_id=chat_id).pack(),
                ),
                InlineKeyboardButton(
                    text=f"❌ {localization.get('common.cancel', language)}",
                    callback_data=ChatCallback(action="list").pack(),
                ),
            ]
        ]
    )
