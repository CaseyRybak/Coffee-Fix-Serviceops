import asyncio

from serviceops_telegram_bot.config import BotSettings
from serviceops_telegram_bot.main import build_linked_request_message, parse_start_token
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
