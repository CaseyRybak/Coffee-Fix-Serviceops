from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Protocol

from celery import shared_task


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector for each input text."""


class KnowledgeChunkRepository(Protocol):
    def list_chunks_missing_embeddings(self, document_id: int) -> list[dict[str, object]]:
        """Return chunks that still need embeddings."""

    def save_chunk_embeddings(self, document_id: int, embeddings_by_chunk_id: dict[int, list[float]]) -> None:
        """Persist embeddings keyed by chunk id."""


class DeterministicEmbeddingProvider:
    def __init__(self, dimensions: int = 12) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be greater than zero")
        self.dimensions = dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[a-zа-я0-9]+", text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
            bucket = int.from_bytes(digest[:2], "big") % self.dimensions
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vector[bucket] += sign
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [round(value / magnitude, 8) for value in vector]


class PostgresKnowledgeChunkRepository:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connection: object | None = None

    def list_chunks_missing_embeddings(self, document_id: int) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT id, content
            FROM knowledge_chunks
            WHERE document_id = %s AND embedding IS NULL
            ORDER BY chunk_index
            """,
            (document_id,),
        ).fetchall()
        return [{"chunk_id": row["id"], "content": row["content"]} for row in rows]

    def save_chunk_embeddings(self, document_id: int, embeddings_by_chunk_id: dict[int, list[float]]) -> None:
        connection = self._connect()
        with connection.transaction():
            for chunk_id, embedding in embeddings_by_chunk_id.items():
                connection.execute(
                    """
                    UPDATE knowledge_chunks
                    SET embedding = %s::vector
                    WHERE id = %s AND document_id = %s
                    """,
                    (_vector_literal(embedding), chunk_id, document_id),
                )
            connection.execute(
                """
                UPDATE knowledge_documents
                SET status = %s, embedded_at = now()
                WHERE id = %s
                """,
                ("embedded", document_id),
            )

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection


def embed_document_chunks(
    document_id: int,
    repository: KnowledgeChunkRepository,
    embedding_provider: EmbeddingProvider,
) -> dict[str, object]:
    chunks = repository.list_chunks_missing_embeddings(document_id)
    embeddings = embedding_provider.embed_texts([str(chunk["content"]) for chunk in chunks])
    repository.save_chunk_embeddings(
        document_id,
        {
            int(chunk["chunk_id"]): embedding
            for chunk, embedding in zip(chunks, embeddings)
        },
    )
    return {"document_id": document_id, "embedded_chunks": len(chunks)}


def _default_embedding_provider() -> DeterministicEmbeddingProvider:
    dimensions = int(os.getenv("SERVICEOPS_KNOWLEDGE_EMBEDDING_DIMENSIONS", "12"))
    return DeterministicEmbeddingProvider(dimensions=dimensions)


def _default_repository() -> KnowledgeChunkRepository:
    database_url = os.getenv("SERVICEOPS_DATABASE_URL", "").strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresKnowledgeChunkRepository(database_url)
    raise RuntimeError("SERVICEOPS_DATABASE_URL must be a PostgreSQL URL for knowledge embedding tasks")


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


@shared_task(name="serviceops_worker.knowledge_base_tasks.embed_knowledge_document")
def embed_knowledge_document(document_id: int) -> dict[str, object]:
    return embed_document_chunks(
        document_id,
        _default_repository(),
        _default_embedding_provider(),
    )
