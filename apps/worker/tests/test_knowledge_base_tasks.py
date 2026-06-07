from serviceops_worker.celery_app import create_celery_app
from serviceops_worker.knowledge_base_tasks import (
    DeterministicEmbeddingProvider,
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
