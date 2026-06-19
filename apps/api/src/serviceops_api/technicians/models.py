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


def _clean_text_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


class TechnicianProfilePayload(BaseModel):
    active: bool = True
    skill_brands: list[str] = Field(default_factory=list, max_length=12)
    service_regions: list[str] = Field(default_factory=list, max_length=12)
    notes: str | None = Field(default=None, max_length=500)

    _clean_notes = field_validator("notes")(_clean_optional)

    @field_validator("skill_brands", "service_regions")
    @classmethod
    def _clean_lists(cls, values: list[str]) -> list[str]:
        return _clean_text_list(values)


class TechnicianProfileSnapshot(BaseModel):
    staff_username: str
    display_name: str
    phone: str
    staff_active: bool
    active: bool
    skill_brands: list[str]
    service_regions: list[str]
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TechnicianProfileListResponse(BaseModel):
    items: list[TechnicianProfileSnapshot]


class TechnicianRecommendationRequestSnapshot(BaseModel):
    request_number: str
    brand: str
    model: str | None
    address: str
    urgency: Urgency
    status: RequestStatus


class TechnicianRecommendationItem(BaseModel):
    staff_username: str
    display_name: str
    phone: str
    score: int
    active: bool
    staff_active: bool
    skill_brands: list[str]
    service_regions: list[str]
    scheduled_visit_count: int
    reasons: list[str]
    risks: list[str]


class TechnicianRecommendationResponse(BaseModel):
    request: TechnicianRecommendationRequestSnapshot
    items: list[TechnicianRecommendationItem]
