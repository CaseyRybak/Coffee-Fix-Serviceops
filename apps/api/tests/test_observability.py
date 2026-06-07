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


def test_create_app_configures_logging(monkeypatch) -> None:
    import serviceops_api.main as main

    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(main, "get_settings", lambda: Settings(environment="test"))
    monkeypatch.setattr(main, "configure_logging", lambda service_name, environment: calls.append((service_name, environment)))

    main.create_app()

    assert calls == [("serviceops-api", "test")]
