from __future__ import annotations

from typing import Any, Protocol

from serviceops_api.notifications.models import (
    DeliveryResultPayload,
    DeliveryResultResponse,
    NotificationEvent,
    TelegramOptInLinkPayload,
    TelegramOptInLinkResponse,
)
from serviceops_api.notifications.n8n import N8nDeliveryClient, event_to_dict


class NotificationStore(Protocol):
    def next_sequence(self, request_number: str) -> int:
        """Return the next notification event sequence for a request."""

    def create_queued_attempt(self, event: NotificationEvent) -> bool:
        """Persist a queued delivery attempt and return False for duplicate event IDs."""

    def record_delivery_result(
        self,
        event_id: str,
        status: str,
        channel: str | None = None,
        provider_message_id: str | None = None,
        error: str | None = None,
        attempt_count: int = 1,
    ) -> None:
        """Persist delivery result metadata."""

    def record_callback_result(self, payload: DeliveryResultPayload) -> None:
        """Persist an n8n callback payload."""


class ServiceRequestNotificationReader(Protocol):
    def get_request_snapshot(self, request_number: str) -> dict[str, Any]:
        """Return internal request data for payload assembly."""

    def get_public_status_by_request_number(self, request_number: str) -> dict[str, Any]:
        """Return public-safe request data for payload assembly."""

    def link_telegram_opt_in(self, token: str, chat_id: str, username: str | None) -> dict[str, Any]:
        """Link a Telegram opt-in token to a Telegram chat."""


class NotificationPublisher:
    def __init__(
        self,
        notification_store: NotificationStore,
        n8n_client: N8nDeliveryClient,
        service_request_reader: ServiceRequestNotificationReader,
    ) -> None:
        self._notification_store = notification_store
        self._n8n_client = n8n_client
        self._service_request_reader = service_request_reader

    def publish_request_created(self, request_number: str) -> None:
        snapshot = self._service_request_reader.get_request_snapshot(request_number)
        public_status = self._service_request_reader.get_public_status_by_request_number(request_number)
        payload = {
            "request_number": request_number,
            "customer_name": snapshot["customer"]["name"],
            "customer_phone_masked": public_status["customer"]["phone_masked"],
            "machine_brand": snapshot["machine"]["brand"],
            "machine_model": snapshot["machine"]["model"],
            "urgency": snapshot["request"]["urgency"],
            "public_status_url": f"/status/{public_status['public_token']}",
        }
        self._publish("service_request.created", request_number, payload)

    def publish_status_changed(self, request_number: str, new_status: str) -> None:
        public_status = self._service_request_reader.get_public_status_by_request_number(request_number)
        snapshot = self._service_request_reader.get_request_snapshot(request_number)
        payload = {
            "request_number": request_number,
            "customer_name": public_status["customer"]["name"],
            "telegram_handle": public_status["customer"]["telegram"],
            "telegram_chat_id": snapshot["customer"].get("telegram_chat_id"),
            "new_status": new_status,
            "public_status_url": f"/status/{public_status['public_token']}",
        }
        self._publish("service_request.status_changed", request_number, payload)

    def publish_clarification_requested(self, request_number: str, question_id: int) -> None:
        public_status = self._service_request_reader.get_public_status_by_request_number(request_number)
        snapshot = self._service_request_reader.get_request_snapshot(request_number)
        clarification = public_status["clarification"] or {}
        payload = {
            "request_number": request_number,
            "customer_name": public_status["customer"]["name"],
            "telegram_handle": public_status["customer"]["telegram"],
            "telegram_chat_id": snapshot["customer"].get("telegram_chat_id"),
            "question_id": question_id,
            "question": clarification.get("question"),
            "public_status_url": f"/status/{public_status['public_token']}",
        }
        self._publish("service_request.clarification_requested", request_number, payload)

    def publish_customer_answered(self, request_number: str, question_id: int) -> None:
        public_status = self._service_request_reader.get_public_status_by_request_number(request_number)
        payload = {
            "request_number": request_number,
            "question_id": question_id,
            "status": public_status["status"],
            "public_status_url": f"/status/{public_status['public_token']}",
        }
        self._publish("service_request.customer_answered", request_number, payload)

    def _publish(self, event_type: str, request_number: str, payload: dict[str, Any]) -> None:
        sequence = self._notification_store.next_sequence(request_number)
        event = NotificationEvent(
            event_id=f"{request_number}:{event_type}:{sequence}",
            event_type=event_type,  # type: ignore[arg-type]
            request_number=request_number,
            payload=payload,
        )
        if not self._notification_store.create_queued_attempt(event):
            return
        result = self._n8n_client.deliver(event_to_dict(event))
        self._notification_store.record_delivery_result(
            event_id=event.event_id,
            status=result.get("status", "failed"),
            provider_message_id=result.get("provider_message_id") or None,
            error=result.get("error") or None,
            attempt_count=1,
        )


class RecordN8nDeliveryResult:
    def __init__(self, notification_store: NotificationStore) -> None:
        self._notification_store = notification_store

    def execute(self, payload: DeliveryResultPayload) -> DeliveryResultResponse:
        self._notification_store.record_callback_result(payload)
        return DeliveryResultResponse(event_id=payload.event_id, status=payload.status)


class LinkTelegramOptIn:
    def __init__(self, service_request_reader: ServiceRequestNotificationReader) -> None:
        self._service_request_reader = service_request_reader

    def execute(self, token: str, payload: TelegramOptInLinkPayload) -> TelegramOptInLinkResponse:
        linked = self._service_request_reader.link_telegram_opt_in(
            token=token,
            chat_id=str(payload.chat_id),
            username=payload.username,
        )
        return TelegramOptInLinkResponse.model_validate(
            {
                **linked,
                "message": "Telegram notifications linked",
            }
        )
