from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row

from serviceops_api.staff_management.models import CreateStaffAccountPayload, StaffRoleValue


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
SERVICE_REQUEST_MIGRATION_PATH = MIGRATIONS_DIR / "0001_service_request_intake.sql"
KNOWLEDGE_BASE_MIGRATION_PATH = MIGRATIONS_DIR / "0002_knowledge_base_rag.sql"
AI_SUGGESTIONS_MIGRATION_PATH = MIGRATIONS_DIR / "0003_ai_suggestions.sql"
TECHNICIAN_INVENTORY_MIGRATION_PATH = MIGRATIONS_DIR / "0004_technician_inventory.sql"
STAFF_MANAGEMENT_MIGRATION_PATH = MIGRATIONS_DIR / "0005_staff_management.sql"


class StaffAccountStore(Protocol):
    def create_account(self, payload: CreateStaffAccountPayload, password_hash: str, actor: str) -> dict[str, object]:
        """Create a staff account with roles."""

    def list_accounts(self) -> list[dict[str, object]]:
        """List staff accounts."""

    def get_account_by_username(self, username: str) -> dict[str, object] | None:
        """Return an account including password_hash, or None."""

    def update_roles(self, username: str, roles: list[StaffRoleValue], actor: str) -> dict[str, object]:
        """Replace account roles."""

    def set_active(self, username: str, active: bool, actor: str) -> dict[str, object]:
        """Activate or deactivate an account."""

    def reset_password(self, username: str, password_hash: str, actor: str) -> dict[str, object]:
        """Replace the password hash."""

    def list_audit_events(self) -> list[dict[str, object]]:
        """List staff audit events newest first."""

    def record_audit_event(self, actor: str, target: str, action: str, metadata: dict[str, object]) -> None:
        """Record an operational audit event."""

    def count_active_admins(self) -> int:
        """Count active admin users."""


