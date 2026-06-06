from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.service_requests.models import (
    CustomerAnswerPayload,
    CustomerAnswerResponse,
    CreateServiceRequestPayload,
    CreateServiceRequestResponse,
    DispatcherActionResponse,
    DispatcherAssignmentPayload,
    DispatcherClarificationPayload,
    DispatcherInternalNotePayload,
    DispatcherRequestDetail,
    DispatcherRequestListResponse,
    DispatcherStatusUpdatePayload,
    PublicStatusResponse,
    TelegramOptInPayload,
    TelegramOptInResponse,
)
from serviceops_api.service_requests.use_cases import (
    AskDispatcherClarification,
    AssignDispatcherTechnician,
    CreateServiceRequest,
    CreateTelegramOptIn,
    GetDispatcherRequest,
    GetPublicStatus,
    ListDispatcherRequests,
    SaveDispatcherInternalNote,
    SubmitCustomerAnswer,
    UpdateDispatcherStatus,
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


def create_dispatcher_router(
    list_requests: ListDispatcherRequests,
    get_request: GetDispatcherRequest,
    update_status: UpdateDispatcherStatus,
    ask_clarification: AskDispatcherClarification,
    assign_technician: AssignDispatcherTechnician,
    save_internal_note: SaveDispatcherInternalNote,
    staff_dependency: Depends | None = None,
) -> APIRouter:
    dependencies = [Depends(staff_dependency)] if staff_dependency is not None else []
    router = APIRouter(prefix="/dispatcher/service-requests", tags=["dispatcher"], dependencies=dependencies)

    @router.get("", response_model=DispatcherRequestListResponse)
    async def list_dispatcher_requests() -> DispatcherRequestListResponse:
        return list_requests.execute()

    @router.get("/{request_number}", response_model=DispatcherRequestDetail)
    async def get_dispatcher_request(request_number: str) -> DispatcherRequestDetail:
        try:
            return get_request.execute(request_number)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.post("/{request_number}/status", response_model=DispatcherActionResponse)
    async def update_dispatcher_status(
        request_number: str,
        payload: DispatcherStatusUpdatePayload,
    ) -> DispatcherActionResponse:
        try:
            return update_status.execute(request_number, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.post("/{request_number}/clarifications", response_model=DispatcherActionResponse)
    async def create_dispatcher_clarification(
        request_number: str,
        payload: DispatcherClarificationPayload,
    ) -> DispatcherActionResponse:
        try:
            return ask_clarification.execute(request_number, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.post("/{request_number}/assignment", response_model=DispatcherActionResponse)
    async def assign_dispatcher_technician(
        request_number: str,
        payload: DispatcherAssignmentPayload,
    ) -> DispatcherActionResponse:
        try:
            return assign_technician.execute(request_number, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    @router.post("/{request_number}/internal-notes", response_model=DispatcherActionResponse)
    async def save_dispatcher_internal_note(
        request_number: str,
        payload: DispatcherInternalNotePayload,
    ) -> DispatcherActionResponse:
        try:
            return save_internal_note.execute(request_number, payload)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found") from exc

    return router
