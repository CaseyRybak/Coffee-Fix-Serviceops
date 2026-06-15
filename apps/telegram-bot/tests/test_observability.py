import asyncio
import json
import logging

from serviceops_telegram_bot.config import BotSettings


def test_json_log_formatter_emits_service_context() -> None:
    from serviceops_telegram_bot.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-telegram-bot", environment="test")
    record = logging.LogRecord(
        name="serviceops_telegram_bot.tests",
        level=logging.ERROR,
        pathname=__file__,
        lineno=10,
        msg="bot disabled",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["service"] == "serviceops-telegram-bot"
    assert payload["environment"] == "test"
    assert payload["level"] == "ERROR"
    assert payload["logger"] == "serviceops_telegram_bot.tests"
    assert payload["message"] == "bot disabled"
    assert "timestamp" in payload


def test_json_log_formatter_emits_safe_operational_context() -> None:
    from serviceops_telegram_bot.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-telegram-bot", environment="test")
    record = logging.LogRecord(
        name="serviceops_telegram_bot.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="opt-in traced",
        args=(),
        exc_info=None,
    )
    record.serviceops_context = {
        "request_number": "CFX-20260615-000001",
        "event_id": "CFX-20260615-000001:service_request.created:1",
        "event_type": "service_request.created",
        "actor_username": "dispatcher@example.com",
        "action": "telegram.opt_in_consumed",
        "target": "telegram",
        "outcome": "succeeded",
        "reason": "linked",
        "duration_ms": 42,
        "provider": "telegram",
        "telegram_chat_id": "not logged",
    }

    payload = json.loads(formatter.format(record))

    assert payload["request_number"] == "CFX-20260615-000001"
    assert payload["event_id"] == "CFX-20260615-000001:service_request.created:1"
    assert payload["event_type"] == "service_request.created"
    assert payload["actor_username"] == "dispatcher@example.com"
    assert payload["action"] == "telegram.opt_in_consumed"
    assert payload["target"] == "telegram"
    assert payload["outcome"] == "succeeded"
    assert payload["reason"] == "linked"
    assert payload["duration_ms"] == 42
    assert payload["provider"] == "telegram"
    assert payload["telegram_chat_id"] == "[redacted]"


def test_json_log_formatter_redacts_sensitive_context_keys() -> None:
    from serviceops_telegram_bot.observability import JsonLogFormatter

    formatter = JsonLogFormatter(service_name="serviceops-telegram-bot", environment="test")
    record = logging.LogRecord(
        name="serviceops_telegram_bot.tests",
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


def test_run_bot_configures_logging_when_disabled(monkeypatch) -> None:
    import serviceops_telegram_bot.main as main

    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        main,
        "configure_logging",
        lambda service_name, environment: calls.append((service_name, environment)),
    )

    asyncio.run(main.run_bot(BotSettings(telegram_bot_token="", environment="test")))

    assert calls == [("serviceops-telegram-bot", "test")]
