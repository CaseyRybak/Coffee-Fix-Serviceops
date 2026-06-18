from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


NotificationEventType = Literal[
    "service_request.created",
    "service_request.status_changed",
    "service_request.clarification_requested",
    "service_request.customer_answered",
    "operational.sla_reminder",
    "operational.red_alert",
    "operational.owner_daily_report",
    "operational.low_stock_alert",
]
DeliveryStatus = Literal["queued", "sent", "failed", "retried"]


class NotificationEvent(BaseModel):
    event_id: str
    event_type: NotificationEventType
    request_number: str
    payload: dict[str, Any]


class DeliveryAttempt(BaseModel):
    event_id: str
    event_type: str
    request_number: str
    status: DeliveryStatus
    channel: str | None = None
    provider_message_id: str | None = None
    error: str | None = None
    attempt_count: int = 1
    created_at: str | None = None
    updated_at: str | None = None


class DeliveryResultPayload(BaseModel):
    event_id: str = Field(min_length=1, max_length=240)
    status: DeliveryStatus
    channel: str | None = Field(default=None, max_length=80)
    provider_message_id: str | None = Field(default=None, max_length=160)
    error: str | None = Field(default=None, max_length=500)
    attempt_count: int = Field(default=1, ge=1)

    @field_validator("event_id")
    @classmethod
    def clean_event_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field is required")
        return cleaned


class DeliveryResultResponse(BaseModel):
    event_id: str
    status: DeliveryStatus


class TelegramOptInLinkPayload(BaseModel):
    chat_id: int
    username: str | None = Field(default=None, max_length=120)


class TelegramOptInLinkResponse(BaseModel):
    request_number: str
    status: str
    customer_name: str
    machine_label: str
    public_status_url: str
    message: str


class OperationalRequestAlertItem(BaseModel):
    event_id: str
    request_number: str
    status: str
    urgency: str
    customer_name: str
    machine_label: str
    sla_state: str
    deadline_at: str | None
    hours_remaining: float | None
    dashboard_url: str = "/owner"


class OperationalLowStockAlertItem(BaseModel):
    event_id: str
    part_id: int
    sku: str
    name: str
    unit: str
    available_quantity: int
    low_stock_threshold: int | None
    dashboard_url: str = "/owner"


class OperationalOwnerDailyReportItem(BaseModel):
    event_id: str
    report: dict[str, Any]


class OperationalRequestAlertResponse(BaseModel):
    automation: Literal["sla_reminder", "red_alert"]
    generated_at: str
    window_key: str
    items: list[OperationalRequestAlertItem]
    suppressed_count: int = 0


class OperationalLowStockAlertResponse(BaseModel):
    automation: Literal["low_stock_alert"]
    generated_at: str
    window_key: str
    items: list[OperationalLowStockAlertItem]
    suppressed_count: int = 0


class OperationalOwnerDailyReportResponse(BaseModel):
    automation: Literal["owner_daily_report"]
    generated_at: str
    window_key: str
    items: list[OperationalOwnerDailyReportItem]
    suppressed_count: int = 0
