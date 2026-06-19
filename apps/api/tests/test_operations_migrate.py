import pytest

from serviceops_api.config import Settings


def test_run_migrations_rejects_sqlite_database() -> None:
    from serviceops_api.operations.migrate import run_migrations

    with pytest.raises(RuntimeError, match="Production migrations require PostgreSQL"):
        run_migrations(Settings(database_url="sqlite:///:memory:"))


def test_knowledge_base_pgvector_migration_uses_live_embedding_dimensions() -> None:
    migration_sql = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src"
        / "serviceops_api"
        / "migrations"
        / "0002_knowledge_base_rag.sql"
    ).read_text(encoding="utf-8")

    assert "embedding vector(1536)" in migration_sql
    assert "ALTER COLUMN embedding TYPE vector(1536)" in migration_sql
    assert "embedding vector(12)" not in migration_sql


def test_request_number_sequence_migration_is_transaction_safe() -> None:
    migration_sql = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src"
        / "serviceops_api"
        / "migrations"
        / "0011_request_number_sequence.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE SEQUENCE IF NOT EXISTS service_request_number_seq" in migration_sql
    assert "setval('service_request_number_seq'" in migration_sql
    assert "substring(request_number from" in migration_sql


def test_scheduling_migration_enforces_postgres_overlap_constraint() -> None:
    migration_sql = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src"
        / "serviceops_api"
        / "migrations"
        / "0007_scheduling_appointments.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS btree_gist" in migration_sql
    assert "EXCLUDE USING gist" in migration_sql
    assert "technician_identifier WITH =" in migration_sql
    assert "tstzrange(starts_at, ends_at, '[)') WITH &&" in migration_sql
    assert "WHERE (status = 'scheduled')" in migration_sql


def test_technician_profile_migration_contract() -> None:
    migration_sql = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src"
        / "serviceops_api"
        / "migrations"
        / "0014_technician_profiles.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS technician_profiles" in migration_sql
    assert "staff_username TEXT PRIMARY KEY REFERENCES staff_accounts(username) ON DELETE CASCADE" in migration_sql
    assert "skill_brands JSONB NOT NULL DEFAULT '[]'::jsonb" in migration_sql
    assert "service_regions JSONB NOT NULL DEFAULT '[]'::jsonb" in migration_sql
    assert "CREATE INDEX IF NOT EXISTS idx_technician_profiles_active" in migration_sql


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
    monkeypatch.setattr(migrate, "create_ai_assistant_history_repository", record_factory("ai_assistant"))
    monkeypatch.setattr(migrate, "create_inventory_repository", record_factory("inventory"))
    monkeypatch.setattr(migrate, "create_staff_account_repository", record_factory("staff_management"))
    monkeypatch.setattr(migrate, "create_technician_profile_repository", record_factory("technician_profiles"))
    monkeypatch.setattr(migrate, "create_notification_repository", record_factory("notifications"))

    result = migrate.run_migrations(
        Settings(database_url="postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops")
    )

    assert result == {"status": "ok", "database": "postgres"}
    assert calls == [
        ("service_requests", True),
        ("knowledge_base", True),
        ("ai_agents", True),
        ("ai_assistant", True),
        ("inventory", True),
        ("staff_management", True),
        ("technician_profiles", True),
        ("notifications", True),
    ]
