APP_NAME: str = "ai-telegram-bot"
APP_VERSION: str = "0.1.0"

SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "ru", "uk", "cs")
DEFAULT_LANGUAGE: str = "en"

MODEL_PROVIDERS: dict[str, str] = {
    "gpt-4o-mini": "openai",
    "gemini-2.0-flash": "gemini",
}

FREE_MODELS: tuple[str, ...] = ("gpt-4o-mini", "gemini-2.0-flash")

DEFAULT_MODEL: str = "gpt-4o-mini"
DEFAULT_CONVERSATION_STYLE: str = "balanced"
DEFAULT_CREATIVITY: float = 0.7
DEFAULT_CONTEXT_ENABLED: bool = True

CHAT_TITLE_MAX_LENGTH: int = 50

CONTEXT_MESSAGE_LIMIT: int = 20
CONTEXT_SUMMARY_THRESHOLD: int = 80_000

PLAN_DURATIONS: dict[str, int] = {
    "monthly": 30,
    "quarterly": 90,
    "yearly": 365,
}
