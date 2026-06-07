import pytest

from serviceops_api.config import Settings


def test_run_migrations_rejects_sqlite_database() -> None:
    from serviceops_api.operations.migrate import run_migrations

    with pytest.raises(RuntimeError, match="Production migrations require PostgreSQL"):
        run_migrations(Settings(database_url="sqlite:///:memory:"))


def test_run_migrations_initializes_all_postgres_repositories(monkeypatch) -> None:
    from serviceops_api.operations import migrate

    calls: list[tuple[str, bool]] = []

    def record_factory(name: str):
        def factory(settings: Settings, initialize: bool = True) -> object:
            calls.append((name, initialize))
            assert settings.database_url.startswith("postgresql+psycopg://")
            return object()

        return factory

    monkeypatch.setattr(migrate, "create_service_request_repository", record_factory("service_requests"))
    monkeypatch.setattr(migrate, "create_knowledge_base_repository", record_factory("knowledge_base"))
    monkeypatch.setattr(migrate, "create_ai_suggestion_repository", record_factory("ai_agents"))
    monkeypatch.setattr(migrate, "create_inventory_repository", record_factory("inventory"))
    monkeypatch.setattr(migrate, "create_staff_account_repository", record_factory("staff_management"))

    result = migrate.run_migrations(
        Settings(database_url="postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops")
    )

    assert result == {"status": "ok", "database": "postgres"}
    assert calls == [
        ("service_requests", True),
        ("knowledge_base", True),
        ("ai_agents", True),
        ("inventory", True),
        ("staff_management", True),
    ]
