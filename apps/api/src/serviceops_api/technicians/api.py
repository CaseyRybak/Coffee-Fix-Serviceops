from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.staff_auth import StaffUser
from serviceops_api.technicians.models import (
    DiagnosisChecklistPayload,
    RecordPartsUsedPayload,
    RepairResultPayload,
    TechnicianActionResponse,
    TechnicianProfileListResponse,
    TechnicianProfilePayload,
    TechnicianProfileSnapshot,
    TechnicianRecommendationResponse,
    TechnicianRequestDetail,
    TechnicianRequestListResponse,
)
from serviceops_api.technicians.use_cases import (
    GetTechnicianRequest,
    ListTechnicianRequests,
    ListTechnicianProfiles,
    RecordTechnicianDiagnosis,
    RecordTechnicianPartsUsed,
    RecordTechnicianResult,
    RecommendTechnicians,
    UpsertTechnicianProfile,
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


def create_technician_profile_router(
    list_profiles: ListTechnicianProfiles,
    upsert_profile: UpsertTechnicianProfile,
    recommend_technicians: RecommendTechnicians,
    admin_dependency: Callable[..., object],
    dispatcher_dependency: Callable[..., object],
) -> APIRouter:
    router = APIRouter(tags=["technician profiles"])

    @router.get("/admin/technician-profiles", response_model=TechnicianProfileListResponse)
    async def get_technician_profiles(_staff: StaffUser = Depends(admin_dependency)) -> TechnicianProfileListResponse:
        return list_profiles.execute()

    @router.post("/admin/technician-profiles/{username:path}", response_model=TechnicianProfileSnapshot)
    async def post_technician_profile(
        username: str,
        payload: TechnicianProfilePayload,
        staff: StaffUser = Depends(admin_dependency),
    ) -> TechnicianProfileSnapshot:
        try:
            return upsert_profile.execute(username, payload, actor=staff.username)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff account not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @router.get(
        "/dispatcher/service-requests/{request_number}/technician-recommendations",
        response_model=TechnicianRecommendationResponse,
    )
    async def get_technician_recommendations(
        request_number: str,
        starts_at: str | None = None,
        ends_at: str | None = None,
        _staff: StaffUser = Depends(dispatcher_dependency),
    ) -> TechnicianRecommendationResponse:
        try:
            return recommend_technicians.execute(request_number, starts_at=starts_at, ends_at=ends_at)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return router
