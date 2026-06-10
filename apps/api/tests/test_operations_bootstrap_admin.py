from serviceops_api.config import Settings
from serviceops_api.operations.bootstrap_admin import BootstrapAdminConfig, bootstrap_first_admin
from serviceops_api.staff_auth import verify_staff_password
from serviceops_api.staff_management.repository import SqliteStaffAccountRepository


def test_bootstrap_first_admin_creates_admin_and_audit_record() -> None:
    repository = SqliteStaffAccountRepository.in_memory()

    result = bootstrap_first_admin(
        BootstrapAdminConfig(
            username="owner@example.com",
            display_name="Owner",
            password="strong-admin-pass",
        ),
        Settings(environment="production", database_url="sqlite:///:memory:"),
        repository=repository,
    )

    account = repository.get_account_by_username("owner@example.com")
    assert result == {"status": "created", "username": "owner@example.com", "roles": ["admin"]}
    assert account is not None
    assert account["roles"] == ["admin"]
    assert verify_staff_password("strong-admin-pass", str(account["password_hash"]))
    assert repository.list_audit_events()[0]["action"] == "staff.bootstrap_admin_created"


def test_bootstrap_first_admin_refuses_when_active_admin_exists() -> None:
    repository = SqliteStaffAccountRepository.in_memory()
    bootstrap_first_admin(
        BootstrapAdminConfig(
            username="owner@example.com",
            display_name="Owner",
            password="strong-admin-pass",
        ),
        Settings(environment="production", database_url="sqlite:///:memory:"),
        repository=repository,
    )

    try:
        bootstrap_first_admin(
            BootstrapAdminConfig(
                username="second@example.com",
                display_name="Second",
                password="strong-admin-pass-2",
            ),
            Settings(environment="production", database_url="sqlite:///:memory:"),
            repository=repository,
        )
    except RuntimeError as exc:
        assert str(exc) == "Active admin already exists; use the admin workspace for staff management"
    else:
        raise AssertionError("expected bootstrap to refuse a second active admin")


def test_bootstrap_first_admin_validates_input_without_printing_password() -> None:
    repository = SqliteStaffAccountRepository.in_memory()

    try:
        bootstrap_first_admin(
            BootstrapAdminConfig(username=" ", display_name="Owner", password="short"),
            Settings(environment="production", database_url="sqlite:///:memory:"),
            repository=repository,
        )
    except ValueError as exc:
        message = str(exc)
        assert "password" in message
        assert "short" not in message
    else:
        raise AssertionError("expected invalid bootstrap input to fail")
