from aiogram import Router

from src.features.chats.handlers import router as chats_router
from src.features.settings.handlers import router as settings_router
from src.features.subscriptions.handlers import router as subscriptions_router
from src.features.users.handlers import router as users_router

main_router = Router(name="main")
main_router.include_router(users_router)
main_router.include_router(settings_router)
main_router.include_router(chats_router)
main_router.include_router(subscriptions_router)

__all__ = ["main_router"]
