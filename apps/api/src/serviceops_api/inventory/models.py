from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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


class CreatePartPayload(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    brand: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    unit: str = Field(min_length=1, max_length=40)
    compatibility_note: str | None = Field(default=None, max_length=500)

    _clean_sku = field_validator("sku")(_clean_required)
    _clean_name = field_validator("name")(_clean_required)
    _clean_brand = field_validator("brand")(_clean_optional)
    _clean_model = field_validator("model")(_clean_optional)
    _clean_unit = field_validator("unit")(_clean_required)
    _clean_compatibility_note = field_validator("compatibility_note")(_clean_optional)


class PartRecord(BaseModel):
    part_id: int
    sku: str
    name: str
    brand: str | None
    model: str | None
    unit: str
    compatibility_note: str | None
    created_at: str


class InventoryPartItem(PartRecord):
    quantity_on_hand: int
    stock_updated_at: str | None


class InventoryPartListResponse(BaseModel):
    items: list[InventoryPartItem]


class StockCountPayload(BaseModel):
    quantity_on_hand: int = Field(ge=0)


class StockSnapshot(BaseModel):
    part_id: int
    quantity_on_hand: int
    updated_at: str


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
