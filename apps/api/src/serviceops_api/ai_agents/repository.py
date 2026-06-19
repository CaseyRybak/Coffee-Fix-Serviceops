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
AI_ASSISTANT_MIGRATION_PATH = MIGRATIONS_DIR / "0015_ai_assistant_runs.sql"


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


class AiAssistantHistoryStore(Protocol):
    def save_run(
        self,
        *,
        actor_username: str,
        safe_message: str,
        status: str,
        assistant_message: str,
        tool_calls: list[dict[str, object]],
    ) -> dict[str, object]:
        """Persist one assistant run with safe tool-call records."""

    def list_runs(self, actor_username: str) -> list[dict[str, object]]:
        """Return assistant runs for one staff actor."""

    def get_run(self, run_id: int, actor_username: str) -> dict[str, object]:
        """Return one assistant run for one staff actor."""

    def claim_run_for_confirmation(self, run_id: int, actor_username: str) -> dict[str, object]:
        """Atomically claim a confirmation-required run before executing its mutating tool."""

    def update_run_after_confirmation(
        self,
        *,
        run_id: int,
        actor_username: str,
        status: str,
        assistant_message: str,
        tool_call: dict[str, object],
    ) -> dict[str, object]:
        """Update one pending run after a confirmed mutating tool executes."""

    def mark_run_failed(self, run_id: int, actor_username: str, result_summary: str) -> dict[str, object]:
        """Mark a claimed run failed without exposing raw error details."""


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


