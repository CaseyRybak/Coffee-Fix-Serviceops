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
