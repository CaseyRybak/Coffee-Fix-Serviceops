from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row

from serviceops_api.ai_agents.models import AiSuggestionCreate


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
SERVICE_REQUEST_MIGRATION_PATH = MIGRATIONS_DIR / "0001_service_request_intake.sql"
KNOWLEDGE_BASE_MIGRATION_PATH = MIGRATIONS_DIR / "0002_knowledge_base_rag.sql"
AI_SUGGESTIONS_MIGRATION_PATH = MIGRATIONS_DIR / "0003_ai_suggestions.sql"


class AiSuggestionStore(Protocol):
    def save_suggestions(self, request_number: str, suggestions: list[AiSuggestionCreate]) -> list[dict[str, object]]:
        """Persist AI suggestions for dispatcher review."""

    def replace_pending_suggestions(
        self, request_number: str, suggestions: list[AiSuggestionCreate]
    ) -> list[dict[str, object]]:
        """Replace pending suggestions for a request while preserving acted-on suggestions."""

    def list_suggestions(self, request_number: str) -> list[dict[str, object]]:
        """Return suggestions for a request."""

    def get_suggestion(self, suggestion_id: int) -> dict[str, object]:
        """Return one suggestion by id."""

    def mark_accepted(self, suggestion_id: int) -> dict[str, object]:
        """Mark a suggestion accepted."""

    def mark_ignored(self, suggestion_id: int) -> dict[str, object]:
        """Mark a suggestion ignored."""


