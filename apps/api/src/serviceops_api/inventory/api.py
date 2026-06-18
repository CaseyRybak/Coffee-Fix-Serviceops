from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.inventory.models import (
    AdjustReservationPayload,
    CompatibilityPayload,
    CompatibilityRecord,
    CreatePurchaseRequestPayload,
    CreatePartPayload,
    InventoryPartListResponse,
    LowStockPurchaseDraftPayload,
    PartRecord,
    PurchaseRequestActionPayload,
    PurchaseRequestItemPayload,
    PurchaseRequestListResponse,
    PurchaseRequestRecord,
    ReleaseReservationPayload,
    ReservationListResponse,
    ReservationPayload,
    ReservationRecord,
    StockCountPayload,
    StockMovementListResponse,
    StockSnapshot,
    SupplierListResponse,
    SupplierPayload,
    SupplierRecord,
)
from serviceops_api.inventory.repository import DuplicatePartError, InsufficientStockError, InvalidPurchaseRequestTransitionError
from serviceops_api.inventory.use_cases import (
    AddCompatibility,
    AdjustReservation,
    ApprovePurchaseRequest,
    CancelPurchaseRequest,
    CreateLowStockPurchaseDraft,
    CreatePart,
    CreatePurchaseRequest,
    CreateSupplier,
    GetPurchaseRequest,
    ListParts,
    ListPurchaseRequests,
    ListReservations,
    ListStockMovements,
    ListSuppliers,
    MarkPurchaseRequestOrdered,
    ReceivePurchaseRequest,
    ReleaseReservation,
    ReplacePurchaseRequestItems,
    ReservePart,
    SetStockCount,
    SubmitPurchaseRequest,
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
    create_supplier: CreateSupplier,
    list_suppliers: ListSuppliers,
    create_purchase_request: CreatePurchaseRequest,
    list_purchase_requests: ListPurchaseRequests,
    get_purchase_request: GetPurchaseRequest,
    replace_purchase_items: ReplacePurchaseRequestItems,
    submit_purchase_request: SubmitPurchaseRequest,
    approve_purchase_request: ApprovePurchaseRequest,
    mark_purchase_request_ordered: MarkPurchaseRequestOrdered,
    receive_purchase_request: ReceivePurchaseRequest,
    cancel_purchase_request: CancelPurchaseRequest,
    create_low_stock_purchase_draft: CreateLowStockPurchaseDraft,
    staff_dependency: Depends | None = None,
    read_dependency: Depends | None = None,
    low_stock_dependency: Depends | None = None,
    procurement_read_dependency: Depends | None = None,
    procurement_approval_dependency: Depends | None = None,
) -> APIRouter:
    dependencies = [Depends(staff_dependency)] if staff_dependency is not None else []
    read_dependencies = [Depends(read_dependency)] if read_dependency is not None else dependencies
    low_stock_dependencies = [Depends(low_stock_dependency)] if low_stock_dependency is not None else dependencies
    procurement_read_dependencies = [Depends(procurement_read_dependency)] if procurement_read_dependency is not None else dependencies
    procurement_approval_dependencies = (
        [Depends(procurement_approval_dependency)] if procurement_approval_dependency is not None else dependencies
    )
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

    @router.post(
        "/procurement/suppliers",
        response_model=SupplierRecord,
        status_code=status.HTTP_201_CREATED,
        dependencies=dependencies,
    )
    async def create_procurement_supplier(payload: SupplierPayload) -> SupplierRecord:
        return create_supplier.execute(payload)

    @router.get(
        "/procurement/suppliers",
        response_model=SupplierListResponse,
        dependencies=procurement_read_dependencies,
    )
    async def get_procurement_suppliers() -> SupplierListResponse:
        return list_suppliers.execute()

    @router.post(
        "/procurement/purchase-requests",
        response_model=PurchaseRequestRecord,
        status_code=status.HTTP_201_CREATED,
        dependencies=dependencies,
    )
    async def create_procurement_purchase_request(payload: CreatePurchaseRequestPayload) -> PurchaseRequestRecord:
        try:
            return create_purchase_request.execute_payload(payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier or part not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.get(
        "/procurement/purchase-requests",
        response_model=PurchaseRequestListResponse,
        dependencies=procurement_read_dependencies,
    )
    async def get_procurement_purchase_requests() -> PurchaseRequestListResponse:
        return list_purchase_requests.execute()

    @router.get(
        "/procurement/purchase-requests/{purchase_request_id}",
        response_model=PurchaseRequestRecord,
        dependencies=procurement_read_dependencies,
    )
    async def get_procurement_purchase_request(purchase_request_id: int) -> PurchaseRequestRecord:
        try:
            return get_purchase_request.execute(purchase_request_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase request not found") from exc

    @router.post(
        "/procurement/purchase-requests/{purchase_request_id}/items",
        response_model=PurchaseRequestRecord,
        dependencies=dependencies,
    )
    async def update_procurement_purchase_request_items(
        purchase_request_id: int,
        payload: list[PurchaseRequestItemPayload],
    ) -> PurchaseRequestRecord:
        try:
            return replace_purchase_items.execute(purchase_request_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase request or part not found") from exc
        except (InvalidPurchaseRequestTransitionError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post(
        "/procurement/purchase-requests/low-stock-draft",
        response_model=PurchaseRequestRecord,
        status_code=status.HTTP_201_CREATED,
        dependencies=dependencies,
    )
    async def create_procurement_low_stock_draft(payload: LowStockPurchaseDraftPayload) -> PurchaseRequestRecord:
        try:
            return create_low_stock_purchase_draft.execute_payload(payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post(
        "/procurement/purchase-requests/{purchase_request_id}/submit",
        response_model=PurchaseRequestRecord,
        dependencies=dependencies,
    )
    async def submit_procurement_purchase_request(purchase_request_id: int) -> PurchaseRequestRecord:
        try:
            return submit_purchase_request.execute(purchase_request_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase request not found") from exc
        except InvalidPurchaseRequestTransitionError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post(
        "/procurement/purchase-requests/{purchase_request_id}/approve",
        response_model=PurchaseRequestRecord,
        dependencies=procurement_approval_dependencies,
    )
    async def approve_procurement_purchase_request(purchase_request_id: int) -> PurchaseRequestRecord:
        try:
            return approve_purchase_request.execute(purchase_request_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase request not found") from exc
        except InvalidPurchaseRequestTransitionError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post(
        "/procurement/purchase-requests/{purchase_request_id}/mark-ordered",
        response_model=PurchaseRequestRecord,
        dependencies=dependencies,
    )
    async def mark_procurement_purchase_request_ordered(purchase_request_id: int) -> PurchaseRequestRecord:
        try:
            return mark_purchase_request_ordered.execute(purchase_request_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase request not found") from exc
        except InvalidPurchaseRequestTransitionError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post(
        "/procurement/purchase-requests/{purchase_request_id}/receive",
        response_model=PurchaseRequestRecord,
        dependencies=dependencies,
    )
    async def receive_procurement_purchase_request(
        purchase_request_id: int,
        payload: PurchaseRequestActionPayload,
    ) -> PurchaseRequestRecord:
        try:
            return receive_purchase_request.execute(purchase_request_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase request not found") from exc
        except InvalidPurchaseRequestTransitionError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    @router.post(
        "/procurement/purchase-requests/{purchase_request_id}/cancel",
        response_model=PurchaseRequestRecord,
        dependencies=dependencies,
    )
    async def cancel_procurement_purchase_request(purchase_request_id: int) -> PurchaseRequestRecord:
        try:
            return cancel_purchase_request.execute(purchase_request_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase request not found") from exc
        except InvalidPurchaseRequestTransitionError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return router
