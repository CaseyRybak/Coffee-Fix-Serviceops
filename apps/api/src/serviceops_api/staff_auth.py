from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from serviceops_api.config import Settings


StaffRole = Literal["dispatcher", "admin", "technician", "inventory"]

security = HTTPBearer(auto_error=False)


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Field is required")
    return cleaned


class StaffLoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=180)
    password: str = Field(min_length=1, max_length=240)

    _clean_username = field_validator("username")(_clean_required)
    _clean_password = field_validator("password")(_clean_required)


class StaffUser(BaseModel):
    username: str
    roles: list[StaffRole]


class StaffLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    staff: StaffUser


class StaffAuthenticator:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.staff_auth_secret.encode("utf-8")
        self._token_ttl_seconds = settings.staff_token_ttl_seconds
        self._users = self._build_dev_users(settings)

    def authenticate(self, username: str, password: str) -> StaffUser:
        stored = self._users.get(username)
        if stored is None or not hmac.compare_digest(stored["password"], password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid staff credentials")
        return StaffUser(username=username, roles=list(stored["roles"]))

    def issue_token(self, staff: StaffUser) -> str:
        now = int(time.time())
        payload = {
            "sub": staff.username,
            "roles": staff.roles,
            "iat": now,
            "exp": now + self._token_ttl_seconds,
        }
        payload_segment = self._encode_json(payload)
        signature = self._sign(payload_segment)
        return f"{payload_segment}.{signature}"

    def verify_token(self, token: str) -> StaffUser:
        try:
            payload_segment, signature = token.split(".", 1)
        except ValueError as exc:
            raise self._invalid_token() from exc
        expected_signature = self._sign(payload_segment)
        if not hmac.compare_digest(signature, expected_signature):
            raise self._invalid_token()
        try:
            payload = json.loads(base64.urlsafe_b64decode(self._pad(payload_segment)).decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as exc:
            raise self._invalid_token() from exc
        if int(payload.get("exp", 0)) < int(time.time()):
            raise self._invalid_token()
        username = str(payload.get("sub", "")).strip()
        roles = [role for role in payload.get("roles", []) if role in {"dispatcher", "admin", "technician", "inventory"}]
        if not username or not roles:
            raise self._invalid_token()
        return StaffUser(username=username, roles=roles)

    def _build_dev_users(self, settings: Settings) -> dict[str, dict[str, object]]:
        users: dict[str, dict[str, object]] = {
            settings.staff_dev_username: {
                "password": settings.staff_dev_password,
                "roles": settings.staff_dev_roles_list,
            }
        }
        users.setdefault("admin@coffeefix.local", {"password": "admin-local", "roles": ["admin"]})
        users.setdefault("technician@coffeefix.local", {"password": "technician-local", "roles": ["technician"]})
        users.setdefault("inventory@coffeefix.local", {"password": "inventory-local", "roles": ["inventory"]})
        return users

    def _encode_json(self, payload: dict[str, object]) -> str:
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    def _sign(self, payload_segment: str) -> str:
        digest = hmac.new(self._secret, payload_segment.encode("ascii"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    def _pad(self, value: str) -> bytes:
        return f"{value}{'=' * (-len(value) % 4)}".encode("ascii")

    def _invalid_token(self) -> HTTPException:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid staff token")


def create_staff_auth_router(authenticator: StaffAuthenticator) -> APIRouter:
    router = APIRouter(prefix="/staff", tags=["staff auth"])

    @router.post("/login", response_model=StaffLoginResponse)
    async def login(payload: StaffLoginPayload) -> StaffLoginResponse:
        staff = authenticator.authenticate(payload.username, payload.password)
        return StaffLoginResponse(access_token=authenticator.issue_token(staff), token_type="bearer", staff=staff)

    return router


def get_current_staff(authenticator: StaffAuthenticator):
    async def dependency(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    ) -> StaffUser:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff authentication required")
        return authenticator.verify_token(credentials.credentials)

    return dependency


def require_staff_role(role: StaffRole, authenticator: StaffAuthenticator):
    async def dependency(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    ) -> StaffUser:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff authentication required")
        staff = authenticator.verify_token(credentials.credentials)
        if role not in staff.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role is not allowed")
        return staff

    return dependency