class SqliteStaffAccountRepository:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    @classmethod
    def in_memory(cls) -> "SqliteStaffAccountRepository":
        return cls(":memory:")

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS staff_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS staff_account_roles (
                staff_account_id INTEGER NOT NULL REFERENCES staff_accounts(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (staff_account_id, role)
            );

            CREATE TABLE IF NOT EXISTS staff_audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_username TEXT NOT NULL,
                target_username TEXT NOT NULL,
                action TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

    def create_account(self, payload: CreateStaffAccountPayload, password_hash: str, actor: str) -> dict[str, object]:
        try:
            with self._connection:
                cursor = self._connection.execute(
                    """
                    INSERT INTO staff_accounts (username, display_name, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (payload.username, payload.display_name, password_hash),
                )
                account_id = int(cursor.lastrowid)
                self._replace_roles(account_id, payload.roles)
                self._insert_audit(actor, payload.username, "staff.created", {"roles": payload.roles})
        except sqlite3.IntegrityError as exc:
            raise ValueError("Staff account username already exists") from exc
        account = self.get_account_by_username(payload.username)
        if account is None:
            raise RuntimeError("staff account was not persisted")
        return account

    def list_accounts(self) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT id, username, display_name, password_hash, active, created_at, updated_at
            FROM staff_accounts
            ORDER BY username
            """
        ).fetchall()
        return [self._account_row(row) for row in rows]

    def get_account_by_username(self, username: str) -> dict[str, object] | None:
        row = self._connection.execute(
            """
            SELECT id, username, display_name, password_hash, active, created_at, updated_at
            FROM staff_accounts
            WHERE username = ?
            """,
            (username,),
        ).fetchone()
        if row is None:
            return None
        return self._account_row(row)

    def update_roles(self, username: str, roles: list[StaffRoleValue], actor: str) -> dict[str, object]:
        account = self._require_account(username)
        if "admin" in account["roles"] and "admin" not in roles and bool(account["active"]) and self.count_active_admins() <= 1:
            raise ValueError("Cannot remove the last active admin")
        with self._connection:
            self._replace_roles(int(account["id"]), roles)
            self._connection.execute("UPDATE staff_accounts SET updated_at = CURRENT_TIMESTAMP WHERE username = ?", (username,))
            self._insert_audit(actor, username, "staff.roles_updated", {"roles": roles})
        return self._require_account(username)

    def set_active(self, username: str, active: bool, actor: str) -> dict[str, object]:
        account = self._require_account(username)
        if not active and "admin" in account["roles"] and int(account["active"]) and self.count_active_admins() <= 1:
            raise ValueError("Cannot deactivate the last active admin")
        with self._connection:
            self._connection.execute(
                "UPDATE staff_accounts SET active = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
                (1 if active else 0, username),
            )
            self._insert_audit(actor, username, "staff.activated" if active else "staff.deactivated", {})
        return self._require_account(username)

    def reset_password(self, username: str, password_hash: str, actor: str) -> dict[str, object]:
        self._require_account(username)
        with self._connection:
            self._connection.execute(
                "UPDATE staff_accounts SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
                (password_hash, username),
            )
            self._insert_audit(actor, username, "staff.password_reset", {})
        return self._require_account(username)

    def list_audit_events(self) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT actor_username, target_username, action, metadata, created_at
            FROM staff_audit_events
            ORDER BY id DESC
            """
        ).fetchall()
        return [self._audit_row(row) for row in rows]

    def record_audit_event(self, actor: str, target: str, action: str, metadata: dict[str, object]) -> None:
        with self._connection:
            self._insert_audit(actor, target, action, metadata)

    def count_active_admins(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM staff_accounts sa
            JOIN staff_account_roles sar ON sar.staff_account_id = sa.id
            WHERE sa.active = 1 AND sar.role = 'admin'
            """
        ).fetchone()
        return int(row["count"])

    def _require_account(self, username: str) -> dict[str, object]:
        account = self.get_account_by_username(username)
        if account is None:
            raise KeyError(username)
        return account

    def _replace_roles(self, account_id: int, roles: list[StaffRoleValue]) -> None:
        self._connection.execute("DELETE FROM staff_account_roles WHERE staff_account_id = ?", (account_id,))
        self._connection.executemany(
            "INSERT INTO staff_account_roles (staff_account_id, role) VALUES (?, ?)",
            [(account_id, role) for role in sorted(roles)],
        )

    def _insert_audit(self, actor: str, target: str, action: str, metadata: dict[str, object]) -> None:
        self._connection.execute(
            """
            INSERT INTO staff_audit_events (actor_username, target_username, action, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (actor, target, action, json.dumps(metadata, separators=(",", ":"), sort_keys=True)),
        )

    def _account_row(self, row: sqlite3.Row) -> dict[str, object]:
        role_rows = self._connection.execute(
            """
            SELECT role FROM staff_account_roles
            WHERE staff_account_id = ?
            ORDER BY role
            """,
            (row["id"],),
        ).fetchall()
        return {
            "id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"],
            "password_hash": row["password_hash"],
            "roles": [role["role"] for role in role_rows],
            "active": bool(row["active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _audit_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "actor_username": row["actor_username"],
            "target_username": row["target_username"],
            "action": row["action"],
            "metadata": json.loads(row["metadata"]),
            "created_at": row["created_at"],
        }


class PostgresStaffAccountRepository:
    def __init__(self, database_url: str, initialize: bool = True) -> None:
        self._database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connection: psycopg.Connection[dict[str, Any]] | None = None
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        connection = self._connect()
        for migration_path in (
            SERVICE_REQUEST_MIGRATION_PATH,
            KNOWLEDGE_BASE_MIGRATION_PATH,
            AI_SUGGESTIONS_MIGRATION_PATH,
            TECHNICIAN_INVENTORY_MIGRATION_PATH,
            STAFF_MANAGEMENT_MIGRATION_PATH,
        ):
            connection.execute(migration_path.read_text(encoding="utf-8"))
        connection.commit()

    def create_account(self, payload: CreateStaffAccountPayload, password_hash: str, actor: str) -> dict[str, object]:
        connection = self._connect()
        try:
            with connection.transaction():
                row = connection.execute(
                    """
                    INSERT INTO staff_accounts (username, display_name, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (payload.username, payload.display_name, password_hash),
                ).fetchone()
                if row is None:
                    raise RuntimeError("staff account insert did not return an id")
                self._replace_roles(int(row["id"]), payload.roles)
                self._insert_audit(actor, payload.username, "staff.created", {"roles": payload.roles})
        except psycopg.errors.UniqueViolation as exc:
            raise ValueError("Staff account username already exists") from exc
        return self._require_account(payload.username)

    def list_accounts(self) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT id, username, display_name, password_hash, active, created_at, updated_at
            FROM staff_accounts
            ORDER BY username
            """
        ).fetchall()
        return [self._account_row(row) for row in rows]

    def get_account_by_username(self, username: str) -> dict[str, object] | None:
        row = self._connect().execute(
            """
            SELECT id, username, display_name, password_hash, active, created_at, updated_at
            FROM staff_accounts
            WHERE username = %s
            """,
            (username,),
        ).fetchone()
        if row is None:
            return None
        return self._account_row(row)

    def update_roles(self, username: str, roles: list[StaffRoleValue], actor: str) -> dict[str, object]:
        account = self._require_account(username)
        if "admin" in account["roles"] and "admin" not in roles and bool(account["active"]) and self.count_active_admins() <= 1:
            raise ValueError("Cannot remove the last active admin")
        connection = self._connect()
        with connection.transaction():
            self._replace_roles(int(account["id"]), roles)
            connection.execute("UPDATE staff_accounts SET updated_at = now() WHERE username = %s", (username,))
            self._insert_audit(actor, username, "staff.roles_updated", {"roles": roles})
        return self._require_account(username)

    def set_active(self, username: str, active: bool, actor: str) -> dict[str, object]:
        account = self._require_account(username)
        if not active and "admin" in account["roles"] and bool(account["active"]) and self.count_active_admins() <= 1:
            raise ValueError("Cannot deactivate the last active admin")
        connection = self._connect()
        with connection.transaction():
            connection.execute(
                "UPDATE staff_accounts SET active = %s, updated_at = now() WHERE username = %s",
                (active, username),
            )
            self._insert_audit(actor, username, "staff.activated" if active else "staff.deactivated", {})
        return self._require_account(username)

    def reset_password(self, username: str, password_hash: str, actor: str) -> dict[str, object]:
        self._require_account(username)
        connection = self._connect()
        with connection.transaction():
            connection.execute(
                "UPDATE staff_accounts SET password_hash = %s, updated_at = now() WHERE username = %s",
                (password_hash, username),
            )
            self._insert_audit(actor, username, "staff.password_reset", {})
        return self._require_account(username)

    def list_audit_events(self) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT actor_username, target_username, action, metadata, created_at
            FROM staff_audit_events
            ORDER BY id DESC
            """
        ).fetchall()
        return [self._audit_row(row) for row in rows]

    def record_audit_event(self, actor: str, target: str, action: str, metadata: dict[str, object]) -> None:
        self._insert_audit(actor, target, action, metadata)

    def count_active_admins(self) -> int:
        row = self._connect().execute(
            """
            SELECT COUNT(*) AS count
            FROM staff_accounts sa
            JOIN staff_account_roles sar ON sar.staff_account_id = sa.id
            WHERE sa.active = true AND sar.role = 'admin'
            """
        ).fetchone()
        return 0 if row is None else int(row["count"])

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection

    def _require_account(self, username: str) -> dict[str, object]:
        account = self.get_account_by_username(username)
        if account is None:
            raise KeyError(username)
        return account

    def _replace_roles(self, account_id: int, roles: list[StaffRoleValue]) -> None:
        connection = self._connect()
        connection.execute("DELETE FROM staff_account_roles WHERE staff_account_id = %s", (account_id,))
        for role in sorted(roles):
            connection.execute(
                "INSERT INTO staff_account_roles (staff_account_id, role) VALUES (%s, %s)",
                (account_id, role),
            )

    def _insert_audit(self, actor: str, target: str, action: str, metadata: dict[str, object]) -> None:
        self._connect().execute(
            """
            INSERT INTO staff_audit_events (actor_username, target_username, action, metadata)
            VALUES (%s, %s, %s, %s)
            """,
            (actor, target, action, json.dumps(metadata, separators=(",", ":"), sort_keys=True)),
        )

    def _account_row(self, row: dict[str, Any]) -> dict[str, object]:
        role_rows = self._connect().execute(
            "SELECT role FROM staff_account_roles WHERE staff_account_id = %s ORDER BY role",
            (row["id"],),
        ).fetchall()
        return {
            "id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"],
            "password_hash": row["password_hash"],
            "roles": [role["role"] for role in role_rows],
            "active": row["active"],
            "created_at": self._format_timestamp(row["created_at"]),
            "updated_at": self._format_timestamp(row["updated_at"]),
        }

    def _audit_row(self, row: dict[str, Any]) -> dict[str, object]:
        metadata = row["metadata"]
        return {
            "actor_username": row["actor_username"],
            "target_username": row["target_username"],
            "action": row["action"],
            "metadata": json.loads(metadata) if isinstance(metadata, str) else metadata,
            "created_at": self._format_timestamp(row["created_at"]),
        }

    def _format_timestamp(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)


def create_staff_account_repository(
    settings: Any,
    initialize: bool = True,
) -> SqliteStaffAccountRepository | PostgresStaffAccountRepository:
    database_url = settings.database_url.strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresStaffAccountRepository(database_url, initialize=initialize)
    if database_url.startswith("sqlite:///"):
        return SqliteStaffAccountRepository(database_url.removeprefix("sqlite:///"))
    if database_url == "sqlite:///:memory:":
        return SqliteStaffAccountRepository.in_memory()
    if not database_url:
        return SqliteStaffAccountRepository(".local/serviceops-staff.sqlite3")
    raise ValueError(f"Unsupported SERVICEOPS_DATABASE_URL: {database_url}")
