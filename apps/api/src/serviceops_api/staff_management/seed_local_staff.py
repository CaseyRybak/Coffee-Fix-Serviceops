from __future__ import annotations

from typing import NamedTuple

from serviceops_api.config import Settings, get_settings
from serviceops_api.staff_auth import hash_staff_password
from serviceops_api.staff_management.models import CreateStaffAccountPayload
from serviceops_api.staff_management.repository import StaffAccountStore, create_staff_account_repository


LOCAL_SEED_ENVIRONMENTS = {"local", "development", "dev", "test"}


class LocalStaffSeedAccount(NamedTuple):
    username: str
    first_name: str
    last_name: str
    phone: str
    password: str
    roles: list[str]


LOCAL_STAFF_SEED_ACCOUNTS: tuple[LocalStaffSeedAccount, ...] = (
    LocalStaffSeedAccount(
        username="dispatcher@coffeefix.local",
        first_name="Coffee Fix",
        last_name="Dispatcher",
        phone="+7 999 000-10-01",
        password="dispatcher-local",
        roles=["dispatcher"],
    ),
    LocalStaffSeedAccount(
        username="technician@coffeefix.local",
        first_name="Coffee Fix",
        last_name="Technician",
        phone="+7 999 000-10-02",
        password="technician-local",
        roles=["technician"],
    ),
    LocalStaffSeedAccount(
        username="inventory@coffeefix.local",
        first_name="Coffee Fix",
        last_name="Inventory",
        phone="+7 999 000-10-03",
        password="inventory-local",
        roles=["inventory"],
    ),
)


def seed_local_staff_accounts(repository: StaffAccountStore, settings: Settings) -> dict[str, list[str]]:
    if settings.environment.strip().lower() not in LOCAL_SEED_ENVIRONMENTS:
        raise ValueError("Local staff seed is only allowed in local development environments")

    created: list[str] = []
    skipped: list[str] = []
    for account in LOCAL_STAFF_SEED_ACCOUNTS:
        if repository.get_account_by_username(account.username) is not None:
            skipped.append(account.username)
            continue
        payload = CreateStaffAccountPayload(
            username=account.username,
            first_name=account.first_name,
            last_name=account.last_name,
            phone=account.phone,
            password=account.password,
            roles=account.roles,
        )
        repository.create_account(
            payload,
            password_hash=hash_staff_password(account.password),
            actor="local-staff-seed",
        )
        created.append(account.username)
    return {"created": created, "skipped": skipped}


def main() -> None:
    settings = get_settings()
    repository = create_staff_account_repository(settings)
    result = seed_local_staff_accounts(repository, settings)
    print(f"created: {', '.join(result['created']) if result['created'] else 'none'}")
    print(f"skipped: {', '.join(result['skipped']) if result['skipped'] else 'none'}")


if __name__ == "__main__":
    main()
