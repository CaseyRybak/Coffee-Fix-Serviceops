from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.inventory.models import (
    CreatePartPayload,
    InventoryPartListResponse,
    PartRecord,
    StockCountPayload,
    StockSnapshot,
)
from serviceops_api.inventory.use_cases import CreatePart, ListParts, SetStockCount


def create_inventory_router(
    create_part: CreatePart,
    list_parts: ListParts,
    set_stock_count: SetStockCount,
    staff_dependency: Depends | None = None,
) -> APIRouter:
    dependencies = [Depends(staff_dependency)] if staff_dependency is not None else []
    router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=dependencies)

    @router.get("/parts", response_model=InventoryPartListResponse)
    async def get_parts() -> InventoryPartListResponse:
        return list_parts.execute()

    @router.post("/parts", response_model=PartRecord, status_code=status.HTTP_201_CREATED)
    async def create_inventory_part(payload: CreatePartPayload) -> PartRecord:
        return create_part.execute(payload)

    @router.post("/parts/{part_id}/stock", response_model=StockSnapshot)
    async def update_stock_count(part_id: int, payload: StockCountPayload) -> StockSnapshot:
        try:
            return set_stock_count.execute(part_id, payload.quantity_on_hand)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Part not found") from exc

    return router
