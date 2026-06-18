from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


ReservationStatus = Literal["active", "released", "consumed"]
StockMovementType = Literal[
    "manual_adjustment",
    "reservation_created",
    "reservation_adjusted",
    "release",
    "consumption",
    "procurement_receipt",
]
CompatibilityLevel = Literal["exact_model", "series", "generic_group"]
PurchaseRequestStatus = Literal["draft", "pending_approval", "approved", "ordered", "received", "cancelled"]


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Field is required")
    return cleaned


def _clean_unit(value: str) -> str:
    cleaned = _clean_required(value)
    if cleaned.isdigit():
        raise ValueError("Unit must be a text code like pcs, kit, set, or ml")
    return cleaned


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class CreatePartPayload(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    brand: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    unit: str = Field(min_length=1, max_length=40)
    compatibility_note: str | None = Field(default=None, max_length=500)
    part_type: str | None = Field(default=None, max_length=80)
    parameter_label: str | None = Field(default=None, max_length=80)
    parameter_value: str | None = Field(default=None, max_length=80)
    parameter_unit: str | None = Field(default=None, max_length=40)

    _clean_sku = field_validator("sku")(_clean_required)
    _clean_name = field_validator("name")(_clean_required)
    _clean_brand = field_validator("brand")(_clean_optional)
    _clean_model = field_validator("model")(_clean_optional)
    _clean_unit = field_validator("unit")(_clean_unit)
    _clean_compatibility_note = field_validator("compatibility_note")(_clean_optional)
    _clean_part_type = field_validator("part_type")(_clean_optional)
    _clean_parameter_label = field_validator("parameter_label")(_clean_optional)
    _clean_parameter_value = field_validator("parameter_value")(_clean_optional)
    _clean_parameter_unit = field_validator("parameter_unit")(_clean_optional)


class CompatibilityPayload(BaseModel):
    compatibility_level: CompatibilityLevel
    brand: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    series: str | None = Field(default=None, max_length=120)
    machine_family: str | None = Field(default=None, max_length=120)
    note: str | None = Field(default=None, max_length=500)

    _clean_brand = field_validator("brand")(_clean_optional)
    _clean_model = field_validator("model")(_clean_optional)
    _clean_series = field_validator("series")(_clean_optional)
    _clean_machine_family = field_validator("machine_family")(_clean_optional)
    _clean_note = field_validator("note")(_clean_optional)

    @model_validator(mode="after")
    def require_level_identity(self) -> "CompatibilityPayload":
        if self.compatibility_level == "exact_model" and (not self.brand or not self.model):
            raise ValueError("Exact model compatibility requires brand and model")
        if self.compatibility_level == "series" and not self.series:
            raise ValueError("Series compatibility requires series")
        if self.compatibility_level == "generic_group" and not self.machine_family:
            raise ValueError("Generic group compatibility requires machine_family")
        return self


class CompatibilityRecord(CompatibilityPayload):
    compatibility_id: int
    part_id: int
    created_at: str


class PartRecord(BaseModel):
    part_id: int
    sku: str
    name: str
    brand: str | None
    model: str | None
    unit: str
    compatibility_note: str | None
    part_type: str | None = None
    parameter_label: str | None = None
    parameter_value: str | None = None
    parameter_unit: str | None = None
    factual_key: str | None = None
    compatibility: list[CompatibilityRecord] = Field(default_factory=list)
    created_at: str


class InventoryPartItem(PartRecord):
    quantity_on_hand: int
    reserved_quantity: int = 0
    available_quantity: int = 0
    low_stock_threshold: int | None = None
    is_low_stock: bool = False
    stock_updated_at: str | None


class InventoryPartListResponse(BaseModel):
    items: list[InventoryPartItem]


class StockCountPayload(BaseModel):
    quantity_on_hand: int = Field(ge=0)
    low_stock_threshold: int | None = Field(default=None, ge=0)


class StockSnapshot(BaseModel):
    part_id: int
    quantity_on_hand: int
    reserved_quantity: int = 0
    available_quantity: int = 0
    low_stock_threshold: int | None = None
    is_low_stock: bool = False
    updated_at: str


class ReservationPayload(BaseModel):
    request_number: str = Field(min_length=1, max_length=80)
    part_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    appointment_id: int | None = Field(default=None, gt=0)
    note: str | None = Field(default=None, max_length=500)

    _clean_request_number = field_validator("request_number")(_clean_required)
    _clean_note = field_validator("note")(_clean_optional)


class AdjustReservationPayload(BaseModel):
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_optional)


class ReleaseReservationPayload(BaseModel):
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_optional)


class ReservationRecord(BaseModel):
    reservation_id: int
    request_number: str
    appointment_id: int | None = None
    part_id: int
    sku: str
    part_name: str
    quantity: int
    status: ReservationStatus
    note: str | None = None
    actor: str
    created_at: str
    updated_at: str


class ReservationListResponse(BaseModel):
    items: list[ReservationRecord]


class StockMovementRecord(BaseModel):
    movement_id: int
    part_id: int
    sku: str
    part_name: str
    movement_type: StockMovementType
    quantity: int
    quantity_on_hand_after: int
    reserved_quantity_after: int
    available_quantity_after: int
    request_number: str | None = None
    reservation_id: int | None = None
    note: str | None = None
    actor: str
    created_at: str


class StockMovementListResponse(BaseModel):
    items: list[StockMovementRecord]


class SupplierPayload(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    contact_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=180)
    note: str | None = Field(default=None, max_length=500)

    _clean_name = field_validator("name")(_clean_required)
    _clean_contact_name = field_validator("contact_name")(_clean_optional)
    _clean_phone = field_validator("phone")(_clean_optional)
    _clean_email = field_validator("email")(_clean_optional)
    _clean_note = field_validator("note")(_clean_optional)


class SupplierRecord(SupplierPayload):
    supplier_id: int
    active: bool = True
    created_at: str
    updated_at: str


class SupplierListResponse(BaseModel):
    items: list[SupplierRecord]


class PurchaseRequestItemPayload(BaseModel):
    part_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_optional)


class CreatePurchaseRequestPayload(BaseModel):
    supplier_id: int = Field(gt=0)
    items: list[PurchaseRequestItemPayload] = Field(min_length=1)
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_optional)


class LowStockPurchaseDraftPayload(BaseModel):
    supplier_id: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_optional)


class PurchaseRequestActionPayload(BaseModel):
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_optional)


class PurchaseRequestItemRecord(BaseModel):
    item_id: int
    purchase_request_id: int
    part_id: int
    sku: str
    part_name: str
    unit: str
    quantity: int
    note: str | None = None


class PurchaseRequestRecord(BaseModel):
    purchase_request_id: int
    supplier_id: int
    supplier_name: str
    status: PurchaseRequestStatus
    note: str | None = None
    actor: str
    items: list[PurchaseRequestItemRecord] = Field(default_factory=list)
    created_at: str
    updated_at: str


class PurchaseRequestListResponse(BaseModel):
    items: list[PurchaseRequestRecord]


class RecordPartsUsedPayload(BaseModel):
    part_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)

    _clean_note = field_validator("note")(_clean_optional)


class PartsUsedRecord(BaseModel):
    request_number: str
    part_id: int
    sku: str
    part_name: str
    quantity: int
    unit: str
    note: str | None
    quantity_on_hand: int
    stock_after_use: int
    actor: str
    created_at: str
