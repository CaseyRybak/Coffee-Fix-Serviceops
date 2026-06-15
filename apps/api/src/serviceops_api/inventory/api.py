from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.inventory.models import (
    AdjustReservationPayload,
    CompatibilityPayload,
    CompatibilityRecord,
    CreatePartPayload,
    InventoryPartListResponse,
    PartRecord,
    ReleaseReservationPayload,
    ReservationListResponse,
    ReservationPayload,
    ReservationRecord,
    StockCountPayload,
    StockMovementListResponse,
    StockSnapshot,
)
from serviceops_api.inventory.repository import DuplicatePartError, InsufficientStockError
from serviceops_api.inventory.use_cases import (
    AddCompatibility,
    AdjustReservation,
    CreatePart,
    ListParts,
    ListReservations,
    ListStockMovements,
    ReleaseReservation,
    ReservePart,
    SetStockCount,
)


def create_inventory_router(
    create_part: CreatePart,
    add_compatibility: AddCompatibility,
    list_parts: ListParts,
    set_stock_count: SetStockCount,
    reserve_part: ReservePart,
    adjust_reservation: AdjustReservation,
    release_reservation: ReleaseReservation,
    list_reservations: ListReservations,
    list_movements: ListStockMovements,
    staff_dependency: Depends | None = None,
    read_dependency: Depends | None = None,
    low_stock_dependency: Depends | None = None,
) -> APIRouter:
    dependencies = [Depends(staff_dependency)] if staff_dependency is not None else []
    read_dependencies = [Depends(read_dependency)] if read_dependency is not None else dependencies
    low_stock_dependencies = [Depends(low_stock_dependency)] if low_stock_dependency is not None else dependencies
    router = APIRouter(prefix="/inventory", tags=["inventory"])

    @router.get("/parts", response_model=InventoryPartListResponse, dependencies=read_dependencies)
    async def get_parts() -> InventoryPartListResponse:
        return list_parts.execute()

    @router.get("/low-stock", response_model=InventoryPartListResponse, dependencies=low_stock_dependencies)
    async def get_low_stock_parts() -> InventoryPartListResponse:
        parts = list_parts.execute()
        return InventoryPartListResponse.model_validate({"items": [part for part in parts.items if part.is_low_stock]})

    @router.post("/parts", response_model=PartRecord, status_code=status.HTTP_201_CREATED, dependencies=dependencies)
    async def create_inventory_part(payload: CreatePartPayload) -> PartRecord:
        try:
            return create_part.execute(payload)
        except DuplicatePartError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post(
        "/parts/{part_id}/compatibility",
        response_model=CompatibilityRecord,
        status_code=status.HTTP_201_CREATED,
        dependencies=dependencies,
    )
    async def create_part_compatibility(part_id: int, payload: CompatibilityPayload) -> CompatibilityRecord:
        try:
            return add_compatibility.execute(part_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found") from exc

    @router.post("/parts/{part_id}/stock", response_model=StockSnapshot, dependencies=dependencies)
    async def update_stock_count(part_id: int, payload: StockCountPayload) -> StockSnapshot:
        try:
            return set_stock_count.execute(part_id, payload.quantity_on_hand, payload.low_stock_threshold)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found") from exc

    @router.post("/reservations", response_model=ReservationRecord, status_code=status.HTTP_201_CREATED, dependencies=dependencies)
    async def create_reservation(payload: ReservationPayload) -> ReservationRecord:
        try:
            return reserve_part.execute(payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found") from exc
        except InsufficientStockError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post("/reservations/{reservation_id}/adjust", response_model=ReservationRecord, dependencies=dependencies)
    async def update_reservation(reservation_id: int, payload: AdjustReservationPayload) -> ReservationRecord:
        try:
            return adjust_reservation.execute(reservation_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found") from exc
        except InsufficientStockError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post("/reservations/{reservation_id}/release", response_model=ReservationRecord, dependencies=dependencies)
    async def release_inventory_reservation(reservation_id: int, payload: ReleaseReservationPayload) -> ReservationRecord:
        try:
            return release_reservation.execute(reservation_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found") from exc

    @router.get("/reservations", response_model=ReservationListResponse, dependencies=dependencies)
    async def get_reservations(request_number: str | None = None) -> ReservationListResponse:
        return list_reservations.execute(request_number)

    @router.get("/movements", response_model=StockMovementListResponse, dependencies=dependencies)
    async def get_movements(part_id: int | None = None, request_number: str | None = None) -> StockMovementListResponse:
        return list_movements.execute(part_id=part_id, request_number=request_number)

    return router