class SqliteAiAssistantHistoryRepository:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    @classmethod
    def in_memory(cls) -> "SqliteAiAssistantHistoryRepository":
        return cls(":memory:")

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ai_assistant_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_username TEXT NOT NULL,
                safe_message TEXT NOT NULL,
                status TEXT NOT NULL,
                assistant_message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ai_assistant_tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES ai_assistant_runs(id) ON DELETE CASCADE,
                tool_name TEXT NOT NULL,
                policy TEXT NOT NULL,
                status TEXT NOT NULL,
                arguments_json TEXT NOT NULL,
                result_summary TEXT NOT NULL,
                result_refs_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

    def save_run(
        self,
        *,
        actor_username: str,
        safe_message: str,
        status: str,
        assistant_message: str,
        tool_calls: list[dict[str, object]],
    ) -> dict[str, object]:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO ai_assistant_runs (actor_username, safe_message, status, assistant_message)
                VALUES (?, ?, ?, ?)
                """,
                (actor_username, safe_message, status, assistant_message),
            )
            run_id = int(cursor.lastrowid)
            for tool_call in tool_calls:
                self._insert_tool_call(run_id, tool_call)
        return self.get_run(run_id, actor_username)

    def list_runs(self, actor_username: str) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM ai_assistant_runs
            WHERE actor_username = ?
            ORDER BY id DESC
            """,
            (actor_username,),
        ).fetchall()
        return [self._row_to_run(row) for row in rows]

    def get_run(self, run_id: int, actor_username: str) -> dict[str, object]:
        row = self._connection.execute(
            "SELECT * FROM ai_assistant_runs WHERE id = ? AND actor_username = ?",
            (run_id, actor_username),
        ).fetchone()
        if row is None:
            raise KeyError(str(run_id))
        return self._row_to_run(row)

    def claim_run_for_confirmation(self, run_id: int, actor_username: str) -> dict[str, object]:
        self.get_run(run_id, actor_username)
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE ai_assistant_runs
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND actor_username = ? AND status = ?
                """,
                ("executing", run_id, actor_username, "confirmation_required"),
            )
            if cursor.rowcount != 1:
                raise ValueError("Assistant run does not require confirmation")
            self._connection.execute(
                """
                UPDATE ai_assistant_tool_calls
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE run_id = ? AND status = ?
                """,
                ("executing", run_id, "confirmation_required"),
            )
        return self.get_run(run_id, actor_username)

    def update_run_after_confirmation(
        self,
        *,
        run_id: int,
        actor_username: str,
        status: str,
        assistant_message: str,
        tool_call: dict[str, object],
    ) -> dict[str, object]:
        self.get_run(run_id, actor_username)
        with self._connection:
            self._connection.execute(
                "UPDATE ai_assistant_runs SET status = ?, assistant_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, assistant_message, run_id),
            )
            self._connection.execute(
                """
                UPDATE ai_assistant_tool_calls
                SET status = ?, result_summary = ?, result_refs_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE run_id = ? AND tool_name = ?
                """,
                (
                    tool_call["status"],
                    tool_call["result_summary"],
                    json.dumps(tool_call.get("result_refs", []), sort_keys=True),
                    run_id,
                    tool_call["tool_name"],
                ),
            )
        return self.get_run(run_id, actor_username)

    def mark_run_failed(self, run_id: int, actor_username: str, result_summary: str) -> dict[str, object]:
        self.get_run(run_id, actor_username)
        with self._connection:
            self._connection.execute(
                "UPDATE ai_assistant_runs SET status = ?, assistant_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("failed", "Assistant tool request failed.", run_id),
            )
            self._connection.execute(
                """
                UPDATE ai_assistant_tool_calls
                SET status = ?, result_summary = ?, updated_at = CURRENT_TIMESTAMP
                WHERE run_id = ? AND status = ?
                """,
                ("failed", result_summary, run_id, "executing"),
            )
        return self.get_run(run_id, actor_username)

    def _insert_tool_call(self, run_id: int, tool_call: dict[str, object]) -> None:
        self._connection.execute(
            """
            INSERT INTO ai_assistant_tool_calls (
                run_id, tool_name, policy, status, arguments_json, result_summary, result_refs_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                tool_call["tool_name"],
                tool_call["policy"],
                tool_call["status"],
                json.dumps(tool_call.get("arguments", {}), sort_keys=True),
                tool_call["result_summary"],
                json.dumps(tool_call.get("result_refs", []), sort_keys=True),
            ),
        )

    def _row_to_run(self, row: sqlite3.Row) -> dict[str, object]:
        tool_rows = self._connection.execute(
            """
            SELECT *
            FROM ai_assistant_tool_calls
            WHERE run_id = ?
            ORDER BY id
            """,
            (row["id"],),
        ).fetchall()
        return {
            "run_id": row["id"],
            "actor_username": row["actor_username"],
            "safe_message": row["safe_message"],
            "status": row["status"],
            "assistant_message": row["assistant_message"],
            "tool_calls": [self._row_to_tool_call(tool_row) for tool_row in tool_rows],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _row_to_tool_call(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "tool_call_id": row["id"],
            "tool_name": row["tool_name"],
            "policy": row["policy"],
            "status": row["status"],
            "arguments": json.loads(row["arguments_json"]),
            "result_summary": row["result_summary"],
            "result_refs": json.loads(row["result_refs_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
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


class PostgresAiAssistantHistoryRepository:
    def __init__(self, database_url: str, initialize: bool = True) -> None:
        self._database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connection: psycopg.Connection[dict[str, Any]] | None = None
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        connection = self._connect()
        connection.execute(AI_ASSISTANT_MIGRATION_PATH.read_text(encoding="utf-8"))
        connection.commit()

    def save_run(
        self,
        *,
        actor_username: str,
        safe_message: str,
        status: str,
        assistant_message: str,
        tool_calls: list[dict[str, object]],
    ) -> dict[str, object]:
        connection = self._connect()
        with connection.transaction():
            row = connection.execute(
                """
                INSERT INTO ai_assistant_runs (actor_username, safe_message, status, assistant_message)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (actor_username, safe_message, status, assistant_message),
            ).fetchone()
            if row is None:
                raise RuntimeError("assistant run insert did not return an id")
            run_id = int(row["id"])
            for tool_call in tool_calls:
                self._insert_tool_call(run_id, tool_call)
        return self.get_run(run_id, actor_username)

    def list_runs(self, actor_username: str) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT *
            FROM ai_assistant_runs
            WHERE actor_username = %s
            ORDER BY id DESC
            """,
            (actor_username,),
        ).fetchall()
        return [self._row_to_run(row) for row in rows]

    def get_run(self, run_id: int, actor_username: str) -> dict[str, object]:
        row = self._connect().execute(
            "SELECT * FROM ai_assistant_runs WHERE id = %s AND actor_username = %s",
            (run_id, actor_username),
        ).fetchone()
        if row is None:
            raise KeyError(str(run_id))
        return self._row_to_run(row)

    def claim_run_for_confirmation(self, run_id: int, actor_username: str) -> dict[str, object]:
        self.get_run(run_id, actor_username)
        connection = self._connect()
        with connection.transaction():
            cursor = connection.execute(
                """
                UPDATE ai_assistant_runs
                SET status = %s, updated_at = now()
                WHERE id = %s AND actor_username = %s AND status = %s
                """,
                ("executing", run_id, actor_username, "confirmation_required"),
            )
            if cursor.rowcount != 1:
                raise ValueError("Assistant run does not require confirmation")
            connection.execute(
                """
                UPDATE ai_assistant_tool_calls
                SET status = %s, updated_at = now()
                WHERE run_id = %s AND status = %s
                """,
                ("executing", run_id, "confirmation_required"),
            )
        return self.get_run(run_id, actor_username)

    def update_run_after_confirmation(
        self,
        *,
        run_id: int,
        actor_username: str,
        status: str,
        assistant_message: str,
        tool_call: dict[str, object],
    ) -> dict[str, object]:
        self.get_run(run_id, actor_username)
        connection = self._connect()
        with connection.transaction():
            connection.execute(
                "UPDATE ai_assistant_runs SET status = %s, assistant_message = %s, updated_at = now() WHERE id = %s",
                (status, assistant_message, run_id),
            )
            connection.execute(
                """
                UPDATE ai_assistant_tool_calls
                SET status = %s, result_summary = %s, result_refs = %s, updated_at = now()
                WHERE run_id = %s AND tool_name = %s
                """,
                (
                    tool_call["status"],
                    tool_call["result_summary"],
                    json.dumps(tool_call.get("result_refs", []), sort_keys=True),
                    run_id,
                    tool_call["tool_name"],
                ),
            )
        return self.get_run(run_id, actor_username)

    def mark_run_failed(self, run_id: int, actor_username: str, result_summary: str) -> dict[str, object]:
        self.get_run(run_id, actor_username)
        connection = self._connect()
        with connection.transaction():
            connection.execute(
                "UPDATE ai_assistant_runs SET status = %s, assistant_message = %s, updated_at = now() WHERE id = %s",
                ("failed", "Assistant tool request failed.", run_id),
            )
            connection.execute(
                """
                UPDATE ai_assistant_tool_calls
                SET status = %s, result_summary = %s, updated_at = now()
                WHERE run_id = %s AND status = %s
                """,
                ("failed", result_summary, run_id, "executing"),
            )
        return self.get_run(run_id, actor_username)

    def _insert_tool_call(self, run_id: int, tool_call: dict[str, object]) -> None:
        self._connect().execute(
            """
            INSERT INTO ai_assistant_tool_calls (
                run_id, tool_name, policy, status, arguments, result_summary, result_refs
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                tool_call["tool_name"],
                tool_call["policy"],
                tool_call["status"],
                json.dumps(tool_call.get("arguments", {}), sort_keys=True),
                tool_call["result_summary"],
                json.dumps(tool_call.get("result_refs", []), sort_keys=True),
            ),
        )

    def _row_to_run(self, row: dict[str, Any]) -> dict[str, object]:
        tool_rows = self._connect().execute(
            """
            SELECT *
            FROM ai_assistant_tool_calls
            WHERE run_id = %s
            ORDER BY id
            """,
            (row["id"],),
        ).fetchall()
        return {
            "run_id": row["id"],
            "actor_username": row["actor_username"],
            "safe_message": row["safe_message"],
            "status": row["status"],
            "assistant_message": row["assistant_message"],
            "tool_calls": [self._row_to_tool_call(tool_row) for tool_row in tool_rows],
            "created_at": self._format_timestamp(row["created_at"]),
            "updated_at": self._format_timestamp(row["updated_at"]),
        }

    def _row_to_tool_call(self, row: dict[str, Any]) -> dict[str, object]:
        arguments = row["arguments"]
        result_refs = row["result_refs"]
        return {
            "tool_call_id": row["id"],
            "tool_name": row["tool_name"],
            "policy": row["policy"],
            "status": row["status"],
            "arguments": arguments if isinstance(arguments, dict) else json.loads(arguments),
            "result_summary": row["result_summary"],
            "result_refs": result_refs if isinstance(result_refs, list) else json.loads(result_refs),
            "created_at": self._format_timestamp(row["created_at"]),
            "updated_at": self._format_timestamp(row["updated_at"]),
        }

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection

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


def create_ai_assistant_history_repository(
    settings: Any,
    initialize: bool = True,
) -> SqliteAiAssistantHistoryRepository | PostgresAiAssistantHistoryRepository:
    database_url = settings.database_url.strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresAiAssistantHistoryRepository(database_url, initialize=initialize)
    if database_url.startswith("sqlite:///"):
        return SqliteAiAssistantHistoryRepository(database_url.removeprefix("sqlite:///"))
    if database_url == "sqlite:///:memory:":
        return SqliteAiAssistantHistoryRepository.in_memory()
    if not database_url:
        return SqliteAiAssistantHistoryRepository(settings.ai_sqlite_path)
    raise ValueError(f"Unsupported SERVICEOPS_DATABASE_URL: {database_url}")
