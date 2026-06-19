from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
SERVICE_REQUEST_MIGRATION_PATH = MIGRATIONS_DIR / "0001_service_request_intake.sql"
STAFF_MANAGEMENT_MIGRATION_PATH = MIGRATIONS_DIR / "0005_staff_management.sql"
STAFF_PROFILE_FIELDS_MIGRATION_PATH = MIGRATIONS_DIR / "0012_staff_profile_fields.sql"
TECHNICIAN_PROFILE_MIGRATION_PATH = MIGRATIONS_DIR / "0014_technician_profiles.sql"


class TechnicianProfileStore(Protocol):
    def list_profiles(self) -> list[dict[str, object]]:
        """Return technician profiles keyed by staff username."""

    def get_profile(self, staff_username: str) -> dict[str, object] | None:
        """Return one technician profile, or None when it has not been configured."""

    def upsert_profile(
        self,
        staff_username: str,
        *,
        active: bool,
        skill_brands: list[str],
        service_regions: list[str],
        notes: str | None,
    ) -> dict[str, object]:
        """Create or update one technician profile."""


class SqliteTechnicianProfileRepository:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    @classmethod
    def in_memory(cls) -> "SqliteTechnicianProfileRepository":
        return cls(":memory:")

    def initialize(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS technician_profiles (
                    staff_username TEXT PRIMARY KEY,
                    active INTEGER NOT NULL DEFAULT 1,
                    skill_brands TEXT NOT NULL DEFAULT '[]',
                    service_regions TEXT NOT NULL DEFAULT '[]',
                    notes TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_technician_profiles_active
                    ON technician_profiles (active);
                """
            )

    def list_profiles(self) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT staff_username, active, skill_brands, service_regions, notes, created_at, updated_at
            FROM technician_profiles
            ORDER BY staff_username
            """
        ).fetchall()
        return [self._profile_row(row) for row in rows]

    def get_profile(self, staff_username: str) -> dict[str, object] | None:
        row = self._connection.execute(
            """
            SELECT staff_username, active, skill_brands, service_regions, notes, created_at, updated_at
            FROM technician_profiles
            WHERE staff_username = ?
            """,
            (staff_username,),
        ).fetchone()
        return None if row is None else self._profile_row(row)

    def upsert_profile(
        self,
        staff_username: str,
        *,
        active: bool,
        skill_brands: list[str],
        service_regions: list[str],
        notes: str | None,
    ) -> dict[str, object]:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO technician_profiles (
                    staff_username, active, skill_brands, service_regions, notes
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(staff_username) DO UPDATE SET
                    active = excluded.active,
                    skill_brands = excluded.skill_brands,
                    service_regions = excluded.service_regions,
                    notes = excluded.notes,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    staff_username,
                    1 if active else 0,
                    json.dumps(skill_brands, ensure_ascii=False, separators=(",", ":")),
                    json.dumps(service_regions, ensure_ascii=False, separators=(",", ":")),
                    notes,
                ),
            )
        profile = self.get_profile(staff_username)
        if profile is None:
            raise RuntimeError("technician profile was not persisted")
        return profile

    def _profile_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "staff_username": row["staff_username"],
            "active": bool(row["active"]),
            "skill_brands": json.loads(row["skill_brands"]),
            "service_regions": json.loads(row["service_regions"]),
            "notes": row["notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


class PostgresTechnicianProfileRepository:
    def __init__(self, database_url: str, initialize: bool = True) -> None:
        self._database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connection: psycopg.Connection[dict[str, Any]] | None = None
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        connection = self._connect()
        for migration_path in (
            SERVICE_REQUEST_MIGRATION_PATH,
            STAFF_MANAGEMENT_MIGRATION_PATH,
            STAFF_PROFILE_FIELDS_MIGRATION_PATH,
            TECHNICIAN_PROFILE_MIGRATION_PATH,
        ):
            connection.execute(migration_path.read_text(encoding="utf-8"))
        connection.commit()

    def list_profiles(self) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT staff_username, active, skill_brands, service_regions, notes, created_at, updated_at
            FROM technician_profiles
            ORDER BY staff_username
            """
        ).fetchall()
        return [self._profile_row(row) for row in rows]

    def get_profile(self, staff_username: str) -> dict[str, object] | None:
        row = self._connect().execute(
            """
            SELECT staff_username, active, skill_brands, service_regions, notes, created_at, updated_at
            FROM technician_profiles
            WHERE staff_username = %s
            """,
            (staff_username,),
        ).fetchone()
        return None if row is None else self._profile_row(row)

    def upsert_profile(
        self,
        staff_username: str,
        *,
        active: bool,
        skill_brands: list[str],
        service_regions: list[str],
        notes: str | None,
    ) -> dict[str, object]:
        self._connect().execute(
            """
            INSERT INTO technician_profiles (
                staff_username, active, skill_brands, service_regions, notes
            )
            VALUES (%s, %s, %s::jsonb, %s::jsonb, %s)
            ON CONFLICT (staff_username) DO UPDATE SET
                active = excluded.active,
                skill_brands = excluded.skill_brands,
                service_regions = excluded.service_regions,
                notes = excluded.notes,
                updated_at = now()
            """,
            (
                staff_username,
                active,
                json.dumps(skill_brands, ensure_ascii=False, separators=(",", ":")),
                json.dumps(service_regions, ensure_ascii=False, separators=(",", ":")),
                notes,
            ),
        )
        self._connect().commit()
        profile = self.get_profile(staff_username)
        if profile is None:
            raise RuntimeError("technician profile was not persisted")
        return profile

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection

    def _profile_row(self, row: dict[str, Any]) -> dict[str, object]:
        return {
            "staff_username": row["staff_username"],
            "active": bool(row["active"]),
            "skill_brands": _json_list(row["skill_brands"]),
            "service_regions": _json_list(row["service_regions"]),
            "notes": row["notes"],
            "created_at": _format_timestamp(row["created_at"]),
            "updated_at": _format_timestamp(row["updated_at"]),
        }


def _json_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return list(json.loads(value))
    return list(value or [])


def _format_timestamp(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def create_technician_profile_repository(
    settings: Any,
    initialize: bool = True,
) -> SqliteTechnicianProfileRepository | PostgresTechnicianProfileRepository:
    database_url = settings.database_url.strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresTechnicianProfileRepository(database_url, initialize=initialize)
    if database_url.startswith("sqlite:///"):
        return SqliteTechnicianProfileRepository(database_url.removeprefix("sqlite:///"))
    if database_url == "sqlite:///:memory:":
        return SqliteTechnicianProfileRepository.in_memory()
    if not database_url:
        return SqliteTechnicianProfileRepository(".local/serviceops-technician-profiles.sqlite3")
    raise ValueError(f"Unsupported SERVICEOPS_DATABASE_URL: {database_url}")
