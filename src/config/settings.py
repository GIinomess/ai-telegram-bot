from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str
    channel_id: str

    database_url: str
    redis_url: str

    openai_api_key: str
    gemini_api_key: str

    free_daily_limit: int = 40


settings = Settings()  # type: ignore[call-arg]
