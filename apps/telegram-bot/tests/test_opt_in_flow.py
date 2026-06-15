import asyncio
import logging

from serviceops_telegram_bot.config import BotSettings
from serviceops_telegram_bot.main import build_linked_request_message, log_opt_in_link_failed, parse_start_token
from serviceops_telegram_bot.serviceops_client import ServiceOpsClient


def test_parse_start_token_accepts_deep_link_token() -> None:
    assert parse_start_token("/start tg_abc123") == "tg_abc123"


def test_parse_start_token_rejects_missing_token() -> None:
    assert parse_start_token("/start") is None


def test_build_linked_request_message_includes_request_summary() -> None:
    message = build_linked_request_message(
        {
            "request_number": "CFX-20260610-000001",
            "status": "new",
            "customer_name": "Anna Petrova",
            "machine_label": "Jura E8",
            "public_status_url": "/status/status_token",
            "message": "Telegram notifications linked",
        },
        public_api_base_url="http://localhost:8000",
    )

    assert "CFX-20260610-000001" in message
    assert "Jura E8" in message
    assert "http://localhost:8000/status/status_token" in message


def test_serviceops_client_links_chat_with_bot_secret(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
        captured["url"] = url
        captured["body"] = body
        captured["headers"] = headers
        return {"request_number": "CFX-1"}

    client = ServiceOpsClient(
        BotSettings(
            telegram_bot_token="token",
            api_base_url="http://api:8000",
            bot_api_secret="bot-secret",
        ),
        async_post_json=fake_post_json,
    )

    result = asyncio.run(client.link_opt_in("tg_abc", chat_id=123, username="anna"))

    assert result == {"request_number": "CFX-1"}
    assert captured == {
        "url": "http://api:8000/notifications/telegram/opt-ins/tg_abc/link",
        "body": {"chat_id": 123, "username": "anna"},
        "headers": {"X-ServiceOps-Telegram-Bot-Secret": "bot-secret"},
    }


def test_serviceops_client_logs_success_without_token_or_chat_id(caplog) -> None:
    async def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
        return {
            "request_number": "CFX-20260615-000001",
            "status": "new",
            "machine_label": "Jura E8",
            "public_status_url": "/status/public-token",
        }

    client = ServiceOpsClient(
        BotSettings(
            telegram_bot_token="bot-token",
            api_base_url="http://api:8000",
            bot_api_secret="bot-secret",
        ),
        async_post_json=fake_post_json,
    )

    with caplog.at_level(logging.INFO, logger="serviceops_telegram_bot.serviceops_client"):
        result = asyncio.run(client.link_opt_in("tg_secret_token", chat_id=123, username="anna"))

    assert result["request_number"] == "CFX-20260615-000001"
    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    assert {
        "request_number": "CFX-20260615-000001",
        "action": "telegram.opt_in_linked",
        "target": "CFX-20260615-000001",
        "outcome": "succeeded",
        "provider": "telegram",
    } in contexts
    assert "tg_secret_token" not in str(contexts)
    assert "123" not in str(contexts)
    assert "bot-secret" not in str(contexts)


def test_serviceops_client_logs_failure_without_token_or_chat_id(caplog) -> None:
    async def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
        raise RuntimeError("expired token tg_secret_token for chat 123")

    client = ServiceOpsClient(
        BotSettings(
            telegram_bot_token="bot-token",
            api_base_url="http://api:8000",
            bot_api_secret="bot-secret",
        ),
        async_post_json=fake_post_json,
    )

    with caplog.at_level(logging.INFO, logger="serviceops_telegram_bot.serviceops_client"):
        try:
            asyncio.run(client.link_opt_in("tg_secret_token", chat_id=123, username="anna"))
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected opt-in link failure")

    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    assert {
        "action": "telegram.opt_in_linked",
        "target": "telegram",
        "outcome": "failed",
        "reason": "api_request_failed",
        "provider": "telegram",
    } in contexts
    assert "tg_secret_token" not in str(contexts)
    assert "123" not in str(contexts)
    assert "bot-secret" not in str(contexts)


def test_bot_handler_failure_log_has_no_exception_payload(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="serviceops_telegram_bot.main"):
        log_opt_in_link_failed()

    record = next(record for record in caplog.records if record.message == "Telegram opt-in link failed")
    assert record.exc_info is None
    assert record.serviceops_context == {
        "action": "telegram.opt_in_linked",
        "target": "telegram",
        "outcome": "failed",
        "reason": "api_request_failed",
        "provider": "telegram",
    }
