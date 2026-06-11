from serviceops_api.knowledge_base.embeddings import DeterministicEmbeddingProvider
from serviceops_api.knowledge_base.repository import SqliteKnowledgeBaseRepository
from serviceops_api.operations.seed_knowledge_base import seed_knowledge_base


def test_seed_knowledge_base_ingests_seed_documents_once() -> None:
    repository = SqliteKnowledgeBaseRepository.in_memory()
    embedding_provider = DeterministicEmbeddingProvider(dimensions=12)

    first_result = seed_knowledge_base(repository=repository, embedding_provider=embedding_provider)
    second_result = seed_knowledge_base(repository=repository, embedding_provider=embedding_provider)

    assert first_result["inserted"] == 9
    assert first_result["skipped"] == 0
    assert second_result["inserted"] == 0
    assert second_result["skipped"] == 9
    assert second_result["status"] == "ok"
