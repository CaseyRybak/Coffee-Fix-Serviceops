from __future__ import annotations

from serviceops_api.inventory.models import (
    AdjustReservationPayload,
    CompatibilityPayload,
    CompatibilityRecord,
    CreatePartPayload,
    InventoryPartListResponse,
    PartRecord,
    PartsUsedRecord,
    RecordPartsUsedPayload,
    ReleaseReservationPayload,
    ReservationListResponse,
    ReservationPayload,
    ReservationRecord,
    StockMovementListResponse,
    StockSnapshot,
)
from serviceops_api.inventory.repository import InventoryStore


class CreatePart:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self, payload: CreatePartPayload) -> PartRecord:
        return PartRecord.model_validate(self._repository.create_part(payload))


class AddCompatibility:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self, part_id: int, payload: CompatibilityPayload) -> CompatibilityRecord:
        return CompatibilityRecord.model_validate(self._repository.add_compatibility(part_id, payload))


class ListParts:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self) -> InventoryPartListResponse:
        return InventoryPartListResponse.model_validate({"items": self._repository.list_parts()})


class SetStockCount:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self, part_id: int, quantity_on_hand: int, low_stock_threshold: int | None = None) -> StockSnapshot:
        return StockSnapshot.model_validate(self._repository.set_stock_count(part_id, quantity_on_hand, low_stock_threshold))


class ReservePart:
    def __init__(self, repository: InventoryStore, actor: str = "inventory") -> None:
        self._repository = repository
        self._actor = actor

    def execute(self, payload: ReservationPayload) -> ReservationRecord:
        return ReservationRecord.model_validate(
            self._repository.reserve_part(
                request_number=payload.request_number,
                part_id=payload.part_id,
                quantity=payload.quantity,
                appointment_id=payload.appointment_id,
                note=payload.note,
                actor=self._actor,
            )
        )


class AdjustReservation:
    def __init__(self, repository: InventoryStore, actor: str = "inventory") -> None:
        self._repository = repository
        self._actor = actor

    def execute(self, reservation_id: int, payload: AdjustReservationPayload) -> ReservationRecord:
        return ReservationRecord.model_validate(
            self._repository.adjust_reservation(reservation_id, payload.quantity, payload.note, self._actor)
        )


class ReleaseReservation:
    def __init__(self, repository: InventoryStore, actor: str = "inventory") -> None:
        self._repository = repository
        self._actor = actor

    def execute(self, reservation_id: int, payload: ReleaseReservationPayload) -> ReservationRecord:
        return ReservationRecord.model_validate(
            self._repository.release_reservation(reservation_id, payload.note, self._actor)
        )


class ListReservations:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self, request_number: str | None = None) -> ReservationListResponse:
        return ReservationListResponse.model_validate({"items": self._repository.list_reservations(request_number)})


class ListStockMovements:
    def __init__(self, repository: InventoryStore) -> None:
        self._repository = repository

    def execute(self, part_id: int | None = None, request_number: str | None = None) -> StockMovementListResponse:
        return StockMovementListResponse.model_validate(
            {"items": self._repository.list_stock_movements(part_id=part_id, request_number=request_number)}
        )


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
