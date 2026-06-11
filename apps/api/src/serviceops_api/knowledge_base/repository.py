from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row

from serviceops_api.knowledge_base.chunking import TextChunk
from serviceops_api.knowledge_base.embeddings import cosine_similarity


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
SERVICE_REQUEST_MIGRATION_PATH = MIGRATIONS_DIR / "0001_service_request_intake.sql"
KNOWLEDGE_BASE_MIGRATION_PATH = MIGRATIONS_DIR / "0002_knowledge_base_rag.sql"


class KnowledgeBaseStore(Protocol):
    def save_document(
        self,
        title: str,
        source_uri: str | None,
        body: str,
        metadata: dict[str, Any],
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> dict[str, object]:
        """Persist a knowledge document with chunk embeddings."""

    def get_document(self, document_id: int) -> dict[str, object]:
        """Return a document snapshot."""

    def list_chunks_missing_embeddings(self, document_id: int) -> list[dict[str, object]]:
        """Return chunks without embeddings for a document."""

    def save_chunk_embeddings(self, document_id: int, embeddings_by_chunk_id: dict[int, list[float]]) -> None:
        """Persist chunk embeddings for a document."""

    def source_uri_exists(self, source_uri: str) -> bool:
        """Return whether a document with this source URI already exists."""

    def retrieve(self, query_embedding: list[float], limit: int) -> list[dict[str, object]]:
        """Return relevant chunks for an embedding query."""


class SqliteKnowledgeBaseRepository:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    @classmethod
    def in_memory(cls) -> "SqliteKnowledgeBaseRepository":
        return cls(":memory:")

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_uri TEXT,
                body TEXT NOT NULL,
                metadata TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                embedded_at TEXT
            );

            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL REFERENCES knowledge_documents(id),
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                start_char INTEGER NOT NULL,
                end_char INTEGER NOT NULL,
                embedding TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

    def save_document(
        self,
        title: str,
        source_uri: str | None,
        body: str,
        metadata: dict[str, Any],
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> dict[str, object]:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        status = "embedded" if chunks else "pending_embedding"
        with self._connection:
            document_cursor = self._connection.execute(
                """
                INSERT INTO knowledge_documents (
                    title, source_uri, body, metadata, status, embedded_at
                )
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (title, source_uri, body, json.dumps(metadata, sort_keys=True), status),
            )
            document_id = int(document_cursor.lastrowid)
            for chunk, embedding in zip(chunks, embeddings):
                self._connection.execute(
                    """
                    INSERT INTO knowledge_chunks (
                        document_id, chunk_index, content, start_char, end_char, embedding
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.start_char,
                        chunk.end_char,
                        json.dumps(embedding),
                    ),
                )
        return {
            "document_id": document_id,
            "title": title,
            "source_uri": source_uri,
            "status": status,
            "chunk_count": len(chunks),
        }

    def get_document(self, document_id: int) -> dict[str, object]:
        row = self._connection.execute(
            """
            SELECT id, title, source_uri, body, metadata, status, created_at, embedded_at
            FROM knowledge_documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(document_id))
        return {
            "document_id": row["id"],
            "title": row["title"],
            "source_uri": row["source_uri"],
            "body": row["body"],
            "metadata": json.loads(row["metadata"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "embedded_at": row["embedded_at"],
        }

    def list_chunks_missing_embeddings(self, document_id: int) -> list[dict[str, object]]:
        self.get_document(document_id)
        rows = self._connection.execute(
            """
            SELECT id, content
            FROM knowledge_chunks
            WHERE document_id = ? AND embedding IS NULL
            ORDER BY chunk_index
            """,
            (document_id,),
        ).fetchall()
        return [{"chunk_id": row["id"], "content": row["content"]} for row in rows]

    def save_chunk_embeddings(self, document_id: int, embeddings_by_chunk_id: dict[int, list[float]]) -> None:
        self.get_document(document_id)
        with self._connection:
            for chunk_id, embedding in embeddings_by_chunk_id.items():
                self._connection.execute(
                    """
                    UPDATE knowledge_chunks
                    SET embedding = ?
                    WHERE id = ? AND document_id = ?
                    """,
                    (json.dumps(embedding), chunk_id, document_id),
                )
            self._connection.execute(
                """
                UPDATE knowledge_documents
                SET status = ?, embedded_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                ("embedded", document_id),
            )

    def source_uri_exists(self, source_uri: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM knowledge_documents WHERE source_uri = ? LIMIT 1",
            (source_uri,),
        ).fetchone()
        return row is not None

    def retrieve(self, query_embedding: list[float], limit: int) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT
                kc.id AS chunk_id,
                kc.chunk_index,
                kc.content,
                kc.start_char,
                kc.end_char,
                kc.embedding,
                kd.id AS document_id,
                kd.title AS document_title,
                kd.source_uri
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kd.id = kc.document_id
            WHERE kc.embedding IS NOT NULL
            ORDER BY kd.id, kc.chunk_index
            """
        ).fetchall()
        ranked: list[dict[str, object]] = []
        for row in rows:
            score = cosine_similarity(query_embedding, json.loads(row["embedding"]))
            ranked.append(
                {
                    "document_id": row["document_id"],
                    "document_title": row["document_title"],
                    "source_uri": row["source_uri"],
                    "chunk_id": row["chunk_id"],
                    "chunk_index": row["chunk_index"],
                    "start_char": row["start_char"],
                    "end_char": row["end_char"],
                    "content": row["content"],
                    "score": score,
                }
            )
        return sorted(ranked, key=lambda item: float(item["score"]), reverse=True)[:limit]


class PostgresKnowledgeBaseRepository:
    def __init__(self, database_url: str, initialize: bool = True) -> None:
        self._database_url = self._normalize_database_url(database_url)
        self._connection: psycopg.Connection[dict[str, Any]] | None = None
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        connection = self._connect()
        connection.execute(SERVICE_REQUEST_MIGRATION_PATH.read_text(encoding="utf-8"))
        connection.execute(KNOWLEDGE_BASE_MIGRATION_PATH.read_text(encoding="utf-8"))
        connection.commit()

    def save_document(
        self,
        title: str,
        source_uri: str | None,
        body: str,
        metadata: dict[str, Any],
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> dict[str, object]:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        status = "embedded" if chunks else "pending_embedding"
        connection = self._connect()
        with connection.transaction():
            document_row = connection.execute(
                """
                INSERT INTO knowledge_documents (
                    title, source_uri, body, metadata, status, embedded_at
                )
                VALUES (%s, %s, %s, %s, %s, now())
                RETURNING id
                """,
                (title, source_uri, body, json.dumps(metadata, sort_keys=True), status),
            ).fetchone()
            if document_row is None:
                raise RuntimeError("knowledge document insert did not return an id")
            document_id = int(document_row["id"])
            for chunk, embedding in zip(chunks, embeddings):
                connection.execute(
                    """
                    INSERT INTO knowledge_chunks (
                        document_id, chunk_index, content, start_char, end_char, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::vector)
                    """,
                    (
                        document_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.start_char,
                        chunk.end_char,
                        self._vector_literal(embedding),
                    ),
                )
        return {
            "document_id": document_id,
            "title": title,
            "source_uri": source_uri,
            "status": status,
            "chunk_count": len(chunks),
        }

    def get_document(self, document_id: int) -> dict[str, object]:
        row = self._connect().execute(
            """
            SELECT id, title, source_uri, body, metadata, status, created_at, embedded_at
            FROM knowledge_documents
            WHERE id = %s
            """,
            (document_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(document_id))
        metadata = row["metadata"]
        return {
            "document_id": row["id"],
            "title": row["title"],
            "source_uri": row["source_uri"],
            "body": row["body"],
            "metadata": metadata if isinstance(metadata, dict) else json.loads(metadata),
            "status": row["status"],
            "created_at": self._format_timestamp(row["created_at"]),
            "embedded_at": None if row["embedded_at"] is None else self._format_timestamp(row["embedded_at"]),
        }

    def list_chunks_missing_embeddings(self, document_id: int) -> list[dict[str, object]]:
        self.get_document(document_id)
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
        self.get_document(document_id)
        connection = self._connect()
        with connection.transaction():
            for chunk_id, embedding in embeddings_by_chunk_id.items():
                connection.execute(
                    """
                    UPDATE knowledge_chunks
                    SET embedding = %s::vector
                    WHERE id = %s AND document_id = %s
                    """,
                    (self._vector_literal(embedding), chunk_id, document_id),
                )
            connection.execute(
                """
                UPDATE knowledge_documents
                SET status = %s, embedded_at = now()
                WHERE id = %s
                """,
                ("embedded", document_id),
            )

    def source_uri_exists(self, source_uri: str) -> bool:
        row = self._connect().execute(
            "SELECT 1 FROM knowledge_documents WHERE source_uri = %s LIMIT 1",
            (source_uri,),
        ).fetchone()
        return row is not None

    def retrieve(self, query_embedding: list[float], limit: int) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT
                kc.id AS chunk_id,
                kc.chunk_index,
                kc.content,
                kc.start_char,
                kc.end_char,
                kd.id AS document_id,
                kd.title AS document_title,
                kd.source_uri,
                1 - (kc.embedding <=> %s::vector) AS score
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kd.id = kc.document_id
            WHERE kc.embedding IS NOT NULL
            ORDER BY kc.embedding <=> %s::vector
            LIMIT %s
            """,
            (self._vector_literal(query_embedding), self._vector_literal(query_embedding), limit),
        ).fetchall()
        return [
            {
                "document_id": row["document_id"],
                "document_title": row["document_title"],
                "source_uri": row["source_uri"],
                "chunk_id": row["chunk_id"],
                "chunk_index": row["chunk_index"],
                "start_char": row["start_char"],
                "end_char": row["end_char"],
                "content": row["content"],
                "score": float(row["score"]),
            }
            for row in rows
        ]

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection

    def _normalize_database_url(self, database_url: str) -> str:
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)

    def _vector_literal(self, embedding: list[float]) -> str:
        return "[" + ",".join(str(value) for value in embedding) + "]"

    def _format_timestamp(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)


def create_knowledge_base_repository(
    settings: Any,
    initialize: bool = True,
) -> SqliteKnowledgeBaseRepository | PostgresKnowledgeBaseRepository:
    database_url = settings.database_url.strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresKnowledgeBaseRepository(database_url, initialize=initialize)
    if database_url.startswith("sqlite:///"):
        return SqliteKnowledgeBaseRepository(database_url.removeprefix("sqlite:///"))
    if database_url == "sqlite:///:memory:":
        return SqliteKnowledgeBaseRepository.in_memory()
    if not database_url:
        return SqliteKnowledgeBaseRepository(settings.knowledge_sqlite_path)
    raise ValueError(f"Unsupported SERVICEOPS_DATABASE_URL: {database_url}")
