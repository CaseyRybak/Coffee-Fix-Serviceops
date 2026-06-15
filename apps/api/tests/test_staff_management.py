import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository
from serviceops_api.staff_auth import StaffAuthenticator, hash_staff_password
from serviceops_api.staff_management.models import CreateStaffAccountPayload
from serviceops_api.staff_management.repository import SqliteStaffAccountRepository
from serviceops_api.staff_management.seed_local_staff import seed_local_staff_accounts
from serviceops_api.staff_management.use_cases import CreateStaffAccount, ListStaffAccounts
from serviceops_api.config import Settings


async def post_json(
    service_repository: ServiceRequestRepository,
    staff_repository: SqliteStaffAccountRepository,
    path: str,
    body: dict[str, object],
    token: str | None = None,
) -> httpx.Response:
    app = create_app(service_request_repository=service_repository, staff_account_repository=staff_repository)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(
    service_repository: ServiceRequestRepository,
    staff_repository: SqliteStaffAccountRepository,
    path: str,
    token: str | None = None,
) -> httpx.Response:
    app = create_app(service_request_repository=service_repository, staff_account_repository=staff_repository)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def login(
    service_repository: ServiceRequestRepository,
    staff_repository: SqliteStaffAccountRepository,
    username: str,
    password: str,
) -> httpx.Response:
    return await post_json(service_repository, staff_repository, "/staff/login", {"username": username, "password": password})


def create_admin(repository: SqliteStaffAccountRepository) -> None:
    repository.create_account(
        CreateStaffAccountPayload(
            username="admin@coffeefix.local",
            display_name="Admin",
            password="admin-local",
            roles=["admin"],
        ),
        password_hash=hash_staff_password("admin-local"),
        actor="system",
    )


def test_staff_repository_creates_account_with_roles_and_audit() -> None:
    repository = SqliteStaffAccountRepository.in_memory()

    created = CreateStaffAccount(repository).execute(
        CreateStaffAccountPayload(
            username="tech-1@coffeefix.local",
            display_name="Tech One",
            password="temporary-pass-1",
            roles=["technician"],
        ),
        actor="admin@coffeefix.local",
    )

    assert created.username == "tech-1@coffeefix.local"
    assert created.display_name == "Tech One"
    assert created.roles == ["technician"]
    assert created.active is True
    assert ListStaffAccounts(repository).execute().items[0].username == "tech-1@coffeefix.local"
    assert repository.list_audit_events()[0]["action"] == "staff.created"


def test_staff_repository_updates_roles_active_flag_password_hash_and_audit() -> None:
    repository = SqliteStaffAccountRepository.in_memory()
    created = CreateStaffAccount(repository).execute(
        CreateStaffAccountPayload(
            username="multi@coffeefix.local",
            display_name="Multi Role",
            password="temporary-pass-1",
            roles=["dispatcher"],
        ),
        actor="admin@coffeefix.local",
    )

    updated = repository.update_roles(created.username, ["dispatcher", "inventory"], actor="admin@coffeefix.local")
    deactivated = repository.set_active(created.username, False, actor="admin@coffeefix.local")
    old_hash = str(repository.get_account_by_username(created.username)["password_hash"])
    repository.reset_password(created.username, hash_staff_password("new-temporary-pass"), actor="admin@coffeefix.local")
    new_hash = str(repository.get_account_by_username(created.username)["password_hash"])

    assert updated["roles"] == ["dispatcher", "inventory"]
    assert deactivated["active"] is False
    assert old_hash != new_hash
    assert [event["action"] for event in repository.list_audit_events()] == [
        "staff.password_reset",
        "staff.deactivated",
        "staff.roles_updated",
        "staff.created",
    ]


def test_staff_repository_prevents_deactivating_last_active_admin() -> None:
    repository = SqliteStaffAccountRepository.in_memory()
    create_admin(repository)

    try:
        repository.set_active("admin@coffeefix.local", False, actor="admin@coffeefix.local")
    except ValueError as exc:
        assert str(exc) == "Cannot deactivate the last active admin"
    else:
        raise AssertionError("expected last active admin deactivation to fail")


