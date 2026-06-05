from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from serviceops_api.service_requests.models import (
    CustomerAnswerPayload,
    CustomerAnswerResponse,
    CreateServiceRequestPayload,
    CreateServiceRequestResponse,
    PublicStatusResponse,
    TelegramOptInPayload,
    TelegramOptInResponse,
)
from serviceops_api.service_requests.use_cases import (
    CreateServiceRequest,
    CreateTelegramOptIn,
    GetPublicStatus,
    SubmitCustomerAnswer,
)


def create_service_requests_router(
    create_request: CreateServiceRequest,
    get_status: GetPublicStatus,
    submit_answer: SubmitCustomerAnswer,
    create_telegram_opt_in: CreateTelegramOptIn,
) -> APIRouter:
    router = APIRouter(prefix="/service-requests", tags=["service requests"])

    @router.post("", response_model=CreateServiceRequestResponse, status_code=status.HTTP_201_CREATED)
    async def create_service_request(payload: CreateServiceRequestPayload) -> CreateServiceRequestResponse:
        return create_request.execute(payload)

    @router.get("/{request_number}/status", response_model=PublicStatusResponse)
    async def get_service_request_status(request_number: str) -> PublicStatusResponse:
        try:
            return get_status.by_request_number(request_number)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.post("/{request_number}/answers", response_model=CustomerAnswerResponse)
    async def submit_customer_answer(request_number: str, payload: CustomerAnswerPayload) -> CustomerAnswerResponse:
        try:
            return submit_answer.execute(request_number, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clarification question not found") from exc

    @router.post("/{request_number}/telegram-opt-in", response_model=TelegramOptInResponse)
    async def telegram_opt_in(request_number: str, payload: TelegramOptInPayload) -> TelegramOptInResponse:
        try:
            return create_telegram_opt_in.execute(request_number, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    return router


def create_public_status_router(get_status: GetPublicStatus) -> APIRouter:
    router = APIRouter(tags=["public status"])

    @router.get("/status/{public_token}", response_model=PublicStatusResponse)
    async def get_public_status(public_token: str) -> PublicStatusResponse:
        try:
            return get_status.by_token(public_token)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    return router
