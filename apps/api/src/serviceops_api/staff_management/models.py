from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


StaffRoleValue = Literal["admin", "dispatcher", "technician", "inventory"]


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Field is required")
    return cleaned


def _dedupe_roles(roles: list[StaffRoleValue]) -> list[StaffRoleValue]:
    seen: set[str] = set()
    result: list[StaffRoleValue] = []
    for role in roles:
        if role not in seen:
            result.append(role)
            seen.add(role)
    return sorted(result)


class CreateStaffAccountPayload(BaseModel):
    username: str = Field(min_length=1, max_length=180)
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    display_name: str | None = Field(default=None, max_length=180)
    password: str = Field(min_length=8, max_length=240)
    roles: list[StaffRoleValue] = Field(min_length=1)

    _clean_username = field_validator("username")(_clean_required)
    _clean_password = field_validator("password")(_clean_required)

    @field_validator("first_name", "last_name", "phone", "display_name")
    @classmethod
    def _clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("roles")
    @classmethod
    def _clean_roles(cls, roles: list[StaffRoleValue]) -> list[StaffRoleValue]:
        if not roles:
            raise ValueError("At least one role is required")
        return _dedupe_roles(roles)


class UpdateStaffProfilePayload(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=40)

    _clean_first_name = field_validator("first_name")(_clean_required)
    _clean_last_name = field_validator("last_name")(_clean_required)
    _clean_phone = field_validator("phone")(_clean_required)


class UpdateStaffRolesPayload(BaseModel):
    roles: list[StaffRoleValue] = Field(min_length=1)

    @field_validator("roles")
    @classmethod
    def _clean_roles(cls, roles: list[StaffRoleValue]) -> list[StaffRoleValue]:
        if not roles:
            raise ValueError("At least one role is required")
        return _dedupe_roles(roles)


class ResetStaffPasswordPayload(BaseModel):
    temporary_password: str | None = Field(default=None, min_length=8, max_length=240)

    @field_validator("temporary_password")
    @classmethod
    def _clean_temporary_password(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_required(value)


class StaffAccount(BaseModel):
    username: str
    display_name: str
    first_name: str
    last_name: str
    phone: str
    roles: list[StaffRoleValue]
    active: bool
    created_at: str
    updated_at: str


class StaffAccountListResponse(BaseModel):
    items: list[StaffAccount]


class TechnicianCandidate(BaseModel):
    username: str
    display_name: str
    phone: str


class TechnicianCandidateListResponse(BaseModel):
    items: list[TechnicianCandidate]


class StaffAccountActionResponse(BaseModel):
    account: StaffAccount


class StaffPasswordResetResponse(StaffAccountActionResponse):
    temporary_password: str


class StaffAuditEvent(BaseModel):
    actor_username: str
    target_username: str
    action: str
    metadata: dict[str, object]
    created_at: str


class StaffAuditListResponse(BaseModel):
    items: list[StaffAuditEvent]