def test_staff_repository_prevents_removing_last_active_admin_role() -> None:
    repository = SqliteStaffAccountRepository.in_memory()
    create_admin(repository)

    try:
        repository.update_roles("admin@coffeefix.local", ["dispatcher"], actor="admin@coffeefix.local")
    except ValueError as exc:
        assert str(exc) == "Cannot remove the last active admin"
    else:
        raise AssertionError("expected last active admin role removal to fail")


def test_production_authenticator_does_not_allow_development_seed_users() -> None:
    repository = SqliteStaffAccountRepository.in_memory()
    authenticator = StaffAuthenticator(Settings(environment="production"), repository)

    try:
        authenticator.authenticate("admin@coffeefix.local", "admin-local")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 401
    else:
        raise AssertionError("expected production seed login to fail")


def test_local_staff_seed_creates_development_users_once_as_persisted_accounts() -> None:
    repository = SqliteStaffAccountRepository.in_memory()

    first_result = seed_local_staff_accounts(repository, Settings(environment="local"))
    second_result = seed_local_staff_accounts(repository, Settings(environment="local"))

    accounts = {account["username"]: account for account in repository.list_accounts()}
    assert first_result == {
        "created": [
            "dispatcher@coffeefix.local",
            "technician@coffeefix.local",
            "inventory@coffeefix.local",
        ],
        "skipped": [],
    }
    assert second_result == {
        "created": [],
        "skipped": [
            "dispatcher@coffeefix.local",
            "technician@coffeefix.local",
            "inventory@coffeefix.local",
        ],
    }
    assert accounts["dispatcher@coffeefix.local"]["roles"] == ["dispatcher"]
    assert accounts["technician@coffeefix.local"]["roles"] == ["technician"]
    assert accounts["inventory@coffeefix.local"]["roles"] == ["inventory"]
    assert len(repository.list_audit_events()) == 3


def test_local_staff_seed_is_blocked_outside_local_development_environments() -> None:
    repository = SqliteStaffAccountRepository.in_memory()

    try:
        seed_local_staff_accounts(repository, Settings(environment="production"))
    except ValueError as exc:
        assert str(exc) == "Local staff seed is only allowed in local development environments"
    else:
        raise AssertionError("expected production seed to fail")


def test_persisted_staff_login_and_deactivated_account_rejection() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    staff_repository = SqliteStaffAccountRepository.in_memory()
    CreateStaffAccount(staff_repository).execute(
        CreateStaffAccountPayload(
            username="technician-persisted@coffeefix.local",
            display_name="Persisted Tech",
            password="temporary-pass-1",
            roles=["technician"],
        ),
        actor="admin@coffeefix.local",
    )

    login_response = asyncio.run(
        login(service_repository, staff_repository, "technician-persisted@coffeefix.local", "temporary-pass-1")
    )
    token = str(login_response.json()["access_token"])
    technician_response = asyncio.run(
        get_json(service_repository, staff_repository, "/technician/service-requests", token=token)
    )
    staff_repository.set_active("technician-persisted@coffeefix.local", False, actor="admin@coffeefix.local")
    deactivated_response = asyncio.run(
        login(service_repository, staff_repository, "technician-persisted@coffeefix.local", "temporary-pass-1")
    )

    assert login_response.status_code == 200
    assert login_response.json()["staff"] == {
        "username": "technician-persisted@coffeefix.local",
        "roles": ["technician"],
    }
    assert technician_response.status_code == 200
    assert deactivated_response.status_code == 401


