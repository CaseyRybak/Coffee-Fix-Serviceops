from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ClientType = Literal["private", "office", "coffee_shop", "restaurant", "other"]
LocationType = Literal["home", "office", "coffee_shop", "restaurant", "other"]
Urgency = Literal["today", "one_two_days", "planned"]
RequestStatus = Literal[
    "new",
    "needs_clarification",
    "awaiting_assignment",
    "technician_assigned",
    "visit_scheduled",
    "diagnostics",
    "waiting_for_parts",
    "repair_in_progress",
    "completed",
    "closed",
    "warranty_case",
    "cancelled",
]


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


class CustomerIntake(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=40)
    telegram: str | None = Field(default=None, max_length=80)
    client_type: ClientType

    _clean_name = field_validator("name")(_clean_required)
    _clean_phone = field_validator("phone")(_clean_required)
    _clean_telegram = field_validator("telegram")(_clean_optional)


class MachineIntake(BaseModel):
    brand: str = Field(min_length=1, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    location_type: LocationType

    _clean_brand = field_validator("brand")(_clean_required)
    _clean_model = field_validator("model")(_clean_optional)


class AttachmentMetadata(BaseModel):
    filename: str = Field(min_length=1, max_length=180)
    content_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(ge=1)

    _clean_filename = field_validator("filename")(_clean_required)
    _clean_content_type = field_validator("content_type")(_clean_required)


class CreateServiceRequestPayload(BaseModel):
    customer: CustomerIntake
    machine: MachineIntake
    problem: str = Field(min_length=1, max_length=2000)
    address: str = Field(min_length=1, max_length=240)
    urgency: Urgency
    attachment_metadata: list[AttachmentMetadata] = Field(default_factory=list, max_length=5)

    _clean_problem = field_validator("problem")(_clean_required)
    _clean_address = field_validator("address")(_clean_required)


class ServiceRequestRecord(BaseModel):
    request_number: str
    status: RequestStatus
    customer: CustomerIntake
    machine: MachineIntake
    problem: str
    address: str
    urgency: Urgency
    attachment_metadata: list[AttachmentMetadata]

    model_config = ConfigDict(frozen=True)


class CreateServiceRequestResponse(BaseModel):
    request_number: str
    status: RequestStatus
    message: str


class PublicCustomerSnapshot(BaseModel):
    name: str
    phone_masked: str
    telegram: str | None


class PublicMachineSnapshot(BaseModel):
    brand: str
    model: str | None


class StatusEvent(BaseModel):
    status: RequestStatus
    title: str
    description: str
    actor: str
    created_at: str


class ClarificationSnapshot(BaseModel):
    question_id: int
    question: str
    answer: str | None
    answered_at: str | None


class TelegramOptInSnapshot(BaseModel):
    enabled: bool
    link: str


class PublicStatusResponse(BaseModel):
    request_number: str
    public_token: str
    status: RequestStatus
    customer: PublicCustomerSnapshot
    machine: PublicMachineSnapshot
    problem_summary: str
    timeline: list[StatusEvent]
    clarification: ClarificationSnapshot | None
    telegram_opt_in: TelegramOptInSnapshot


class CustomerAnswerPayload(BaseModel):
    question_id: int = Field(gt=0)
    answer: str = Field(min_length=1, max_length=2000)

    _clean_answer = field_validator("answer")(_clean_required)


class CustomerAnswerResponse(BaseModel):
    request_number: str
    status: RequestStatus
    message: str


class TelegramOptInPayload(BaseModel):
    telegram: str | None = Field(default=None, max_length=80)

    _clean_telegram = field_validator("telegram")(_clean_optional)


class TelegramOptInResponse(BaseModel):
    request_number: str
    telegram: str | None
    token: str
    link: str


class DispatcherRequestListItem(BaseModel):
    request_number: str
    status: RequestStatus
    customer_name: str
    customer_phone: str
    machine_label: str
    urgency: Urgency
    address: str
    created_at: str
    latest_event_title: str


class DispatcherRequestListResponse(BaseModel):
    items: list[DispatcherRequestListItem]


class DispatcherAssignmentSnapshot(BaseModel):
    technician_name: str | None
    technician_phone: str | None
    technician_region: str | None
    visit_window: str | None


class DispatcherInternalNote(BaseModel):
    note: str
    actor: str
    created_at: str


class DispatcherAiSuggestionSource(BaseModel):
    document_title: str
    source_uri: str | None
    chunk_id: int
    score: float


class DispatcherAiSuggestion(BaseModel):
    suggestion_id: int
    kind: str
    title: str
    content: str
    rationale: str
    confidence: float
    status: str
    source_chunks: list[DispatcherAiSuggestionSource] = Field(default_factory=list)
    created_at: str
    acted_at: str | None = None


class DispatcherNotificationDelivery(BaseModel):
    event_id: str
    event_type: str
    status: str
    channel: str | None = None
    provider_message_id: str | None = None
    error: str | None = None
    attempt_count: int
    created_at: str | None = None
    updated_at: str | None = None


class DispatcherRequestDetail(BaseModel):
    request_number: str
    status: RequestStatus
    customer: CustomerIntake
    machine: MachineIntake
    problem: str
    address: str
    urgency: Urgency
    created_at: str
    timeline: list[StatusEvent]
    clarification: ClarificationSnapshot | None
    assignment: DispatcherAssignmentSnapshot
    internal_notes: list[DispatcherInternalNote]
    ai_suggestions: list[DispatcherAiSuggestion] = Field(default_factory=list)
    notification_deliveries: list[DispatcherNotificationDelivery] = Field(default_factory=list)


class DispatcherStatusUpdatePayload(BaseModel):
    status: RequestStatus
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=500)

    _clean_title = field_validator("title")(_clean_required)
    _clean_description = field_validator("description")(_clean_required)


class DispatcherClarificationPayload(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    _clean_question = field_validator("question")(_clean_required)


class DispatcherAssignmentPayload(BaseModel):
    technician_name: str = Field(min_length=1, max_length=120)
    technician_phone: str | None = Field(default=None, max_length=40)
    technician_region: str | None = Field(default=None, max_length=120)
    visit_window: str | None = Field(default=None, max_length=160)

    _clean_technician_name = field_validator("technician_name")(_clean_required)
    _clean_technician_phone = field_validator("technician_phone")(_clean_optional)
    _clean_technician_region = field_validator("technician_region")(_clean_optional)
    _clean_visit_window = field_validator("visit_window")(_clean_optional)


class DispatcherInternalNotePayload(BaseModel):
    note: str = Field(min_length=1, max_length=2000)

    _clean_note = field_validator("note")(_clean_required)


class DispatcherActionResponse(BaseModel):
    request_number: str
    status: RequestStatus
    message: str
