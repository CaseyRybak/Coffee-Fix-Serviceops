#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_BASE_URL = os.environ.get("SERVICEOPS_PUBLIC_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
BOT_SECRET = os.environ.get("SERVICEOPS_TELEGRAM_BOT_API_SECRET", "")
DISPATCHER_CHAT_ID = os.environ.get("SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID", "")
STAFF_USERNAME = os.environ.get("SERVICEOPS_STAFF_DEV_USERNAME", "dispatcher@coffeefix.local")
STAFF_PASSWORD = os.environ.get("SERVICEOPS_STAFF_DEV_PASSWORD", "dispatcher-local")


def request_json(path: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE_URL}{path}",
        data=body,
        method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{path} failed with HTTP {exc.code}: {detail}") from exc


def require_env() -> None:
    missing = [
        name
        for name, value in {
            "SERVICEOPS_TELEGRAM_BOT_API_SECRET": BOT_SECRET,
            "SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID": DISPATCHER_CHAT_ID,
        }.items()
        if not value.strip()
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def create_request() -> str:
    response = request_json(
        "/service-requests",
        {
            "customer": {
                "name": "Local Notification Smoke",
                "phone": "+7 900 000-00-01",
                "telegram": "@serviceops_local_smoke",
                "client_type": "private",
            },
            "machine": {
                "brand": "Jura",
                "model": "E8",
                "location_type": "home",
            },
            "problem": "Local n8n notification smoke test.",
            "address": "Local test address",
            "urgency": "planned",
        },
    )
    return str(response["request_number"])


def link_opt_in(request_number: str) -> None:
    response = request_json(
        f"/service-requests/{urllib.parse.quote(request_number)}/telegram-opt-in",
        {"telegram": "@serviceops_local_smoke"},
    )
    token = str(response["link"]).rsplit("start=", 1)[-1]
    request_json(
        f"/notifications/telegram/opt-ins/{urllib.parse.quote(token)}/link",
        {"chat_id": int(DISPATCHER_CHAT_ID), "username": "serviceops_local_smoke"},
        {"X-ServiceOps-Telegram-Bot-Secret": BOT_SECRET},
    )


def dispatcher_token() -> str:
    response = request_json("/staff/login", {"username": STAFF_USERNAME, "password": STAFF_PASSWORD})
    return str(response["access_token"])


def ask_clarification(request_number: str, token: str) -> None:
    request_json(
        f"/dispatcher/service-requests/{urllib.parse.quote(request_number)}/clarifications",
        {"question": "Local smoke: reply is not required; this checks Telegram delivery."},
        {"Authorization": f"Bearer {token}"},
    )


def wait_for_delivery(request_number: str, token: str) -> dict[str, Any]:
    deadline = time.monotonic() + 45
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        detail = request_json(
            f"/dispatcher/service-requests/{urllib.parse.quote(request_number)}",
            headers={"Authorization": f"Bearer {token}"},
        )
        deliveries = detail.get("notification_deliveries", [])
        for delivery in deliveries:
            if delivery.get("event_type") == "service_request.clarification_requested":
                last = dict(delivery)
                if delivery.get("status") in {"sent", "failed"}:
                    return last
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for clarification delivery result; last={last}")


def main() -> None:
    require_env()
    request_number = create_request()
    link_opt_in(request_number)
    token = dispatcher_token()
    ask_clarification(request_number, token)
    delivery = wait_for_delivery(request_number, token)
    if delivery.get("status") != "sent" or delivery.get("channel") != "telegram" or not delivery.get("provider_message_id"):
        raise RuntimeError(f"Unexpected clarification delivery result: {delivery}")
    print(json.dumps({"request_number": request_number, "clarification_delivery": "sent"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
