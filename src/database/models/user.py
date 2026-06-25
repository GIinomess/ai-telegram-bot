from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base

if TYPE_CHECKING:
    from src.database.models.chat import Chat
    from src.database.models.payment import Payment
    from src.database.models.settings import Settings
    from src.database.models.subscription import Subscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chats: Mapped[list[Chat]] = relationship("Chat", back_populates="user")
    settings: Mapped[Settings | None] = relationship(
        "Settings", back_populates="user", uselist=False
    )
    subscriptions: Mapped[list[Subscription]] = relationship(
        "Subscription", back_populates="user"
    )
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="user")
