from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    telegram_bot_token: str = ""
    environment: str = "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SERVICEOPS_",
        extra="ignore",
    )

    @property
    def is_enabled(self) -> bool:
        return bool(self.telegram_bot_token.strip())

