from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

from src.config.constants import CHAT_TITLE_MAX_LENGTH
from src.features.chats.service import ChatService
from tests.conftest import make_chat


def make_service(
    chat_repo: AsyncMock,
    message_repo: AsyncMock,
    context_service: AsyncMock,
) -> ChatService:
    return ChatService(
        chat_repo=chat_repo,
        message_repo=message_repo,
        context_service=context_service,
    )


def make_repos() -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    chat_repo = AsyncMock()
    chat_repo.create = AsyncMock()
    chat_repo.get_by_id = AsyncMock()
    chat_repo.get_user_chats = AsyncMock()
    chat_repo.update = AsyncMock()
    chat_repo.soft_delete = AsyncMock()
    chat_repo.delete = AsyncMock()

    message_repo = AsyncMock()
    message_repo.delete_by_chat_id = AsyncMock()

    context_service = AsyncMock()
    context_service.clear = AsyncMock()

    return chat_repo, message_repo, context_service


class TestCreate:
    async def test_creates_chat_with_given_title_and_model(self) -> None:
        chat_repo, message_repo, ctx = make_repos()
        chat = make_chat(title="My Chat", model="gpt-4o-mini")
        chat_repo.create.return_value = chat
        user_id = uuid4()

        svc = make_service(chat_repo, message_repo, ctx)
        result = await svc.create(user_id, "gpt-4o-mini", title="My Chat")

        chat_repo.create.assert_awaited_once_with(
            user_id=user_id, title="My Chat", model="gpt-4o-mini"
        )
        assert result is chat

    async def test_default_title_is_new_chat(self) -> None:
        chat_repo, message_repo, ctx = make_repos()
        chat = make_chat()
        chat_repo.create.return_value = chat
        user_id = uuid4()

        svc = make_service(chat_repo, message_repo, ctx)
        await svc.create(user_id, "gpt-4o-mini")

        kwargs = chat_repo.create.call_args.kwargs
        assert kwargs["title"] == "New Chat"


class TestRename:
    async def test_updates_title_and_saves(self) -> None:
        chat_repo, message_repo, ctx = make_repos()
        chat = make_chat(title="Old Title")
        chat_repo.update.return_value = chat

        svc = make_service(chat_repo, message_repo, ctx)
        result = await svc.rename(chat, "New Title")

        assert chat.title == "New Title"
        chat_repo.update.assert_awaited_once_with(chat)
        assert result is chat


class TestRenameFromFirstMessage:
    async def test_truncates_long_message(self) -> None:
        chat_repo, message_repo, ctx = make_repos()
        chat = make_chat()
        chat_repo.update.return_value = chat

        long_msg = "A" * (CHAT_TITLE_MAX_LENGTH + 20)
        svc = make_service(chat_repo, message_repo, ctx)
        await svc.rename_from_first_message(chat, long_msg)

        assert len(chat.title) <= CHAT_TITLE_MAX_LENGTH

    async def test_uses_message_as_title(self) -> None:
        chat_repo, message_repo, ctx = make_repos()
        chat = make_chat()
        chat_repo.update.return_value = chat

        svc = make_service(chat_repo, message_repo, ctx)
        await svc.rename_from_first_message(chat, "Short message")

        assert "Short message" in chat.title

    async def test_empty_message_falls_back_to_new_chat(self) -> None:
        chat_repo, message_repo, ctx = make_repos()
        chat = make_chat()
        chat_repo.update.return_value = chat

        svc = make_service(chat_repo, message_repo, ctx)
        await svc.rename_from_first_message(chat, "   ")

        assert chat.title == "New Chat"


class TestArchive:
    async def test_soft_deletes_and_clears_context(self) -> None:
        chat_repo, message_repo, ctx = make_repos()
        chat = make_chat()
        chat_repo.soft_delete.return_value = chat

        svc = make_service(chat_repo, message_repo, ctx)
        result = await svc.archive(chat)

        chat_repo.soft_delete.assert_awaited_once_with(chat)
        ctx.clear.assert_awaited_once_with(chat.id)
        assert result is chat


class TestDelete:
    async def test_deletes_messages_context_and_chat(self) -> None:
        chat_repo, message_repo, ctx = make_repos()
        chat = make_chat()

        svc = make_service(chat_repo, message_repo, ctx)
        await svc.delete(chat)

        message_repo.delete_by_chat_id.assert_awaited_once_with(chat.id)
        ctx.clear.assert_awaited_once_with(chat.id)
        chat_repo.delete.assert_awaited_once_with(chat)
