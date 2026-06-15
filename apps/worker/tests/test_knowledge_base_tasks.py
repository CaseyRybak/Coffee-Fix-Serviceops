import json
import logging

from serviceops_worker.celery_app import create_celery_app
from serviceops_worker.knowledge_base_tasks import (
    DeterministicEmbeddingProvider,
    OpenAiCompatibleEmbeddingProvider,
    _default_embedding_provider,
    embed_document_chunks,
    embed_knowledge_document,
)


class FakeKnowledgeChunkRepository:
    def __init__(self) -> None:
        self.saved: dict[int, list[float]] = {}

    def list_chunks_missing_embeddings(self, document_id: int) -> list[dict[str, object]]:
        assert document_id == 42
        return [
            {"chunk_id": 7, "content": "E61 thermosiphon scale"},
            {"chunk_id": 8, "content": "Boiler pressure and pressurestat"},
        ]

    def save_chunk_embeddings(self, document_id: int, embeddings_by_chunk_id: dict[int, list[float]]) -> None:
        assert document_id == 42
        self.saved = embeddings_by_chunk_id


class FailingEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("provider response included secret document body")


def test_celery_app_registers_knowledge_base_embedding_task() -> None:
    app = create_celery_app()

    assert "serviceops_worker.knowledge_base_tasks.embed_knowledge_document" in app.tasks


def test_embed_document_chunks_uses_provider_without_network_calls() -> None:
    repository = FakeKnowledgeChunkRepository()
    provider = DeterministicEmbeddingProvider(dimensions=12)

    result = embed_document_chunks(42, repository, provider)

    assert result == {"document_id": 42, "embedded_chunks": 2}
    assert sorted(repository.saved) == [7, 8]
    assert all(len(embedding) == 12 for embedding in repository.saved.values())


def test_embed_document_chunks_logs_success_without_chunk_content(caplog) -> None:
    repository = FakeKnowledgeChunkRepository()
    provider = DeterministicEmbeddingProvider(dimensions=12)

    with caplog.at_level(logging.INFO, logger="serviceops_worker.knowledge_base_tasks"):
        result = embed_document_chunks(42, repository, provider)

    assert result == {"document_id": 42, "embedded_chunks": 2}
    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    started = next(context for context in contexts if context["action"] == "knowledge_base.embedding_started")
    succeeded = next(context for context in contexts if context["action"] == "knowledge_base.embedding_completed")
    assert started == {
        "action": "knowledge_base.embedding_started",
        "target": "document:42",
        "outcome": "succeeded",
        "provider": "deterministic",
    }
    assert succeeded["target"] == "document:42"
    assert succeeded["outcome"] == "succeeded"
    assert succeeded["provider"] == "deterministic"
    assert isinstance(succeeded["duration_ms"], int)
    assert "E61 thermosiphon scale" not in str(contexts)
    assert "Boiler pressure" not in str(contexts)


def test_embed_document_chunks_logs_failure_without_provider_body(caplog) -> None:
    repository = FakeKnowledgeChunkRepository()

    with caplog.at_level(logging.INFO, logger="serviceops_worker.knowledge_base_tasks"):
        try:
            embed_document_chunks(42, repository, FailingEmbeddingProvider())
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected embedding failure")

    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    failed = next(context for context in contexts if context["action"] == "knowledge_base.embedding_completed")
    assert failed["target"] == "document:42"
    assert failed["outcome"] == "failed"
    assert failed["provider"] == "FailingEmbeddingProvider"
    assert failed["reason"] == "embedding_failed"
    assert "secret document body" not in str(contexts)


def test_default_embedding_provider_is_deterministic(monkeypatch) -> None:
    monkeypatch.delenv("SERVICEOPS_EMBEDDING_PROVIDER", raising=False)
    monkeypatch.setenv("SERVICEOPS_KNOWLEDGE_EMBEDDING_DIMENSIONS", "12")

    provider = _default_embedding_provider()

    assert isinstance(provider, DeterministicEmbeddingProvider)


def test_default_embedding_provider_supports_live_openai_compatible(monkeypatch) -> None:
    monkeypatch.setenv("SERVICEOPS_EMBEDDING_PROVIDER", "openai-compatible")
    monkeypatch.setenv("SERVICEOPS_EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("SERVICEOPS_EMBEDDING_API_KEY", "test-key")

    provider = _default_embedding_provider()

    assert isinstance(provider, OpenAiCompatibleEmbeddingProvider)


def test_default_embedding_provider_requires_live_key(monkeypatch) -> None:
    monkeypatch.setenv("SERVICEOPS_EMBEDDING_PROVIDER", "openai-compatible")
    monkeypatch.setenv("SERVICEOPS_EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.delenv("SERVICEOPS_EMBEDDING_API_KEY", raising=False)

    try:
        _default_embedding_provider()
    except ValueError as exc:
        assert "SERVICEOPS_EMBEDDING_API_KEY is required" in str(exc)
    else:
        raise AssertionError("expected missing embedding key failure")


def test_live_embedding_provider_masks_malformed_transport_json() -> None:
    def fake_post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
        raise json.JSONDecodeError("provider leaked body with secret-key", doc="secret-key", pos=0)

    provider = OpenAiCompatibleEmbeddingProvider(
        api_base_url="https://provider.example/v1",
        api_key="secret-key",
        model="text-embedding-3-small",
        timeout_seconds=5,
        max_retries=0,
        post_json=fake_post_json,
    )

    try:
        provider.embed_texts(["first"])
    except RuntimeError as exc:
        assert str(exc) == "Embedding provider request failed"
        assert "secret-key" not in str(exc)
    else:
        raise AssertionError("expected malformed provider response failure")


def test_embed_knowledge_document_task_uses_configured_repository(monkeypatch) -> None:
    repository = FakeKnowledgeChunkRepository()

    monkeypatch.setattr(
        "serviceops_worker.knowledge_base_tasks._default_repository",
        lambda: repository,
    )
    monkeypatch.setenv("SERVICEOPS_KNOWLEDGE_EMBEDDING_DIMENSIONS", "12")

    result = embed_knowledge_document.run(42)

    assert result == {"document_id": 42, "embedded_chunks": 2}
    assert sorted(repository.saved) == [7, 8]
