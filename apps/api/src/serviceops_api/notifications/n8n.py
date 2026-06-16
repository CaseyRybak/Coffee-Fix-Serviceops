from __future__ import annotations

import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from serviceops_api.config import Settings
from serviceops_api.notifications.models import NotificationEvent


class N8nDeliveryClient(Protocol):
    def deliver(self, event: dict[str, object]) -> dict[str, str]:
        """Deliver a notification event and return delivery metadata."""


class DisabledN8nClient:
    def deliver(self, event: dict[str, object]) -> dict[str, str]:
        return {"status": "queued"}


class N8nWebhookClient:
    def __init__(self, settings: Settings) -> None:
        self._shared_secret = settings.n8n_webhook_shared_secret
        self._timeout_seconds = settings.n8n_webhook_timeout_seconds
        self._urls = {
            "service_request.created": settings.n8n_request_created_webhook_url,
            "service_request.status_changed": settings.n8n_status_changed_webhook_url,
            "service_request.clarification_requested": settings.n8n_clarification_webhook_url,
            "service_request.customer_answered": settings.n8n_customer_answered_webhook_url,
        }

    def deliver(self, event: dict[str, object]) -> dict[str, str]:
        event_type = str(event["event_type"])
        url = self._urls.get(event_type)
        if not url:
            return {"status": "queued"}
        body = json.dumps(event, ensure_ascii=False).encode("utf-8")
        request = Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-ServiceOps-Webhook-Secret": self._shared_secret,
                "Idempotency-Key": str(event["event_id"]),
            },
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return {
                    "status": "queued" if 200 <= response.status < 300 else "failed",
                    "provider_message_id": response.headers.get("X-N8n-Execution-Id", ""),
                }
        except (HTTPError, URLError, TimeoutError) as exc:
            return {"status": "failed", "error": str(exc)}


def event_to_dict(event: NotificationEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "request_number": event.request_number,
        "payload": event.payload,
    }
