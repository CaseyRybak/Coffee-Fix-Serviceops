from __future__ import annotations

import json
from typing import Any

from serviceops_api.config import Settings, get_settings
from serviceops_api.knowledge_base.embeddings import EmbeddingProvider, create_embedding_provider
from serviceops_api.knowledge_base.repository import KnowledgeBaseStore, create_knowledge_base_repository
from serviceops_api.knowledge_base.seed_documents import REPAIR_KNOWLEDGE_SEED_DOCUMENTS
from serviceops_api.knowledge_base.use_cases import IngestKnowledgeDocument


def seed_knowledge_base(
    settings: Settings | None = None,
    repository: KnowledgeBaseStore | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> dict[str, Any]:
    resolved_settings = settings or get_settings()
    knowledge_repository = repository or create_knowledge_base_repository(resolved_settings)
    provider = embedding_provider or create_embedding_provider(resolved_settings)
    ingest_document = IngestKnowledgeDocument(knowledge_repository, provider)

    inserted = 0
    skipped = 0
    for document in REPAIR_KNOWLEDGE_SEED_DOCUMENTS:
        if document.source_uri and knowledge_repository.source_uri_exists(document.source_uri):
            skipped += 1
            continue
        ingest_document.execute(document)
        inserted += 1

    return {
        "status": "ok",
        "inserted": inserted,
        "skipped": skipped,
        "total": len(REPAIR_KNOWLEDGE_SEED_DOCUMENTS),
    }


def main() -> None:
    print(json.dumps(seed_knowledge_base(), sort_keys=True))


if __name__ == "__main__":
    main()
