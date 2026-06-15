from __future__ import annotations

import json
import logging
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

SAFE_CONTEXT_KEYS = {
    "request_number",
    "event_id",
    "event_type",
    "actor_username",
    "action",
    "target",
    "outcome",
    "reason",
    "duration_ms",
    "provider",
}

SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "telegram_chat_id",
)

REDACTED_VALUE = "[redacted]"


def is_sensitive_context_key(key: str) -> bool:
    normalized = key.lower()
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)


def redact_context_value(key: str, value: Any) -> Any:
    if is_sensitive_context_key(key):
        return REDACTED_VALUE
    if isinstance(value, Mapping):
        return {str(child_key): redact_context_value(str(child_key), child_value) for child_key, child_value in value.items()}
    if isinstance(value, list):
        return [redact_context_value(key, item) for item in value]
    if isinstance(value, tuple):
        return [redact_context_value(key, item) for item in value]
    return value


def safe_log_context(context: Any) -> dict[str, Any]:
    if not isinstance(context, Mapping):
        return {}

    safe_context: dict[str, Any] = {}
    for key, value in context.items():
        context_key = str(key)
        if context_key in SAFE_CONTEXT_KEYS or is_sensitive_context_key(context_key):
            safe_context[context_key] = redact_context_value(context_key, value)
    return safe_context


class JsonLogFormatter(logging.Formatter):
    def __init__(self, service_name: str, environment: str) -> None:
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
        }
        payload.update(safe_log_context(getattr(record, "serviceops_context", {})))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(service_name: str, environment: str) -> None:
    root_logger = logging.getLogger()
    formatter = JsonLogFormatter(service_name=service_name, environment=environment)

    for handler in root_logger.handlers:
        if getattr(handler, "_serviceops_json_handler", False):
            handler.setFormatter(formatter)
            root_logger.setLevel(logging.INFO)
            return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler._serviceops_json_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