def test_persisted_staff_auth_records_safe_audit_events() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    staff_repository = SqliteStaffAccountRepository.in_memory()
    CreateStaffAccount(staff_repository).execute(
        CreateStaffAccountPayload(
            username="audited-tech@coffeefix.local",
            display_name="Audited Tech",
            password="temporary-pass-1",
            roles=["technician"],
        ),
        actor="admin@coffeefix.local",
    )

    success_response = asyncio.run(
        login(service_repository, staff_repository, "audited-tech@coffeefix.local", "temporary-pass-1")
    )
    failed_response = asyncio.run(
        login(service_repository, staff_repository, "audited-tech@coffeefix.local", "wrong-password")
    )
    staff_repository.set_active("audited-tech@coffeefix.local", False, actor="admin@coffeefix.local")
    inactive_response = asyncio.run(
        login(service_repository, staff_repository, "audited-tech@coffeefix.local", "temporary-pass-1")
    )
    token_response = asyncio.run(
        get_json(
            service_repository,
            staff_repository,
            "/technician/service-requests",
            token=str(success_response.json()["access_token"]),
        )
    )

    assert success_response.status_code == 200
    assert failed_response.status_code == 401
    assert inactive_response.status_code == 401
    assert token_response.status_code == 401
    audit_events = staff_repository.list_audit_events()
    actions = [event["action"] for event in audit_events]
    assert "staff.login_succeeded" in actions
    assert "staff.login_failed" in actions
    assert "staff.token_rejected" in actions
    inactive_event = next(event for event in audit_events if event["action"] == "staff.login_failed" and event["metadata"]["reason"] == "inactive")
    token_event = next(event for event in audit_events if event["action"] == "staff.token_rejected")
    success_event = next(event for event in audit_events if event["action"] == "staff.login_succeeded")
    assert success_event["actor_username"] == "audited-tech@coffeefix.local"
    assert success_event["target_username"] == "audited-tech@coffeefix.local"
    assert success_event["metadata"]["outcome"] == "succeeded"
    assert inactive_event["metadata"]["outcome"] == "failed"
    assert token_event["metadata"] == {"outcome": "failed", "reason": "inactive", "source": "staff_auth"}
    audit_text = str(audit_events)
    assert "temporary-pass-1" not in audit_text
    assert "wrong-password" not in audit_text
    assert str(success_response.json()["access_token"]) not in audit_text
    assert "password_hash" not in audit_text


def test_deactivated_persisted_staff_token_no_longer_authorizes_protected_routes() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    staff_repository = SqliteStaffAccountRepository.in_memory()
    CreateStaffAccount(staff_repository).execute(
        CreateStaffAccountPayload(
            username="technician-persisted@coffeefix.local",
            display_name="Persisted Tech",
            password="temporary-pass-1",
            roles=["technician"],
        ),
        actor="admin@coffeefix.local",
    )
    login_response = asyncio.run(
        login(service_repository, staff_repository, "technician-persisted@coffeefix.local", "temporary-pass-1")
    )
    token = str(login_response.json()["access_token"])

    staff_repository.set_active("technician-persisted@coffeefix.local", False, actor="admin@coffeefix.local")
    response = asyncio.run(get_json(service_repository, staff_repository, "/technician/service-requests", token=token))

    assert response.status_code == 401


def test_removed_role_no_longer_authorizes_existing_staff_token() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    staff_repository = SqliteStaffAccountRepository.in_memory()
    CreateStaffAccount(staff_repository).execute(
        CreateStaffAccountPayload(
            username="dispatcher-persisted@coffeefix.local",
            display_name="Persisted Dispatcher",
            password="temporary-pass-1",
            roles=["dispatcher"],
        ),
        actor="admin@coffeefix.local",
    )
    login_response = asyncio.run(
        login(service_repository, staff_repository, "dispatcher-persisted@coffeefix.local", "temporary-pass-1")
    )
    token = str(login_response.json()["access_token"])

    staff_repository.update_roles("dispatcher-persisted@coffeefix.local", ["inventory"], actor="admin@coffeefix.local")
    response = asyncio.run(get_json(service_repository, staff_repository, "/dispatcher/service-requests", token=token))

    assert response.status_code == 403


