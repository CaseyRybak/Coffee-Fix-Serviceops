from __future__ import annotations

from fastapi import APIRouter, status

from serviceops_api.service_requests.models import (
    CreateServiceRequestPayload,
    CreateServiceRequestResponse,
)
from serviceops_api.service_requests.use_cases import CreateServiceRequest


def create_service_requests_router(use_case: CreateServiceRequest) -> APIRouter:
    router = APIRouter(prefix="/service-requests", tags=["service requests"])

    @router.post("", response_model=CreateServiceRequestResponse, status_code=status.HTTP_201_CREATED)
    async def create_service_request(payload: CreateServiceRequestPayload) -> CreateServiceRequestResponse:
        return use_case.execute(payload)

    return router
