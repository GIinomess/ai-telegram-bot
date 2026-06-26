from __future__ import annotations

from unittest.mock import AsyncMock

from src.config.constants import CONTEXT_MESSAGE_LIMIT, CONTEXT_SUMMARY_THRESHOLD
from src.services.context import ContextService
from tests.conftest import make_chat, make_message


def make_service(message_repo: AsyncMock, chat_repo: AsyncMock) -> ContextService:
    return ContextService(message_repo=message_repo, chat_repo=chat_repo)


def make_repos() -> tuple[AsyncMock, AsyncMock]:
    message_repo = AsyncMock()
    message_repo.get_chat_messages = AsyncMock()
    chat_repo = AsyncMock()
    chat_repo.update = AsyncMock()
    return message_repo, chat_repo


class TestLoadContext:
    async def test_returns_messages_when_context_enabled(self) -> None:
        message_repo, chat_repo = make_repos()
        msgs = [make_message(role="user"), make_message(role="assistant")]
        message_repo.get_chat_messages.return_value = msgs
        chat = make_chat(context_enabled=True)

        svc = make_service(message_repo, chat_repo)
        result = await svc.load_context(chat)

        message_repo.get_chat_messages.assert_awaited_once_with(
            chat.id, limit=CONTEXT_MESSAGE_LIMIT
        )
        assert result == msgs

    async def test_returns_empty_when_context_disabled(self) -> None:
        message_repo, chat_repo = make_repos()
        chat = make_chat(context_enabled=False)

        svc = make_service(message_repo, chat_repo)
        result = await svc.load_context(chat)

        message_repo.get_chat_messages.assert_not_awaited()
        assert result == []


class TestNeedsSummarization:
    async def test_needs_summarization_when_tokens_exceed_threshold(self) -> None:
        message_repo, chat_repo = make_repos()
        msgs = [
            make_message(token_count=CONTEXT_SUMMARY_THRESHOLD // 2 + 1),
            make_message(token_count=CONTEXT_SUMMARY_THRESHOLD // 2),
        ]
        message_repo.get_chat_messages.return_value = msgs
        chat = make_chat()

        svc = make_service(message_repo, chat_repo)
        result = await svc.needs_summarization(chat.id)

        assert result is True

    async def test_no_summarization_when_tokens_below_threshold(self) -> None:
        message_repo, chat_repo = make_repos()
        message_repo.get_chat_messages.return_value = [make_message(token_count=100)]
        chat = make_chat()

        svc = make_service(message_repo, chat_repo)
        result = await svc.needs_summarization(chat.id)

        assert result is False

    async def test_no_summarization_when_messages_have_no_tokens(self) -> None:
        message_repo, chat_repo = make_repos()
        msgs = [make_message(token_count=None), make_message(token_count=None)]
        message_repo.get_chat_messages.return_value = msgs
        chat = make_chat()

        svc = make_service(message_repo, chat_repo)
        result = await svc.needs_summarization(chat.id)

        assert result is False


class TestSaveSummary:
    async def test_sets_summary_and_saves_chat(self) -> None:
        message_repo, chat_repo = make_repos()
        chat = make_chat()
        chat_repo.update.return_value = chat

        svc = make_service(message_repo, chat_repo)
        result = await svc.save_summary(chat, "This is a summary.")

        assert chat.summary == "This is a summary."
        chat_repo.update.assert_awaited_once_with(chat)
        assert result is chat


class TestClear:
    async def test_clear_does_not_raise(self) -> None:
        message_repo, chat_repo = make_repos()
        chat = make_chat()

        svc = make_service(message_repo, chat_repo)
        await svc.clear(chat.id)  # should not raise
