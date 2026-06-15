import json
import logging


def test_json_log_formatter_emits_service_context() -> None:
    from serviceops_worker.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-worker", environment="test")
    record = logging.LogRecord(
        name="serviceops_worker.tests",
        level=logging.WARNING,
        pathname=__file__,
        lineno=10,
        msg="worker started",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["service"] == "serviceops-worker"
    assert payload["environment"] == "test"
    assert payload["level"] == "WARNING"
    assert payload["logger"] == "serviceops_worker.tests"
    assert payload["message"] == "worker started"
    assert "timestamp" in payload


def test_json_log_formatter_emits_safe_operational_context() -> None:
    from serviceops_worker.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-worker", environment="test")
    record = logging.LogRecord(
        name="serviceops_worker.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="embedding traced",
        args=(),
        exc_info=None,
    )
    record.serviceops_context = {
        "request_number": "CFX-20260615-000001",
        "event_id": "CFX-20260615-000001:service_request.created:1",
        "event_type": "service_request.created",
        "actor_username": "dispatcher@example.com",
        "action": "knowledge_base.embedding_generated",
        "target": "document-1",
        "outcome": "succeeded",
        "reason": "processed",
        "duration_ms": 42,
        "provider": "deterministic",
        "document_body": "not logged",
    }

    payload = json.loads(formatter.format(record))

    assert payload["request_number"] == "CFX-20260615-000001"
    assert payload["event_id"] == "CFX-20260615-000001:service_request.created:1"
    assert payload["event_type"] == "service_request.created"
    assert payload["actor_username"] == "dispatcher@example.com"
    assert payload["action"] == "knowledge_base.embedding_generated"
    assert payload["target"] == "document-1"
    assert payload["outcome"] == "succeeded"
    assert payload["reason"] == "processed"
    assert payload["duration_ms"] == 42
    assert payload["provider"] == "deterministic"
    assert "document_body" not in payload


def test_json_log_formatter_redacts_sensitive_context_keys() -> None:
    from serviceops_worker.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-worker", environment="test")
    record = logging.LogRecord(
        name="serviceops_worker.tests",
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


def test_create_celery_app_configures_logging(monkeypatch) -> None:
    import serviceops_worker.celery_app as celery_app

    calls: list[tuple[str, str]] = []
    monkeypatch.setenv("SERVICEOPS_SERVICE_NAME", "serviceops-worker-test")
    monkeypatch.setenv("SERVICEOPS_ENVIRONMENT", "test")
    monkeypatch.setattr(
        celery_app,
        "configure_logging",
        lambda service_name, environment: calls.append((service_name, environment)),
    )

    celery_app.create_celery_app()

    assert calls == [("serviceops-worker-test", "test")]