def test_admin_staff_management_api_returns_controlled_error_for_duplicate_username() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    staff_repository = SqliteStaffAccountRepository.in_memory()
    create_admin(staff_repository)
    admin_login = asyncio.run(login(service_repository, staff_repository, "admin@coffeefix.local", "admin-local"))
    admin_token = str(admin_login.json()["access_token"])
    payload = {
        "username": "duplicate@coffeefix.local",
        "display_name": "Duplicate",
        "password": "temporary-pass-1",
        "roles": ["dispatcher"],
    }

    first_response = asyncio.run(
        post_json(service_repository, staff_repository, "/admin/staff", payload, token=admin_token)
    )
    second_response = asyncio.run(
        post_json(service_repository, staff_repository, "/admin/staff", payload, token=admin_token)
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 400


def test_admin_staff_management_api_lifecycle_and_role_protection() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    staff_repository = SqliteStaffAccountRepository.in_memory()
    create_admin(staff_repository)
    staff_repository.create_account(
        CreateStaffAccountPayload(
            username="dispatcher@coffeefix.local",
            display_name="Dispatcher",
            password="dispatcher-local",
            roles=["dispatcher"],
        ),
        password_hash=hash_staff_password("dispatcher-local"),
        actor="system",
    )
    admin_login = asyncio.run(login(service_repository, staff_repository, "admin@coffeefix.local", "admin-local"))
    admin_token = str(admin_login.json()["access_token"])
    dispatcher_login = asyncio.run(
        login(service_repository, staff_repository, "dispatcher@coffeefix.local", "dispatcher-local")
    )
    dispatcher_token = str(dispatcher_login.json()["access_token"])

    create_response = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            "/admin/staff",
            {
                "username": "inventory-admin@coffeefix.local",
                "display_name": "Inventory Admin",
                "password": "temporary-pass-1",
                "roles": ["inventory"],
            },
            token=admin_token,
        )
    )
    list_response = asyncio.run(get_json(service_repository, staff_repository, "/admin/staff", token=admin_token))
    roles_response = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            "/admin/staff/inventory-admin%40coffeefix.local/roles",
            {"roles": ["inventory", "dispatcher"]},
            token=admin_token,
        )
    )
    deactivate_response = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            "/admin/staff/inventory-admin%40coffeefix.local/deactivate",
            {},
            token=admin_token,
        )
    )
    reset_response = asyncio.run(
        post_json(
            service_repository,
            staff_repository,
            "/admin/staff/inventory-admin%40coffeefix.local/reset-password",
            {},
            token=admin_token,
        )
    )
    audit_response = asyncio.run(get_json(service_repository, staff_repository, "/admin/staff/audit", token=admin_token))
    non_admin_response = asyncio.run(get_json(service_repository, staff_repository, "/admin/staff", token=dispatcher_token))

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert "inventory-admin@coffeefix.local" in [item["username"] for item in list_response.json()["items"]]
    assert roles_response.json()["account"]["roles"] == ["dispatcher", "inventory"]
    assert deactivate_response.json()["account"]["active"] is False
    assert reset_response.json()["temporary_password"]
    assert audit_response.json()["items"][0]["action"] == "staff.password_reset"
    assert non_admin_response.status_code == 403


def test_forbidden_staff_role_records_safe_audit_event() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    staff_repository = SqliteStaffAccountRepository.in_memory()
    create_admin(staff_repository)
    staff_repository.create_account(
        CreateStaffAccountPayload(
            username="dispatcher@coffeefix.local",
            display_name="Dispatcher",
            password="dispatcher-local",
            roles=["dispatcher"],
        ),
        password_hash=hash_staff_password("dispatcher-local"),
        actor="system",
    )
    dispatcher_login = asyncio.run(
        login(service_repository, staff_repository, "dispatcher@coffeefix.local", "dispatcher-local")
    )
    dispatcher_token = str(dispatcher_login.json()["access_token"])

    response = asyncio.run(get_json(service_repository, staff_repository, "/admin/staff", token=dispatcher_token))

    assert response.status_code == 403
    audit_event = staff_repository.list_audit_events()[0]
    assert audit_event["actor_username"] == "dispatcher@coffeefix.local"
    assert audit_event["target_username"] == "admin"
    assert audit_event["action"] == "staff.role_forbidden"
    assert audit_event["metadata"] == {
        "outcome": "blocked",
        "reason": "missing_role",
        "role": "admin",
        "source": "staff_auth",
    }
    assert dispatcher_token not in str(audit_event)
