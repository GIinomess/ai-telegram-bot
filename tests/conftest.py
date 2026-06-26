from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

# Set required env vars before any src import triggers settings initialization
os.environ.setdefault("BOT_TOKEN", "1234567890:AAtest_bot_token_for_testing_only")
os.environ.setdefault("CHANNEL_ID", "@test_channel")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

import pytest

from src.database.models.chat import Chat
from src.database.models.message import Message
from src.database.models.settings import Settings
from src.database.models.subscription import Subscription
from src.database.models.user import User

# ── Model factories ────────────────────────────────────────────────────────


def make_user(
    *,
    telegram_id: int = 111222333,
    first_name: str = "Test",
    username: str | None = "testuser",
    language: str = "en",
) -> User:
    return User(
        id=uuid4(),
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
        language=language,
    )


def make_settings(user_id: UUID | None = None, *, language: str = "en") -> Settings:
    return Settings(
        id=uuid4(),
        user_id=user_id or uuid4(),
        default_model="gpt-4o-mini",
        language=language,
        conversation_style="balanced",
        creativity=0.7,
        context_enabled=True,
    )


def make_chat(
    user_id: UUID | None = None,
    *,
    title: str = "Test Chat",
    model: str = "gpt-4o-mini",
    context_enabled: bool = True,
) -> Chat:
    return Chat(
        id=uuid4(),
        user_id=user_id or uuid4(),
        title=title,
        model=model,
        context_enabled=context_enabled,
    )


def make_message(
    chat_id: UUID | None = None,
    *,
    role: str = "user",
    content: str = "Hello",
    token_count: int | None = 10,
) -> Message:
    return Message(
        id=uuid4(),
        chat_id=chat_id or uuid4(),
        role=role,
        content=content,
        token_count=token_count,
        created_at=datetime.now(UTC),
    )


def make_subscription(
    user_id: UUID | None = None,
    *,
    plan: str = "monthly",
    status: str = "active",
    days_until_expiry: int = 30,
) -> Subscription:
    now = datetime.now(UTC)
    return Subscription(
        id=uuid4(),
        user_id=user_id or uuid4(),
        plan=plan,
        status=status,
        started_at=now,
        expires_at=now + timedelta(days=days_until_expiry),
    )


# ── Common mock factories ──────────────────────────────────────────────────


def async_mock(return_value: object = None) -> AsyncMock:
    m = AsyncMock()
    m.return_value = return_value
    return m


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def user() -> User:
    return make_user()


@pytest.fixture
def user_settings(user: User) -> Settings:
    return make_settings(user.id)


@pytest.fixture
def chat(user: User) -> Chat:
    return make_chat(user.id)


@pytest.fixture
def active_subscription(user: User) -> Subscription:
    return make_subscription(user.id)
