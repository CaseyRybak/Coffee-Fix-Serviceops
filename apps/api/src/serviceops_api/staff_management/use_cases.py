from __future__ import annotations

import secrets
import string

from serviceops_api.staff_auth import hash_staff_password
from serviceops_api.staff_management.models import (
    CreateStaffAccountPayload,
    ResetStaffPasswordPayload,
    StaffAccount,
    StaffAccountActionResponse,
    StaffAccountListResponse,
    StaffAuditEvent,
    StaffAuditListResponse,
    StaffPasswordResetResponse,
    TechnicianCandidate,
    TechnicianCandidateListResponse,
    UpdateStaffProfilePayload,
    UpdateStaffRolesPayload,
)
from serviceops_api.staff_management.repository import StaffAccountStore


class CreateStaffAccount:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self, payload: CreateStaffAccountPayload, actor: str) -> StaffAccount:
        row = self._repository.create_account(payload, hash_staff_password(payload.password), actor)
        return _account(row)


class ListStaffAccounts:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self) -> StaffAccountListResponse:
        return StaffAccountListResponse(items=[_account(row) for row in self._repository.list_accounts()])


class ListTechnicianCandidates:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self) -> TechnicianCandidateListResponse:
        candidates = [
            TechnicianCandidate(
                username=str(row["username"]),
                display_name=str(row["display_name"]),
                phone=str(row.get("phone", "")),
            )
            for row in self._repository.list_accounts()
            if bool(row["active"]) and "technician" in row["roles"]
        ]
        return TechnicianCandidateListResponse(items=candidates)


class UpdateStaffProfile:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self, username: str, payload: UpdateStaffProfilePayload, actor: str) -> StaffAccountActionResponse:
        row = self._repository.update_profile(
            username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            actor=actor,
        )
        return StaffAccountActionResponse(account=_account(row))


class UpdateStaffRoles:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self, username: str, payload: UpdateStaffRolesPayload, actor: str) -> StaffAccountActionResponse:
        return StaffAccountActionResponse(account=_account(self._repository.update_roles(username, payload.roles, actor)))


class DeactivateStaffAccount:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self, username: str, actor: str) -> StaffAccountActionResponse:
        return StaffAccountActionResponse(account=_account(self._repository.set_active(username, False, actor)))


class ActivateStaffAccount:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self, username: str, actor: str) -> StaffAccountActionResponse:
        return StaffAccountActionResponse(account=_account(self._repository.set_active(username, True, actor)))


class ResetStaffPassword:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self, username: str, payload: ResetStaffPasswordPayload, actor: str) -> StaffPasswordResetResponse:
        temporary_password = payload.temporary_password or _temporary_password()
        row = self._repository.reset_password(username, hash_staff_password(temporary_password), actor)
        return StaffPasswordResetResponse(account=_account(row), temporary_password=temporary_password)


class ListStaffAuditEvents:
    def __init__(self, repository: StaffAccountStore) -> None:
        self._repository = repository

    def execute(self) -> StaffAuditListResponse:
        return StaffAuditListResponse(items=[StaffAuditEvent(**row) for row in self._repository.list_audit_events()])


def _account(row: dict[str, object]) -> StaffAccount:
    return StaffAccount(
        username=str(row["username"]),
        display_name=str(row["display_name"]),
        first_name=str(row.get("first_name", "")),
        last_name=str(row.get("last_name", "")),
        phone=str(row.get("phone", "")),
        roles=list(row["roles"]),
        active=bool(row["active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _temporary_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "tmp-" + "".join(secrets.choice(alphabet) for _ in range(18))
