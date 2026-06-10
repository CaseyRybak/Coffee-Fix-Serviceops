from __future__ import annotations

from dataclasses import dataclass
import json
import os

from serviceops_api.config import Settings, get_settings
from serviceops_api.staff_auth import hash_staff_password
from serviceops_api.staff_management.models import CreateStaffAccountPayload
from serviceops_api.staff_management.repository import StaffAccountStore, create_staff_account_repository


BOOTSTRAP_ACTOR = "system:bootstrap-admin"


@dataclass(frozen=True)
class BootstrapAdminConfig:
    username: str
    display_name: str
    password: str


def bootstrap_first_admin(
    config: BootstrapAdminConfig,
    settings: Settings | None = None,
    repository: StaffAccountStore | None = None,
) -> dict[str, object]:
    resolved_settings = settings or get_settings()
    store = repository or create_staff_account_repository(resolved_settings, initialize=True)
    payload = _payload(config)
    if store.count_active_admins() > 0:
        raise RuntimeError("Active admin already exists; use the admin workspace for staff management")

    account = store.create_account(payload, hash_staff_password(payload.password), actor=BOOTSTRAP_ACTOR)
    store.record_audit_event(
        BOOTSTRAP_ACTOR,
        payload.username,
        "staff.bootstrap_admin_created",
        {"environment": resolved_settings.environment, "roles": ["admin"]},
    )
    return {
        "status": "created",
        "username": account["username"],
        "roles": account["roles"],
    }


def config_from_env(environ: dict[str, str] | None = None) -> BootstrapAdminConfig:
    source = environ or os.environ
    return BootstrapAdminConfig(
        username=source.get("SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME", ""),
        display_name=source.get("SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME", ""),
        password=source.get("SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD", ""),
    )


def _payload(config: BootstrapAdminConfig) -> CreateStaffAccountPayload:
    username = config.username.strip()
    display_name = config.display_name.strip()
    password = config.password.strip()
    errors: list[str] = []
    if not username:
        errors.append("username is required")
    if not display_name:
        errors.append("display_name is required")
    if len(password) < 8:
        errors.append("password must be at least 8 characters")
    if errors:
        raise ValueError("; ".join(errors))
    return CreateStaffAccountPayload(
        username=username,
        display_name=display_name,
        password=password,
        roles=["admin"],
    )


def main() -> None:
    try:
        result = bootstrap_first_admin(config_from_env())
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, sort_keys=True))
        raise SystemExit(1) from exc
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
