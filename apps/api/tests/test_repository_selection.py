from serviceops_api.config import Settings
from serviceops_api.ai_agents.repository import (
    PostgresAiSuggestionRepository,
    SqliteAiSuggestionRepository,
    create_ai_suggestion_repository,
)
from serviceops_api.knowledge_base.repository import (
    PostgresKnowledgeBaseRepository,
    SqliteKnowledgeBaseRepository,
    create_knowledge_base_repository,
)
from psycopg.rows import dict_row

from serviceops_api.service_requests.repository import (
    PostgresServiceRequestRepository,
    ServiceRequestRepository,
    create_service_request_repository,
)


def test_repository_factory_uses_postgres_for_postgresql_url() -> None:
    settings = Settings(database_url="postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops")

    repository = create_service_request_repository(settings, initialize=False)

    assert isinstance(repository, PostgresServiceRequestRepository)


def test_repository_factory_uses_sqlite_for_sqlite_url() -> None:
    settings = Settings(database_url="sqlite:///:memory:")

    repository = create_service_request_repository(settings)

    assert isinstance(repository, ServiceRequestRepository)


def test_repository_factory_rejects_unknown_database_url() -> None:
    settings = Settings(database_url="mysql://serviceops:serviceops@localhost/serviceops")

    try:
        create_service_request_repository(settings, initialize=False)
    except ValueError as exc:
        assert "Unsupported SERVICEOPS_DATABASE_URL" in str(exc)
    else:
        raise AssertionError("expected unsupported database URL to fail")


def test_knowledge_base_repository_factory_uses_postgres_for_postgresql_url() -> None:
    settings = Settings(database_url="postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops")

    repository = create_knowledge_base_repository(settings, initialize=False)

    assert isinstance(repository, PostgresKnowledgeBaseRepository)


def test_knowledge_base_repository_factory_uses_sqlite_for_sqlite_url() -> None:
    settings = Settings(database_url="sqlite:///:memory:")

    repository = create_knowledge_base_repository(settings)

    assert isinstance(repository, SqliteKnowledgeBaseRepository)


def test_knowledge_base_repository_factory_rejects_unknown_database_url() -> None:
    settings = Settings(database_url="mysql://serviceops:serviceops@localhost/serviceops")

    try:
        create_knowledge_base_repository(settings, initialize=False)
    except ValueError as exc:
        assert "Unsupported SERVICEOPS_DATABASE_URL" in str(exc)
    else:
        raise AssertionError("expected unsupported database URL to fail")


def test_ai_suggestion_repository_factory_uses_postgres_for_postgresql_url() -> None:
    settings = Settings(database_url="postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops")

    repository = create_ai_suggestion_repository(settings, initialize=False)

    assert isinstance(repository, PostgresAiSuggestionRepository)


def test_ai_suggestion_repository_factory_uses_sqlite_for_sqlite_url() -> None:
    settings = Settings(database_url="sqlite:///:memory:")

    repository = create_ai_suggestion_repository(settings)

    assert isinstance(repository, SqliteAiSuggestionRepository)


def test_ai_suggestion_repository_factory_rejects_unknown_database_url() -> None:
    settings = Settings(database_url="mysql://serviceops:serviceops@localhost/serviceops")

    try:
        create_ai_suggestion_repository(settings, initialize=False)
    except ValueError as exc:
        assert "Unsupported SERVICEOPS_DATABASE_URL" in str(exc)
    else:
        raise AssertionError("expected unsupported database URL to fail")


def test_postgres_repository_uses_autocommit_connections(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_connect(*args, **kwargs):
        calls.append(kwargs)
        raise RuntimeError("stop before opening a real connection")

    monkeypatch.setattr("serviceops_api.service_requests.repository.psycopg.connect", fake_connect)
    repository = PostgresServiceRequestRepository(
        "postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops",
        initialize=False,
    )

    try:
        repository._connect()
    except RuntimeError as exc:
        assert str(exc) == "stop before opening a real connection"
    else:
        raise AssertionError("expected fake connection to stop the test")

    assert calls == [{"row_factory": dict_row, "autocommit": True}]
