from __future__ import annotations

from serviceops_api.knowledge_base.chunking import chunk_text
from serviceops_api.knowledge_base.embeddings import EmbeddingProvider
from serviceops_api.knowledge_base.models import (
    IngestKnowledgeDocumentPayload,
    KnowledgeDocumentResponse,
    KnowledgeRetrievalPayload,
    KnowledgeRetrievalResponse,
)
from serviceops_api.knowledge_base.repository import KnowledgeBaseStore


class IngestKnowledgeDocument:
    def __init__(self, repository: KnowledgeBaseStore, embedding_provider: EmbeddingProvider) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider

    def execute(self, payload: IngestKnowledgeDocumentPayload) -> KnowledgeDocumentResponse:
        chunks = chunk_text(payload.body)
        embeddings = self._embedding_provider.embed_texts([chunk.content for chunk in chunks])
        return KnowledgeDocumentResponse.model_validate(
            self._repository.save_document(
                title=payload.title,
                source_uri=payload.source_uri,
                body=payload.body,
                metadata=payload.metadata,
                chunks=chunks,
                embeddings=embeddings,
            )
        )


class RetrieveKnowledge:
    def __init__(self, repository: KnowledgeBaseStore, embedding_provider: EmbeddingProvider) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider

    def execute(self, payload: KnowledgeRetrievalPayload) -> KnowledgeRetrievalResponse:
        query_embedding = self._embedding_provider.embed_texts([payload.query])[0]
        return KnowledgeRetrievalResponse.model_validate(
            {
                "query": payload.query,
                "results": self._repository.retrieve(query_embedding, payload.limit),
            }
        )
