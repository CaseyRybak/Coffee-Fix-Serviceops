from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "serviceops-api"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops"
    redis_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SERVICEOPS_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

