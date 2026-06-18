from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Protocol

from serviceops_api.owner_dashboard.models import (
    LowStockRiskItem,
    OwnerDailyReportResponse,
    OwnerDashboardResponse,
    OwnerSlaRiskItem,
)
from serviceops_api.notifications.models import (
    DeliveryResultPayload,
    DeliveryResultResponse,
    NotificationEvent,
    OperationalLowStockAlertItem,
    OperationalLowStockAlertResponse,
    OperationalOwnerDailyReportItem,
    OperationalOwnerDailyReportResponse,
    OperationalRequestAlertItem,
    OperationalRequestAlertResponse,
    TelegramOptInLinkPayload,
    TelegramOptInLinkResponse,
)
from serviceops_api.notifications.n8n import N8nDeliveryClient, event_to_dict

logger = logging.getLogger(__name__)


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
    ) -> bool:
        """Persist delivery result metadata."""

    def record_callback_result(self, payload: DeliveryResultPayload) -> bool:
        """Persist an n8n callback payload."""

    def get_by_event_id(self, event_id: str) -> dict[str, Any] | None:
        """Return one delivery attempt by event id."""


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
            logger.info(
                "Notification event duplicate skipped",
                extra={
                    "serviceops_context": {
                        "request_number": request_number,
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "action": "notification.event_duplicate",
                        "target": event.event_id,
                        "outcome": "skipped",
                        "provider": "n8n",
                    }
                },
            )
            return
        logger.info(
            "Notification event queued",
            extra={
                "serviceops_context": {
                    "request_number": request_number,
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "action": "notification.event_queued",
                    "target": event.event_id,
                    "outcome": "succeeded",
                    "provider": "n8n",
                }
            },
        )
        result = self._n8n_client.deliver(event_to_dict(event))
        status = result.get("status", "failed")
        outcome = "succeeded" if status in {"sent", "queued"} else "failed"
        recorded = self._notification_store.record_delivery_result(
            event_id=event.event_id,
            status=status,
            provider_message_id=result.get("provider_message_id") or None,
            error=result.get("error") or None,
            attempt_count=1,
        )
        if not recorded:
            outcome = "skipped"
        context: dict[str, object] = {
            "request_number": request_number,
            "event_id": event.event_id,
            "event_type": event.event_type,
            "action": "notification.delivery_recorded",
            "target": event.event_id,
            "outcome": outcome,
            "provider": "n8n",
        }
        if result.get("error"):
            context["reason"] = "delivery_failed"
        if not recorded:
            context["reason"] = "delivery_attempt_not_found"
        logger.info("Notification delivery recorded", extra={"serviceops_context": context})


class RecordN8nDeliveryResult:
    def __init__(self, notification_store: NotificationStore) -> None:
        self._notification_store = notification_store

    def execute(self, payload: DeliveryResultPayload) -> DeliveryResultResponse:
        recorded = self._notification_store.record_callback_result(payload)
        request_number, event_type = _parse_event_id(payload.event_id)
        context: dict[str, object] = {
            "request_number": request_number,
            "event_id": payload.event_id,
            "event_type": event_type,
            "action": "notification.callback_recorded",
            "target": payload.event_id,
            "outcome": _callback_outcome(payload.status) if recorded else "skipped",
            "provider": "n8n",
        }
        if not recorded:
            context["reason"] = "event_not_found"
        logger.info(
            "Notification callback recorded",
            extra={"serviceops_context": context},
        )
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


class OwnerDashboardProvider(Protocol):
    def execute(self, now: datetime | None = None) -> OwnerDashboardResponse:
        """Return backend-owned owner dashboard data."""


class OwnerDailyReportProvider(Protocol):
    def execute(self, now: datetime | None = None) -> OwnerDailyReportResponse:
        """Return backend-owned owner daily report data."""


