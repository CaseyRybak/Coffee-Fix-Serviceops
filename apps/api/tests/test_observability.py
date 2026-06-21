import json
import logging

from serviceops_api.config import Settings


def test_json_log_formatter_emits_service_context() -> None:
    from serviceops_api.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-api", environment="test")
    record = logging.LogRecord(
        name="serviceops_api.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="health checked",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["service"] == "serviceops-api"
    assert payload["environment"] == "test"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "serviceops_api.tests"
    assert payload["message"] == "health checked"
    assert "timestamp" in payload


def test_json_log_formatter_emits_safe_operational_context() -> None:
    from serviceops_api.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-api", environment="test")
    record = logging.LogRecord(
        name="serviceops_api.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="request traced",
        args=(),
        exc_info=None,
    )
    record.serviceops_context = {
        "request_number": "CFX-20260615-000001",
        "event_id": "CFX-20260615-000001:service_request.created:1",
        "event_type": "service_request.created",
        "actor_username": "dispatcher@example.com",
        "action": "dispatcher.status_updated",
        "target": "CFX-20260615-000001",
        "outcome": "succeeded",
        "reason": "status accepted",
        "duration_ms": 42,
        "provider": "n8n",
        "ignored_internal_value": "not logged",
    }

    payload = json.loads(formatter.format(record))

    assert payload["request_number"] == "CFX-20260615-000001"
    assert payload["event_id"] == "CFX-20260615-000001:service_request.created:1"
    assert payload["event_type"] == "service_request.created"
    assert payload["actor_username"] == "dispatcher@example.com"
    assert payload["action"] == "dispatcher.status_updated"
    assert payload["target"] == "CFX-20260615-000001"
    assert payload["outcome"] == "succeeded"
    assert payload["reason"] == "status accepted"
    assert payload["duration_ms"] == 42
    assert payload["provider"] == "n8n"
    assert "ignored_internal_value" not in payload


def test_json_log_formatter_redacts_sensitive_context_keys() -> None:
    from serviceops_api.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-api", environment="test")
    record = logging.LogRecord(
        name="serviceops_api.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="sensitive context",
        args=(),
        exc_info=None,
    )
    record.serviceops_context = {
        "password": "plain-password",
        "password_hash": "hash-value",
        "access_token": "access-token",
        "token": "opt-in-token",
        "telegram_chat_id": "123456789",
        "SERVICEOPS_STAFF_AUTH_SECRET": "staff-secret",
        "SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET": "n8n-secret",
        "SERVICEOPS_N8N_CALLBACK_SECRET": "callback-secret",
        "SERVICEOPS_AI_API_KEY": "ai-key",
        "SERVICEOPS_EMBEDDING_API_KEY": "embedding-key",
    }

    payload = json.loads(formatter.format(record))

    assert payload["password"] == "[redacted]"
    assert payload["password_hash"] == "[redacted]"
    assert payload["access_token"] == "[redacted]"
    assert payload["token"] == "[redacted]"
    assert payload["telegram_chat_id"] == "[redacted]"
    assert payload["SERVICEOPS_STAFF_AUTH_SECRET"] == "[redacted]"
    assert payload["SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET"] == "[redacted]"
    assert payload["SERVICEOPS_N8N_CALLBACK_SECRET"] == "[redacted]"
    assert payload["SERVICEOPS_AI_API_KEY"] == "[redacted]"
    assert payload["SERVICEOPS_EMBEDDING_API_KEY"] == "[redacted]"


def test_create_app_configures_logging(monkeypatch) -> None:
    import serviceops_api.main as main

    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(main, "get_settings", lambda: Settings(environment="test"))
    monkeypatch.setattr(main, "configure_logging", lambda service_name, environment: calls.append((service_name, environment)))

    main.create_app()

    assert calls == [("serviceops-api", "test")]


def test_create_app_disables_openapi_docs_in_production(monkeypatch) -> None:
    import serviceops_api.main as main

    from serviceops_api.service_requests.repository import ServiceRequestRepository

    settings = Settings(
        environment="production",
        database_url="postgresql+psycopg://serviceops:strong-password@postgres:5432/serviceops",
        staff_auth_secret="staff-secret-value",
        n8n_webhook_shared_secret="webhook-secret-value",
        n8n_callback_secret="callback-secret-value",
        telegram_bot_api_secret="telegram-api-secret-value",
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "configure_logging", lambda service_name, environment: None)

    app = main.create_app(service_request_repository=ServiceRequestRepository.in_memory())

    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None
