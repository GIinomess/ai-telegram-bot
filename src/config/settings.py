from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    channel_id: str

    database_url: str
    redis_url: str

    openai_api_key: str
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash-lite"

    free_daily_limit: int = 40

    premium_monthly_stars: int = 200
    premium_quarterly_stars: int = 500
    premium_yearly_stars: int = 1800


settings = Settings()  # type: ignore[call-arg]
