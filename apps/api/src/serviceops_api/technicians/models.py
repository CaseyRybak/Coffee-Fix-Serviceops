from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from serviceops_api.service_requests.models import PublicAppointmentSnapshot, RequestStatus, Urgency
from serviceops_api.inventory.models import RecordPartsUsedPayload


RepairResult = Literal["completed", "waiting_for_parts", "follow_up_required"]


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


class TechnicianRequestListItem(BaseModel):
    request_number: str
    status: RequestStatus
    customer_name: str
    machine_label: str
    urgency: Urgency
    address: str
    visit_window: str | None
    appointment: PublicAppointmentSnapshot | None = None
    latest_event_title: str


class TechnicianRequestListResponse(BaseModel):
    items: list[TechnicianRequestListItem]


class DiagnosisChecklistPayload(BaseModel):
    machine_powered_on: bool
    water_supply_checked: bool
    leak_checked: bool
    error_code_checked: bool
    summary: str = Field(min_length=1, max_length=1000)

    _clean_summary = field_validator("summary")(_clean_required)


class DiagnosisSnapshot(DiagnosisChecklistPayload):
    actor: str
    created_at: str


class RepairResultPayload(BaseModel):
    result: RepairResult
    summary: str = Field(min_length=1, max_length=1000)
    next_step: str | None = Field(default=None, max_length=500)

    _clean_summary = field_validator("summary")(_clean_required)
    _clean_next_step = field_validator("next_step")(_clean_optional)


class RepairResultSnapshot(RepairResultPayload):
    actor: str
    created_at: str


class TechnicianRequestDetail(BaseModel):
    request_number: str
    status: RequestStatus
    customer_name: str
    customer_phone: str
    machine_label: str
    problem: str
    address: str
    urgency: Urgency
    visit_window: str | None
    appointment: PublicAppointmentSnapshot | None = None
    diagnosis: DiagnosisSnapshot | None
    repair_result: RepairResultSnapshot | None


class TechnicianActionResponse(BaseModel):
    request_number: str
    status: RequestStatus
    message: str