class SqliteAiSuggestionRepository:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    @classmethod
    def in_memory(cls) -> "SqliteAiSuggestionRepository":
        return cls(":memory:")

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ai_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                rationale TEXT NOT NULL,
                confidence REAL NOT NULL,
                source_chunks TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                acted_at TEXT
            );
            """
        )

    def save_suggestions(self, request_number: str, suggestions: list[AiSuggestionCreate]) -> list[dict[str, object]]:
        saved: list[dict[str, object]] = []
        with self._connection:
            for suggestion in suggestions:
                cursor = self._connection.execute(
                    """
                    INSERT INTO ai_suggestions (
                        request_number, kind, title, content, rationale, confidence, source_chunks, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        request_number,
                        suggestion.kind,
                        suggestion.title,
                        suggestion.content,
                        suggestion.rationale,
                        suggestion.confidence,
                        json.dumps([source.model_dump() for source in suggestion.source_chunks], sort_keys=True),
                        "pending",
                    ),
                )
                saved.append(self.get_suggestion(int(cursor.lastrowid)))
        return saved

    def replace_pending_suggestions(
        self, request_number: str, suggestions: list[AiSuggestionCreate]
    ) -> list[dict[str, object]]:
        with self._connection:
            self._connection.execute(
                "DELETE FROM ai_suggestions WHERE request_number = ? AND status = ?",
                (request_number, "pending"),
            )
        return self.save_suggestions(request_number, suggestions)

    def list_suggestions(self, request_number: str) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM ai_suggestions
            WHERE request_number = ?
            ORDER BY id DESC
            """,
            (request_number,),
        ).fetchall()
        return [self._row_to_suggestion(row) for row in rows]

    def get_suggestion(self, suggestion_id: int) -> dict[str, object]:
        row = self._connection.execute("SELECT * FROM ai_suggestions WHERE id = ?", (suggestion_id,)).fetchone()
        if row is None:
            raise KeyError(str(suggestion_id))
        return self._row_to_suggestion(row)

    def mark_accepted(self, suggestion_id: int) -> dict[str, object]:
        return self._mark(suggestion_id, "accepted")

    def mark_ignored(self, suggestion_id: int) -> dict[str, object]:
        return self._mark(suggestion_id, "ignored")

    def _mark(self, suggestion_id: int, status: str) -> dict[str, object]:
        self.get_suggestion(suggestion_id)
        with self._connection:
            self._connection.execute(
                "UPDATE ai_suggestions SET status = ?, acted_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, suggestion_id),
            )
        return self.get_suggestion(suggestion_id)

    def _row_to_suggestion(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "suggestion_id": row["id"],
            "request_number": row["request_number"],
            "kind": row["kind"],
            "title": row["title"],
            "content": row["content"],
            "rationale": row["rationale"],
            "confidence": row["confidence"],
            "source_chunks": json.loads(row["source_chunks"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "acted_at": row["acted_at"],
        }


class PostgresAiSuggestionRepository:
    def __init__(self, database_url: str, initialize: bool = True) -> None:
        self._database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connection: psycopg.Connection[dict[str, Any]] | None = None
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        connection = self._connect()
        connection.execute(SERVICE_REQUEST_MIGRATION_PATH.read_text(encoding="utf-8"))
        connection.execute(KNOWLEDGE_BASE_MIGRATION_PATH.read_text(encoding="utf-8"))
        connection.execute(AI_SUGGESTIONS_MIGRATION_PATH.read_text(encoding="utf-8"))
        connection.commit()

    def save_suggestions(self, request_number: str, suggestions: list[AiSuggestionCreate]) -> list[dict[str, object]]:
        saved: list[dict[str, object]] = []
        connection = self._connect()
        with connection.transaction():
            for suggestion in suggestions:
                row = connection.execute(
                    """
                    INSERT INTO ai_suggestions (
                        request_number, kind, title, content, rationale, confidence, source_chunks, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        request_number,
                        suggestion.kind,
                        suggestion.title,
                        suggestion.content,
                        suggestion.rationale,
                        suggestion.confidence,
                        json.dumps([source.model_dump() for source in suggestion.source_chunks], sort_keys=True),
                        "pending",
                    ),
                ).fetchone()
                if row is None:
                    raise RuntimeError("ai suggestion insert did not return an id")
                saved.append(self.get_suggestion(int(row["id"])))
        return saved

    def replace_pending_suggestions(
        self, request_number: str, suggestions: list[AiSuggestionCreate]
    ) -> list[dict[str, object]]:
        connection = self._connect()
        with connection.transaction():
            connection.execute(
                "DELETE FROM ai_suggestions WHERE request_number = %s AND status = %s",
                (request_number, "pending"),
            )
        return self.save_suggestions(request_number, suggestions)

    def list_suggestions(self, request_number: str) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT *
            FROM ai_suggestions
            WHERE request_number = %s
            ORDER BY id DESC
            """,
            (request_number,),
        ).fetchall()
        return [self._row_to_suggestion(row) for row in rows]

    def get_suggestion(self, suggestion_id: int) -> dict[str, object]:
        row = self._connect().execute("SELECT * FROM ai_suggestions WHERE id = %s", (suggestion_id,)).fetchone()
        if row is None:
            raise KeyError(str(suggestion_id))
        return self._row_to_suggestion(row)

    def mark_accepted(self, suggestion_id: int) -> dict[str, object]:
        return self._mark(suggestion_id, "accepted")

    def mark_ignored(self, suggestion_id: int) -> dict[str, object]:
        return self._mark(suggestion_id, "ignored")

    def _mark(self, suggestion_id: int, status: str) -> dict[str, object]:
        self.get_suggestion(suggestion_id)
        self._connect().execute(
            "UPDATE ai_suggestions SET status = %s, acted_at = now() WHERE id = %s",
            (status, suggestion_id),
        )
        self._connect().commit()
        return self.get_suggestion(suggestion_id)

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection

    def _row_to_suggestion(self, row: dict[str, Any]) -> dict[str, object]:
        source_chunks = row["source_chunks"]
        return {
            "suggestion_id": row["id"],
            "request_number": row["request_number"],
            "kind": row["kind"],
            "title": row["title"],
            "content": row["content"],
            "rationale": row["rationale"],
            "confidence": row["confidence"],
            "source_chunks": source_chunks if isinstance(source_chunks, list) else json.loads(source_chunks),
            "status": row["status"],
            "created_at": self._format_timestamp(row["created_at"]),
            "acted_at": None if row["acted_at"] is None else self._format_timestamp(row["acted_at"]),
        }

    def _format_timestamp(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)


def create_ai_suggestion_repository(
    settings: Any,
    initialize: bool = True,
) -> SqliteAiSuggestionRepository | PostgresAiSuggestionRepository:
    database_url = settings.database_url.strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresAiSuggestionRepository(database_url, initialize=initialize)
    if database_url.startswith("sqlite:///"):
        return SqliteAiSuggestionRepository(database_url.removeprefix("sqlite:///"))
    if database_url == "sqlite:///:memory:":
        return SqliteAiSuggestionRepository.in_memory()
    if not database_url:
        return SqliteAiSuggestionRepository(settings.ai_sqlite_path)
    raise ValueError(f"Unsupported SERVICEOPS_DATABASE_URL: {database_url}")
