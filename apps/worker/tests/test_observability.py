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
