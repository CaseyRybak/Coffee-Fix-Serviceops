from __future__ import annotations

import json
import hashlib
import logging
import math
import os
import re
import time
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Protocol

from celery import shared_task

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector for each input text."""


PostJson = Callable[[str, dict[str, object], dict[str, str], float], dict[str, object]]


def post_json(url: str, body: dict[str, object], headers: dict[str, str], timeout: float) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class KnowledgeChunkRepository(Protocol):
    def list_chunks_missing_embeddings(self, document_id: int) -> list[dict[str, object]]:
        """Return chunks that still need embeddings."""

    def save_chunk_embeddings(self, document_id: int, embeddings_by_chunk_id: dict[int, list[float]]) -> None:
        """Persist embeddings keyed by chunk id."""


class DeterministicEmbeddingProvider:
    def __init__(self, dimensions: int = 1536) -> None:
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


class OpenAiCompatibleEmbeddingProvider:
    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
        post_json: PostJson = post_json,
    ) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._post_json = post_json

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._request_with_retries({"model": self._model, "input": texts})
        try:
            rows = response["data"]
            if not isinstance(rows, list):
                raise ValueError("embedding data missing")
            ordered: dict[int, list[float]] = {}
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("invalid embedding row")
                ordered[int(row["index"])] = [float(value) for value in row["embedding"]]  # type: ignore[index]
            if sorted(ordered) != list(range(len(texts))):
                raise ValueError("embedding count mismatch")
            return [ordered[index] for index in range(len(texts))]
        except Exception as exc:
            raise RuntimeError("Embedding provider request failed") from exc

    def _request_with_retries(self, body: dict[str, object]) -> dict[str, object]:
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        url = f"{self._api_base_url}/embeddings"
        for attempt in range(self._max_retries + 1):
            try:
                return self._post_json(url, body, headers, self._timeout_seconds)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Embedding provider request failed") from exc
            except HTTPError as exc:
                if attempt >= self._max_retries or exc.code not in {408, 409, 425, 429, 500, 502, 503, 504}:
                    raise RuntimeError("Embedding provider request failed") from exc
            except (TimeoutError, URLError, OSError) as exc:
                if attempt >= self._max_retries:
                    raise RuntimeError("Embedding provider request failed") from exc
        raise RuntimeError("Embedding provider request failed")


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
    provider_name = _provider_name(embedding_provider)
    target = f"document:{document_id}"
    started_at = time.monotonic()
    logger.info(
        "Knowledge-base embedding started",
        extra={
            "serviceops_context": {
                "action": "knowledge_base.embedding_started",
                "target": target,
                "outcome": "succeeded",
                "provider": provider_name,
            }
        },
    )
    try:
        chunks = repository.list_chunks_missing_embeddings(document_id)
        embeddings = embedding_provider.embed_texts([str(chunk["content"]) for chunk in chunks])
        repository.save_chunk_embeddings(
            document_id,
            {
                int(chunk["chunk_id"]): embedding
                for chunk, embedding in zip(chunks, embeddings)
            },
        )
    except Exception:
        logger.info(
            "Knowledge-base embedding failed",
            extra={
                "serviceops_context": {
                    "action": "knowledge_base.embedding_completed",
                    "target": target,
                    "outcome": "failed",
                    "reason": "embedding_failed",
                    "duration_ms": _elapsed_ms(started_at),
                    "provider": provider_name,
                }
            },
        )
        raise
    logger.info(
        "Knowledge-base embedding completed",
        extra={
            "serviceops_context": {
                "action": "knowledge_base.embedding_completed",
                "target": target,
                "outcome": "succeeded",
                "duration_ms": _elapsed_ms(started_at),
                "provider": provider_name,
            }
        },
    )
    return {"document_id": document_id, "embedded_chunks": len(chunks)}


def _default_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("SERVICEOPS_EMBEDDING_PROVIDER", "deterministic").strip().lower()
    if provider == "deterministic":
        dimensions = int(os.getenv("SERVICEOPS_KNOWLEDGE_EMBEDDING_DIMENSIONS", "1536"))
        return DeterministicEmbeddingProvider(dimensions=dimensions)
    if provider == "openai-compatible":
        api_key = os.getenv("SERVICEOPS_EMBEDDING_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "SERVICEOPS_EMBEDDING_API_KEY is required when SERVICEOPS_EMBEDDING_PROVIDER=openai-compatible"
            )
        model = os.getenv("SERVICEOPS_EMBEDDING_MODEL", "").strip()
        if not model:
            raise ValueError(
                "SERVICEOPS_EMBEDDING_MODEL is required when SERVICEOPS_EMBEDDING_PROVIDER=openai-compatible"
            )
        return OpenAiCompatibleEmbeddingProvider(
            api_base_url=os.getenv("SERVICEOPS_EMBEDDING_API_BASE_URL", "https://api.openai.com/v1"),
            api_key=api_key,
            model=model,
            timeout_seconds=float(os.getenv("SERVICEOPS_EMBEDDING_TIMEOUT_SECONDS", "20")),
            max_retries=int(os.getenv("SERVICEOPS_EMBEDDING_MAX_RETRIES", "2")),
        )
    raise ValueError(f"Unsupported SERVICEOPS_EMBEDDING_PROVIDER: {provider}")


def _default_repository() -> KnowledgeChunkRepository:
    database_url = os.getenv("SERVICEOPS_DATABASE_URL", "").strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresKnowledgeChunkRepository(database_url)
    raise RuntimeError("SERVICEOPS_DATABASE_URL must be a PostgreSQL URL for knowledge embedding tasks")


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


def _elapsed_ms(started_at: float) -> int:
    return max(0, int((time.monotonic() - started_at) * 1000))


def _provider_name(provider: EmbeddingProvider) -> str:
    class_name = provider.__class__.__name__.lower()
    if "openai" in class_name:
        return "openai-compatible"
    if "deterministic" in class_name:
        return "deterministic"
    return provider.__class__.__name__


@shared_task(name="serviceops_worker.knowledge_base_tasks.embed_knowledge_document")
def embed_knowledge_document(document_id: int) -> dict[str, object]:
    return embed_document_chunks(
        document_id,
        _default_repository(),
        _default_embedding_provider(),
    )
