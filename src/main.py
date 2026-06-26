from __future__ import annotations

import asyncio

import structlog

from src.bot.app import start_polling
from src.core.logging import configure_logging

logger = structlog.get_logger(__name__)


async def main() -> None:
    configure_logging()
    await start_polling()


if __name__ == "__main__":
    asyncio.run(main())
