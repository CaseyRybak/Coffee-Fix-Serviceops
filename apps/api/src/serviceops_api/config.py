from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "serviceops-api"
    environment: str = "local"
    database_url: str = "sqlite:///.local/serviceops-api.sqlite3"
    intake_sqlite_path: str = ".local/serviceops-api.sqlite3"
    redis_url: str = "redis://redis:6379/0"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    staff_auth_secret: str = "local-dev-staff-auth-secret-change-me"
    staff_token_ttl_seconds: int = 60 * 60 * 12
    staff_dev_username: str = "dispatcher@coffeefix.local"
    staff_dev_password: str = "dispatcher-local"
    staff_dev_roles: str = "dispatcher"
    knowledge_sqlite_path: str = ".local/serviceops-knowledge.sqlite3"
    knowledge_embedding_dimensions: int = 12
    knowledge_retrieval_limit: int = 5
    embedding_provider: str = "deterministic"
    embedding_model: str = "text-embedding-3-small"
    embedding_api_base_url: str = "https://api.openai.com/v1"
    embedding_api_key: str = ""
    embedding_timeout_seconds: float = 20.0
    embedding_max_retries: int = 2
    ai_sqlite_path: str = ".local/serviceops-ai.sqlite3"
    ai_provider: str = "deterministic"
    ai_model: str = "gpt-4.1-mini"
    ai_api_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_timeout_seconds: float = 20.0
    ai_max_retries: int = 2
    ai_suggestion_limit: int = 3
    n8n_webhook_shared_secret: str = ""
    n8n_callback_secret: str = ""
    n8n_webhook_timeout_seconds: float = 5.0
    n8n_request_created_webhook_url: str = ""
    n8n_status_changed_webhook_url: str = ""
    n8n_clarification_webhook_url: str = ""
    n8n_customer_answered_webhook_url: str = ""
    telegram_bot_api_secret: str = ""
    telegram_bot_username: str = "coffeefix_service_bot"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def staff_dev_roles_list(self) -> list[str]:
        return [role.strip() for role in self.staff_dev_roles.split(",") if role.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SERVICEOPS_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
