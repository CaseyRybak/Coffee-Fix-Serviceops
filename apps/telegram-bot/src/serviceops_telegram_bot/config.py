from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    telegram_bot_token: str = ""
    environment: str = "local"
    api_base_url: str = "http://api:8000"
    public_api_base_url: str = "http://localhost:8000"
    bot_api_secret: str = Field(default="", validation_alias="SERVICEOPS_TELEGRAM_BOT_API_SECRET")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SERVICEOPS_",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def is_enabled(self) -> bool:
        token = self.telegram_bot_token.strip()
        return bool(token) and token.lower() != "change-me"
