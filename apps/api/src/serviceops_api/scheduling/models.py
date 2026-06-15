from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


AppointmentStatus = Literal["scheduled", "rescheduled", "cancelled"]


class SchedulingConflictError(RuntimeError):
    pass


class SchedulingLifecycleError(RuntimeError):
    pass


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Field is required")
    return cleaned


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def parse_appointment_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Appointment datetime must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("Appointment datetime must include timezone offset")
    return parsed


def validate_window(starts_at: str, ends_at: str) -> None:
    if parse_appointment_datetime(ends_at) <= parse_appointment_datetime(starts_at):
        raise ValueError("Appointment end must be after start")


class AppointmentWindowPayload(BaseModel):
    technician_identifier: str = Field(min_length=1, max_length=180)
    technician_name: str | None = Field(default=None, max_length=120)
    starts_at: str = Field(min_length=1, max_length=40)
    ends_at: str = Field(min_length=1, max_length=40)
    window_label: str | None = Field(default=None, max_length=160)

    _clean_technician_identifier = field_validator("technician_identifier")(_clean_required)
    _clean_technician_name = field_validator("technician_name")(_clean_optional)
    _clean_starts_at = field_validator("starts_at")(_clean_required)
    _clean_ends_at = field_validator("ends_at")(_clean_required)
    _clean_window_label = field_validator("window_label")(_clean_optional)

    @model_validator(mode="after")
    def _validate_window(self) -> "AppointmentWindowPayload":
        validate_window(self.starts_at, self.ends_at)
        return self


class RescheduleAppointmentPayload(BaseModel):
    starts_at: str = Field(min_length=1, max_length=40)
    ends_at: str = Field(min_length=1, max_length=40)
    window_label: str | None = Field(default=None, max_length=160)
    reason: str | None = Field(default=None, max_length=500)

    _clean_starts_at = field_validator("starts_at")(_clean_required)
    _clean_ends_at = field_validator("ends_at")(_clean_required)
    _clean_window_label = field_validator("window_label")(_clean_optional)
    _clean_reason = field_validator("reason")(_clean_optional)

    @model_validator(mode="after")
    def _validate_window(self) -> "RescheduleAppointmentPayload":
        validate_window(self.starts_at, self.ends_at)
        return self


class CancelAppointmentPayload(BaseModel):
    reason: str | None = Field(default=None, max_length=500)

    _clean_reason = field_validator("reason")(_clean_optional)


class PublicAppointmentSnapshot(BaseModel):
    starts_at: str
    ends_at: str
    window_label: str
    status: AppointmentStatus


class AppointmentSnapshot(PublicAppointmentSnapshot):
    appointment_id: int
    request_number: str
    technician_identifier: str
    technician_name: str
    reschedule_reason: str | None = None
    cancel_reason: str | None = None
    created_at: str
    updated_at: str


class StaffAppointmentResponse(BaseModel):
    request_number: str
    status: str
    appointment: AppointmentSnapshot
    message: str


class ScheduleListItem(BaseModel):
    appointment: AppointmentSnapshot
    request_status: str
    customer_name: str
    machine_label: str
    urgency: str
    address: str
    latest_event_title: str


class ScheduleListResponse(BaseModel):
    items: list[ScheduleListItem]
