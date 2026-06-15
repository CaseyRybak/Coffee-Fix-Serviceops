from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from serviceops_api.config import Settings
from serviceops_api.notifications.models import DeliveryResultPayload, NotificationEvent


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
NOTIFICATION_MIGRATION_PATH = MIGRATIONS_DIR / "0006_notification_delivery.sql"


class SqliteNotificationRepository:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    @classmethod
    def in_memory(cls) -> "SqliteNotificationRepository":
        return cls(":memory:")

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS notification_delivery_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                request_number TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                channel TEXT,
                provider_message_id TEXT,
                error TEXT,
                attempt_count INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_notification_delivery_request
                ON notification_delivery_attempts (request_number);
            CREATE INDEX IF NOT EXISTS idx_notification_delivery_status
                ON notification_delivery_attempts (status);
            """
        )

    def next_sequence(self, request_number: str) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM notification_delivery_attempts
            WHERE request_number = ?
            """,
            (request_number,),
        ).fetchone()
        return int(row["count"]) + 1

    def create_queued_attempt(self, event: NotificationEvent) -> bool:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT OR IGNORE INTO notification_delivery_attempts (
                    event_id, event_type, request_number, payload_json, status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.event_type,
                    event.request_number,
                    json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
                    "queued",
                ),
            )
        return cursor.rowcount == 1

    def record_delivery_result(
        self,
        event_id: str,
        status: str,
        channel: str | None = None,
        provider_message_id: str | None = None,
        error: str | None = None,
        attempt_count: int = 1,
    ) -> bool:
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE notification_delivery_attempts
                SET
                    status = ?,
                    channel = ?,
                    provider_message_id = ?,
                    error = ?,
                    attempt_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE event_id = ?
                """,
                (status, channel, provider_message_id, error, attempt_count, event_id),
            )
        return cursor.rowcount == 1

    def record_callback_result(self, payload: DeliveryResultPayload) -> bool:
        return self.record_delivery_result(
            event_id=payload.event_id,
            status=payload.status,
            channel=payload.channel,
            provider_message_id=payload.provider_message_id,
            error=payload.error,
            attempt_count=payload.attempt_count,
        )

    def list_for_request(self, request_number: str) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT
                event_id, event_type, request_number, status, channel, provider_message_id,
                error, attempt_count, created_at, updated_at
            FROM notification_delivery_attempts
            WHERE request_number = ?
            ORDER BY id DESC
            """,
            (request_number,),
        ).fetchall()
        return [dict(row) for row in rows]


class PostgresNotificationRepository:
    def __init__(self, database_url: str, initialize: bool = True) -> None:
        self._database_url = self._normalize_database_url(database_url)
        self._connection: psycopg.Connection[dict[str, Any]] | None = None
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        self._connect().execute(NOTIFICATION_MIGRATION_PATH.read_text(encoding="utf-8"))
        self._connect().commit()

    def next_sequence(self, request_number: str) -> int:
        row = self._connect().execute(
            """
            SELECT COUNT(*) AS count
            FROM notification_delivery_attempts
            WHERE request_number = %s
            """,
            (request_number,),
        ).fetchone()
        return 1 if row is None else int(row["count"]) + 1

    def create_queued_attempt(self, event: NotificationEvent) -> bool:
        row = self._connect().execute(
            """
            INSERT INTO notification_delivery_attempts (
                event_id, event_type, request_number, payload_json, status
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING
            RETURNING event_id
            """,
            (
                event.event_id,
                event.event_type,
                event.request_number,
                json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
                "queued",
            ),
        ).fetchone()
        self._connect().commit()
        return row is not None

    def record_delivery_result(
        self,
        event_id: str,
        status: str,
        channel: str | None = None,
        provider_message_id: str | None = None,
        error: str | None = None,
        attempt_count: int = 1,
    ) -> bool:
        cursor = self._connect().execute(
            """
            UPDATE notification_delivery_attempts
            SET
                status = %s,
                channel = %s,
                provider_message_id = %s,
                error = %s,
                attempt_count = %s,
                updated_at = now()
            WHERE event_id = %s
            """,
            (status, channel, provider_message_id, error, attempt_count, event_id),
        )
        self._connect().commit()
        return cursor.rowcount == 1

    def record_callback_result(self, payload: DeliveryResultPayload) -> bool:
        return self.record_delivery_result(
            event_id=payload.event_id,
            status=payload.status,
            channel=payload.channel,
            provider_message_id=payload.provider_message_id,
            error=payload.error,
            attempt_count=payload.attempt_count,
        )

    def list_for_request(self, request_number: str) -> list[dict[str, Any]]:
        rows = self._connect().execute(
            """
            SELECT
                event_id, event_type, request_number, status, channel, provider_message_id,
                error, attempt_count, created_at, updated_at
            FROM notification_delivery_attempts
            WHERE request_number = %s
            ORDER BY id DESC
            """,
            (request_number,),
        ).fetchall()
        return [
            {
                **row,
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection

    def _normalize_database_url(self, database_url: str) -> str:
        if database_url.startswith("postgresql+psycopg://"):
            return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        return database_url


NotificationRepository = SqliteNotificationRepository | PostgresNotificationRepository


def create_notification_repository(
    settings: Settings,
    initialize: bool = True,
) -> NotificationRepository:
    if settings.database_url.startswith("sqlite:///"):
        return SqliteNotificationRepository(settings.intake_sqlite_path)
    if settings.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresNotificationRepository(settings.database_url, initialize=initialize)
    raise ValueError(f"Unsupported SERVICEOPS_DATABASE_URL for notifications: {settings.database_url}")
