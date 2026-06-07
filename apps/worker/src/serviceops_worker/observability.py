from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


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