class OperationalN8nAutomation:
    def __init__(
        self,
        dashboard_provider: OwnerDashboardProvider,
        daily_report_provider: OwnerDailyReportProvider,
        notification_store: NotificationStore,
    ) -> None:
        self._dashboard_provider = dashboard_provider
        self._daily_report_provider = daily_report_provider
        self._notification_store = notification_store

    def sla_reminders(
        self,
        now: datetime | None = None,
        window_key: str | None = None,
        mark_sent: bool = True,
    ) -> OperationalRequestAlertResponse:
        dashboard = self._dashboard_provider.execute(now)
        normalized_window = _window_key(window_key, dashboard.generated_at, "hour")
        return self._request_alerts(
            automation="sla_reminder",
            event_type="operational.sla_reminder",
            generated_at=dashboard.generated_at,
            window_key=normalized_window,
            risks=[risk for risk in dashboard.sla_risks if risk.sla.state == "near_deadline"],
            mark_sent=mark_sent,
        )

    def red_alerts(
        self,
        now: datetime | None = None,
        window_key: str | None = None,
        mark_sent: bool = True,
    ) -> OperationalRequestAlertResponse:
        dashboard = self._dashboard_provider.execute(now)
        normalized_window = _window_key(window_key, dashboard.generated_at, "hour")
        return self._request_alerts(
            automation="red_alert",
            event_type="operational.red_alert",
            generated_at=dashboard.generated_at,
            window_key=normalized_window,
            risks=[risk for risk in dashboard.sla_risks if risk.sla.state == "overdue"],
            mark_sent=mark_sent,
        )

    def owner_daily_report(
        self,
        now: datetime | None = None,
        window_key: str | None = None,
        mark_sent: bool = True,
    ) -> OperationalOwnerDailyReportResponse:
        report = self._daily_report_provider.execute(now)
        normalized_window = _window_key(window_key, report.generated_at, "day")
        event_id = f"operational:owner_daily_report:{normalized_window}:report"
        item = OperationalOwnerDailyReportItem(event_id=event_id, report=_owner_daily_report_payload(report))
        items, suppressed_count = self._deduplicate_items(
            event_type="operational.owner_daily_report",
            request_number="operations",
            items=[item],
            mark_sent=mark_sent,
        )
        return OperationalOwnerDailyReportResponse(
            automation="owner_daily_report",
            generated_at=report.generated_at,
            window_key=normalized_window,
            items=items,
            suppressed_count=suppressed_count,
        )

    def low_stock_alerts(
        self,
        now: datetime | None = None,
        window_key: str | None = None,
        mark_sent: bool = True,
    ) -> OperationalLowStockAlertResponse:
        dashboard = self._dashboard_provider.execute(now)
        normalized_window = _window_key(window_key, dashboard.generated_at, "hour")
        raw_items = [
            _low_stock_item(
                event_id=f"operational:low_stock_alert:{normalized_window}:part-{part.part_id}",
                part=part,
            )
            for part in dashboard.low_stock_risk
        ]
        items, suppressed_count = self._deduplicate_items(
            event_type="operational.low_stock_alert",
            request_number="operations",
            items=raw_items,
            mark_sent=mark_sent,
        )
        return OperationalLowStockAlertResponse(
            automation="low_stock_alert",
            generated_at=dashboard.generated_at,
            window_key=normalized_window,
            items=items,
            suppressed_count=suppressed_count,
        )

    def _request_alerts(
        self,
        *,
        automation: str,
        event_type: str,
        generated_at: str,
        window_key: str,
        risks: list[OwnerSlaRiskItem],
        mark_sent: bool,
    ) -> OperationalRequestAlertResponse:
        raw_items = [
            _request_alert_item(
                event_id=f"operational:{automation}:{window_key}:{risk.request_number}",
                risk=risk,
            )
            for risk in risks
        ]
        items, suppressed_count = self._deduplicate_items(
            event_type=event_type,
            request_number=None,
            items=raw_items,
            mark_sent=mark_sent,
        )
        return OperationalRequestAlertResponse(
            automation=automation,  # type: ignore[arg-type]
            generated_at=generated_at,
            window_key=window_key,
            items=items,
            suppressed_count=suppressed_count,
        )

    def _deduplicate_items(
        self,
        *,
        event_type: str,
        request_number: str | None,
        items: list[Any],
        mark_sent: bool,
    ) -> tuple[list[Any], int]:
        if not mark_sent:
            return items, 0
        kept: list[Any] = []
        suppressed_count = 0
        for item in items:
            item_request_number = request_number or str(item.request_number)
            event = NotificationEvent(
                event_id=str(item.event_id),
                event_type=event_type,  # type: ignore[arg-type]
                request_number=item_request_number,
                payload=item.model_dump(),
            )
            if self._notification_store.create_queued_attempt(event):
                kept.append(item)
                continue
            existing = self._notification_store.get_by_event_id(event.event_id)
            if existing is not None and str(existing["status"]) in {"failed", "retried"}:
                self._notification_store.record_delivery_result(
                    event_id=event.event_id,
                    status="queued",
                    channel=None,
                    provider_message_id=None,
                    error=None,
                    attempt_count=int(existing.get("attempt_count") or 1) + 1,
                )
                kept.append(item)
                continue
            suppressed_count += 1
        return kept, suppressed_count


def _parse_event_id(event_id: str) -> tuple[str, str]:
    if event_id.startswith("operational:"):
        parts = event_id.split(":", 2)
        if len(parts) >= 2:
            return "operations", f"operational.{parts[1]}"
        return "operations", "operational"
    parts = event_id.split(":", 2)
    if len(parts) >= 2:
        return parts[0], parts[1]
    return "", ""


def _callback_outcome(status: str) -> str:
    if status in {"sent", "queued"}:
        return "succeeded"
    if status == "retried":
        return "retried"
    return "failed"


def _request_alert_item(event_id: str, risk: OwnerSlaRiskItem) -> OperationalRequestAlertItem:
    return OperationalRequestAlertItem(
        event_id=event_id,
        request_number=risk.request_number,
        status=risk.status,
        urgency=risk.urgency,
        customer_name=risk.customer_name,
        machine_label=risk.machine_label,
        sla_state=risk.sla.state,
        deadline_at=risk.sla.deadline_at,
        hours_remaining=risk.sla.hours_remaining,
    )


def _low_stock_item(event_id: str, part: LowStockRiskItem) -> OperationalLowStockAlertItem:
    return OperationalLowStockAlertItem(
        event_id=event_id,
        part_id=part.part_id,
        sku=part.sku,
        name=part.name,
        unit=part.unit,
        available_quantity=part.available_quantity,
        low_stock_threshold=part.low_stock_threshold,
    )


def _owner_daily_report_payload(report: OwnerDailyReportResponse) -> dict[str, Any]:
    payload = report.model_dump()
    payload["sla_risks"] = [
        {key: value for key, value in item.items() if key != "latest_event_title"}
        for item in payload.get("sla_risks", [])
    ]
    return payload


def _window_key(value: str | None, generated_at: str, granularity: str) -> str:
    if value is not None and value.strip():
        return value.strip()
    parsed = _parse_generated_at(generated_at)
    if granularity == "day":
        return parsed.date().isoformat()
    return parsed.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_generated_at(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
