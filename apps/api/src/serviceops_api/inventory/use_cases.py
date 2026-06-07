from __future__ import annotations

from serviceops_api.inventory.models import (
    CreatePartPayload,
    InventoryPartListResponse,
    PartRecord,
    PartsUsedRecord,
    RecordPartsUsedPayload,
    StockSnapshot,
)
from serviceops_api.inventory.repository import InventoryStore


class CreatePart:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self, payload: CreatePartPayload) -> PartRecord:
        return PartRecord.model_validate(self._repository.create_part(payload))


class ListParts:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self) -> InventoryPartListResponse:
        return InventoryPartListResponse.model_validate({"items": self._repository.list_parts()})


class SetStockCount:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self, part_id: int, quantity_on_hand: int) -> StockSnapshot:
        return StockSnapshot.model_validate(self._repository.set_stock_count(part_id, quantity_on_hand))


class RecordPartsUsed:
    def __init__(self, repository: InventoryStore, actor: str = "technician") -> None:
        self._repository = repository
        self._actor = actor

    def execute(self, request_number: str, payload: RecordPartsUsedPayload) -> PartsUsedRecord:
        return PartsUsedRecord.model_validate(
            self._repository.record_parts_used(
                request_number=request_number,
                part_id=payload.part_id,
                quantity=payload.quantity,
                note=payload.note,
                actor=self._actor,
            )
        )
