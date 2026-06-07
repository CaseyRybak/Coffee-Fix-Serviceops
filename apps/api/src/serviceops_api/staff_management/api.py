from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from serviceops_api.staff_auth import StaffUser
from serviceops_api.staff_management.models import (
    CreateStaffAccountPayload,
    ResetStaffPasswordPayload,
    StaffAccount,
    StaffAccountActionResponse,
    StaffAccountListResponse,
    StaffAuditListResponse,
    StaffPasswordResetResponse,
    UpdateStaffRolesPayload,
)
from serviceops_api.staff_management.use_cases import (
    ActivateStaffAccount,
    CreateStaffAccount,
    DeactivateStaffAccount,
    ListStaffAccounts,
    ListStaffAuditEvents,
    ResetStaffPassword,
    UpdateStaffRoles,
)


def create_staff_management_router(
    create_account: CreateStaffAccount,
    list_accounts: ListStaffAccounts,
    update_roles: UpdateStaffRoles,
    activate_account: ActivateStaffAccount,
    deactivate_account: DeactivateStaffAccount,
    reset_password: ResetStaffPassword,
    list_audit_events: ListStaffAuditEvents,
    staff_dependency: Depends,
) -> APIRouter:
    router = APIRouter(prefix="/admin/staff", tags=["staff management"])

    @router.get("", response_model=StaffAccountListResponse)
    async def get_staff(current_staff: StaffUser = Depends(staff_dependency)) -> StaffAccountListResponse:
        return list_accounts.execute()

    @router.post("", response_model=StaffAccount, status_code=status.HTTP_201_CREATED)
    async def post_staff(
        payload: CreateStaffAccountPayload,
        current_staff: StaffUser = Depends(staff_dependency),
    ) -> StaffAccount:
        try:
            return create_account.execute(payload, actor=current_staff.username)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @router.post("/{username}/roles", response_model=StaffAccountActionResponse)
    async def post_staff_roles(
        username: str,
        payload: UpdateStaffRolesPayload,
        current_staff: StaffUser = Depends(staff_dependency),
    ) -> StaffAccountActionResponse:
        try:
            return update_roles.execute(username, payload, actor=current_staff.username)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff account not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @router.post("/{username}/activate", response_model=StaffAccountActionResponse)
    async def post_staff_activate(
        username: str,
        current_staff: StaffUser = Depends(staff_dependency),
    ) -> StaffAccountActionResponse:
        try:
            return activate_account.execute(username, actor=current_staff.username)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff account not found") from exc

    @router.post("/{username}/deactivate", response_model=StaffAccountActionResponse)
    async def post_staff_deactivate(
        username: str,
        current_staff: StaffUser = Depends(staff_dependency),
    ) -> StaffAccountActionResponse:
        try:
            return deactivate_account.execute(username, actor=current_staff.username)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff account not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @router.post("/{username}/reset-password", response_model=StaffPasswordResetResponse)
    async def post_staff_reset_password(
        username: str,
        payload: ResetStaffPasswordPayload | None = None,
        current_staff: StaffUser = Depends(staff_dependency),
    ) -> StaffPasswordResetResponse:
        try:
            return reset_password.execute(username, payload or ResetStaffPasswordPayload(), actor=current_staff.username)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff account not found") from exc

    @router.get("/audit", response_model=StaffAuditListResponse)
    async def get_staff_audit(current_staff: StaffUser = Depends(staff_dependency)) -> StaffAuditListResponse:
        return list_audit_events.execute()

    return router
