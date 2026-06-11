from __future__ import annotations

import re

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
        candidate_limit = max(payload.limit, min(24, payload.limit * 4))
        candidates = self._repository.retrieve(query_embedding, candidate_limit)
        results = _rerank_by_lexical_overlap(payload.query, candidates)[: payload.limit]
        return KnowledgeRetrievalResponse.model_validate(
            {
                "query": payload.query,
                "results": results,
            }
        )


def _rerank_by_lexical_overlap(query: str, results: list[dict[str, object]]) -> list[dict[str, object]]:
    query_terms = _terms(query)
    if not query_terms:
        return results

    def rank(result: dict[str, object]) -> tuple[float, float]:
        content = " ".join(
            str(result.get(field, ""))
            for field in ("document_title", "source_uri", "content")
        )
        content_terms = _terms(content)
        matches = len(query_terms & content_terms)
        vector_score = float(result.get("score", 0.0))
        lexical_boost = min(0.36, matches * 0.09)
        return vector_score + lexical_boost, vector_score

    return sorted(results, key=rank, reverse=True)


def _terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[\wа-яА-ЯёЁ]+", value.lower()) if len(term) >= 3}
