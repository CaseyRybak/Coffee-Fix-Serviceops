import pytest

from serviceops_api.config import Settings


def test_production_runtime_rejects_sqlite_and_placeholder_secrets() -> None:
    settings = Settings(
        environment="production",
        database_url="sqlite:///:memory:",
        staff_auth_secret="local-dev-staff-auth-secret-change-me",
        n8n_webhook_shared_secret="change-me",
        n8n_callback_secret="change-me",
        n8n_request_created_webhook_url="https://n8n.example/webhook/request-created",
        telegram_bot_api_secret="change-me",
    )

    with pytest.raises(ValueError) as exc:
        settings.validate_runtime()

    message = str(exc.value)
    assert "SERVICEOPS_DATABASE_URL must use PostgreSQL in production" in message
    assert "SERVICEOPS_STAFF_AUTH_SECRET must be set to a non-placeholder value" in message
    assert "SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET must be set to a non-placeholder value" in message
    assert "SERVICEOPS_N8N_CALLBACK_SECRET must be set to a non-placeholder value" in message
    assert "SERVICEOPS_TELEGRAM_BOT_API_SECRET must be set to a non-placeholder value" in message
    assert "change-me" not in message
    assert "local-dev-staff-auth-secret" not in message


def test_production_runtime_rejects_required_placeholder_secrets_without_webhook_urls() -> None:
    settings = Settings(
        environment="production",
        database_url="postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops",
        staff_auth_secret="change-me",
        n8n_webhook_shared_secret="change-me",
        n8n_callback_secret="change-me",
        telegram_bot_api_secret="change-me",
    )

    with pytest.raises(ValueError) as exc:
        settings.validate_runtime()

    message = str(exc.value)
    assert "SERVICEOPS_STAFF_AUTH_SECRET must be set to a non-placeholder value" in message
    assert "SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET must be set to a non-placeholder value" in message
    assert "SERVICEOPS_N8N_CALLBACK_SECRET must be set to a non-placeholder value" in message
    assert "SERVICEOPS_TELEGRAM_BOT_API_SECRET must be set to a non-placeholder value" in message
    assert "SERVICEOPS_DATABASE_URL must use PostgreSQL in production" not in message


def test_local_runtime_allows_deterministic_placeholder_defaults() -> None:
    Settings(environment="local", database_url="sqlite:///:memory:").validate_runtime()
