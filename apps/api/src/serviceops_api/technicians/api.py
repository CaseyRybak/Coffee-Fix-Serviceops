from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.staff_auth import StaffUser
from serviceops_api.technicians.models import (
    DiagnosisChecklistPayload,
    RecordPartsUsedPayload,
    RepairResultPayload,
    TechnicianActionResponse,
    TechnicianRequestDetail,
    TechnicianRequestListResponse,
)
from serviceops_api.technicians.use_cases import (
    GetTechnicianRequest,
    ListTechnicianRequests,
    RecordTechnicianDiagnosis,
    RecordTechnicianPartsUsed,
    RecordTechnicianResult,
)
from serviceops_api.inventory.repository import InsufficientStockError


def create_technician_router(
    list_requests: ListTechnicianRequests,
    get_request: GetTechnicianRequest,
    record_diagnosis: RecordTechnicianDiagnosis,
    record_result: RecordTechnicianResult,
    record_parts_used: RecordTechnicianPartsUsed,
    staff_dependency: Callable[..., object],
) -> APIRouter:
    router = APIRouter(prefix="/technician/service-requests", tags=["technician"])

    @router.get("", response_model=TechnicianRequestListResponse)
    async def list_technician_requests(staff: StaffUser = Depends(staff_dependency)) -> TechnicianRequestListResponse:
        return list_requests.execute(staff)

    @router.get("/{request_number}", response_model=TechnicianRequestDetail)
    async def get_technician_request(
        request_number: str,
        staff: StaffUser = Depends(staff_dependency),
    ) -> TechnicianRequestDetail:
        try:
            return get_request.execute(request_number, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.post("/{request_number}/diagnosis", response_model=TechnicianActionResponse)
    async def create_technician_diagnosis(
        request_number: str,
        payload: DiagnosisChecklistPayload,
        staff: StaffUser = Depends(staff_dependency),
    ) -> TechnicianActionResponse:
        try:
            return record_diagnosis.execute(request_number, payload, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.post("/{request_number}/result", response_model=TechnicianActionResponse)
    async def create_technician_result(
        request_number: str,
        payload: RepairResultPayload,
        staff: StaffUser = Depends(staff_dependency),
    ) -> TechnicianActionResponse:
        try:
            return record_result.execute(request_number, payload, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.post("/{request_number}/parts-used", response_model=TechnicianActionResponse)
    async def create_technician_parts_used(
        request_number: str,
        payload: RecordPartsUsedPayload,
        staff: StaffUser = Depends(staff_dependency),
    ) -> TechnicianActionResponse:
        try:
            return record_parts_used.execute(request_number, payload, staff)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request or part not found") from exc
        except InsufficientStockError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return router
