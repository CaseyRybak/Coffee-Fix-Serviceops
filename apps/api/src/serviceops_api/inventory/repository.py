from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row

from serviceops_api.inventory.models import CreatePartPayload


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
SERVICE_REQUEST_MIGRATION_PATH = MIGRATIONS_DIR / "0001_service_request_intake.sql"
KNOWLEDGE_BASE_MIGRATION_PATH = MIGRATIONS_DIR / "0002_knowledge_base_rag.sql"
AI_SUGGESTIONS_MIGRATION_PATH = MIGRATIONS_DIR / "0003_ai_suggestions.sql"
TECHNICIAN_INVENTORY_MIGRATION_PATH = MIGRATIONS_DIR / "0004_technician_inventory.sql"


class InsufficientStockError(ValueError):
    """Raised when a parts usage request exceeds available stock."""


class InventoryStore(Protocol):
    def create_part(self, payload: CreatePartPayload) -> dict[str, object]:
        """Persist a catalog part."""

    def list_parts(self) -> list[dict[str, object]]:
        """Return catalog parts with stock counts."""

    def set_stock_count(self, part_id: int, quantity_on_hand: int) -> dict[str, object]:
        """Set the current stock count for a part."""

    def get_stock_count(self, part_id: int) -> dict[str, object]:
        """Return the current stock count for a part."""

    def record_parts_used(
        self,
        request_number: str,
        part_id: int,
        quantity: int,
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        """Record parts used and decrement stock."""

    def list_parts_used(self, request_number: str) -> list[dict[str, object]]:
        """Return parts used for a request."""


class SqliteInventoryRepository:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    @classmethod
    def in_memory(cls) -> "SqliteInventoryRepository":
        return cls(":memory:")

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS parts_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                brand TEXT,
                model TEXT,
                unit TEXT NOT NULL,
                compatibility_note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS stock_counts (
                part_id INTEGER PRIMARY KEY REFERENCES parts_catalog(id),
                quantity_on_hand INTEGER NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS request_parts_used (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT NOT NULL,
                part_id INTEGER NOT NULL REFERENCES parts_catalog(id),
                quantity INTEGER NOT NULL,
                stock_after_use INTEGER NOT NULL,
                note TEXT,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self._ensure_sqlite_parts_used_columns()

    def _ensure_sqlite_parts_used_columns(self) -> None:
        existing_columns = {
            str(row["name"])
            for row in self._connection.execute("PRAGMA table_info(request_parts_used)").fetchall()
        }
        if "stock_after_use" not in existing_columns:
            self._connection.execute(
                "ALTER TABLE request_parts_used ADD COLUMN stock_after_use INTEGER NOT NULL DEFAULT 0"
            )

    def create_part(self, payload: CreatePartPayload) -> dict[str, object]:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO parts_catalog (sku, name, brand, model, unit, compatibility_note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (payload.sku, payload.name, payload.brand, payload.model, payload.unit, payload.compatibility_note),
            )
        return self._get_part(int(cursor.lastrowid))

    def list_parts(self) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT
                pc.id,
                pc.sku,
                pc.name,
                pc.brand,
                pc.model,
                pc.unit,
                pc.compatibility_note,
                pc.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand,
                sc.updated_at AS stock_updated_at
            FROM parts_catalog pc
            LEFT JOIN stock_counts sc ON sc.part_id = pc.id
            ORDER BY pc.name, pc.id
            """
        ).fetchall()
        return [self._part_row(row) for row in rows]

    def set_stock_count(self, part_id: int, quantity_on_hand: int) -> dict[str, object]:
        self._get_part(part_id)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO stock_counts (part_id, quantity_on_hand, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(part_id) DO UPDATE SET
                    quantity_on_hand = excluded.quantity_on_hand,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (part_id, quantity_on_hand),
            )
        return self.get_stock_count(part_id)

    def get_stock_count(self, part_id: int) -> dict[str, object]:
        self._get_part(part_id)
        row = self._connection.execute(
            """
            SELECT part_id, quantity_on_hand, updated_at
            FROM stock_counts
            WHERE part_id = ?
            """,
            (part_id,),
        ).fetchone()
        if row is None:
            return {"part_id": part_id, "quantity_on_hand": 0, "updated_at": ""}
        return {"part_id": row["part_id"], "quantity_on_hand": row["quantity_on_hand"], "updated_at": row["updated_at"]}

    def record_parts_used(
        self,
        request_number: str,
        part_id: int,
        quantity: int,
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        part = self._get_part(part_id)
        stock = self.get_stock_count(part_id)
        current_quantity = int(stock["quantity_on_hand"])
        if current_quantity < quantity:
            raise InsufficientStockError("Insufficient stock for requested parts usage")
        stock_after_use = current_quantity - quantity
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO request_parts_used (request_number, part_id, quantity, stock_after_use, note, actor)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (request_number, part_id, quantity, stock_after_use, note, actor),
            )
            self._connection.execute(
                """
                INSERT INTO stock_counts (part_id, quantity_on_hand, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(part_id) DO UPDATE SET
                    quantity_on_hand = excluded.quantity_on_hand,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (part_id, stock_after_use),
            )
        return {
            **part,
            "part_name": part["name"],
            "request_number": request_number,
            "quantity": quantity,
            "note": note,
            "actor": actor,
            "quantity_on_hand": stock_after_use,
            "stock_after_use": stock_after_use,
            "created_at": self._latest_usage_created_at(request_number, part_id),
        }

    def list_parts_used(self, request_number: str) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT
                rpu.request_number,
                rpu.part_id,
                pc.sku,
                pc.name AS part_name,
                pc.unit,
                rpu.quantity,
                rpu.stock_after_use,
                rpu.note,
                rpu.actor,
                rpu.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand
            FROM request_parts_used rpu
            JOIN parts_catalog pc ON pc.id = rpu.part_id
            LEFT JOIN stock_counts sc ON sc.part_id = rpu.part_id
            WHERE rpu.request_number = ?
            ORDER BY rpu.id DESC
            """,
            (request_number,),
        ).fetchall()
        return [self._parts_used_row(row) for row in rows]

    def _get_part(self, part_id: int) -> dict[str, object]:
        row = self._connection.execute(
            """
            SELECT
                pc.id,
                pc.sku,
                pc.name,
                pc.brand,
                pc.model,
                pc.unit,
                pc.compatibility_note,
                pc.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand,
                sc.updated_at AS stock_updated_at
            FROM parts_catalog pc
            LEFT JOIN stock_counts sc ON sc.part_id = pc.id
            WHERE pc.id = ?
            """,
            (part_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(part_id))
        return self._part_row(row)

    def _part_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "part_id": row["id"],
            "sku": row["sku"],
            "name": row["name"],
            "brand": row["brand"],
            "model": row["model"],
            "unit": row["unit"],
            "compatibility_note": row["compatibility_note"],
            "created_at": row["created_at"],
            "quantity_on_hand": row["quantity_on_hand"],
            "stock_updated_at": row["stock_updated_at"],
        }

    def _parts_used_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "request_number": row["request_number"],
            "part_id": row["part_id"],
            "sku": row["sku"],
            "part_name": row["part_name"],
            "quantity": row["quantity"],
            "unit": row["unit"],
            "note": row["note"],
            "quantity_on_hand": row["quantity_on_hand"],
            "stock_after_use": row["stock_after_use"],
            "actor": row["actor"],
            "created_at": row["created_at"],
        }

    def _latest_usage_created_at(self, request_number: str, part_id: int) -> str:
        row = self._connection.execute(
            """
            SELECT created_at
            FROM request_parts_used
            WHERE request_number = ? AND part_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (request_number, part_id),
        ).fetchone()
        return "" if row is None else str(row["created_at"])


class PostgresInventoryRepository:
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
        ):
            connection.execute(migration_path.read_text(encoding="utf-8"))
        connection.commit()

    def create_part(self, payload: CreatePartPayload) -> dict[str, object]:
        row = self._connect().execute(
            """
            INSERT INTO parts_catalog (sku, name, brand, model, unit, compatibility_note)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (payload.sku, payload.name, payload.brand, payload.model, payload.unit, payload.compatibility_note),
        ).fetchone()
        if row is None:
            raise RuntimeError("part insert did not return an id")
        self._connect().commit()
        return self._get_part(int(row["id"]))

    def list_parts(self) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT
                pc.id,
                pc.sku,
                pc.name,
                pc.brand,
                pc.model,
                pc.unit,
                pc.compatibility_note,
                pc.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand,
                sc.updated_at AS stock_updated_at
            FROM parts_catalog pc
            LEFT JOIN stock_counts sc ON sc.part_id = pc.id
            ORDER BY pc.name, pc.id
            """
        ).fetchall()
        return [self._part_row(row) for row in rows]

    def set_stock_count(self, part_id: int, quantity_on_hand: int) -> dict[str, object]:
        self._get_part(part_id)
        self._connect().execute(
            """
            INSERT INTO stock_counts (part_id, quantity_on_hand, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT(part_id) DO UPDATE SET
                quantity_on_hand = excluded.quantity_on_hand,
                updated_at = now()
            """,
            (part_id, quantity_on_hand),
        )
        self._connect().commit()
        return self.get_stock_count(part_id)

    def get_stock_count(self, part_id: int) -> dict[str, object]:
        self._get_part(part_id)
        row = self._connect().execute(
            "SELECT part_id, quantity_on_hand, updated_at FROM stock_counts WHERE part_id = %s",
            (part_id,),
        ).fetchone()
        if row is None:
            return {"part_id": part_id, "quantity_on_hand": 0, "updated_at": ""}
        return {
            "part_id": row["part_id"],
            "quantity_on_hand": row["quantity_on_hand"],
            "updated_at": self._format_timestamp(row["updated_at"]),
        }

    def record_parts_used(
        self,
        request_number: str,
        part_id: int,
        quantity: int,
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        part = self._get_part(part_id)
        stock = self.get_stock_count(part_id)
        current_quantity = int(stock["quantity_on_hand"])
        if current_quantity < quantity:
            raise InsufficientStockError("Insufficient stock for requested parts usage")
        stock_after_use = current_quantity - quantity
        connection = self._connect()
        with connection.transaction():
            row = connection.execute(
                """
                INSERT INTO request_parts_used (request_number, part_id, quantity, stock_after_use, note, actor)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING created_at
                """,
                (request_number, part_id, quantity, stock_after_use, note, actor),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO stock_counts (part_id, quantity_on_hand, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT(part_id) DO UPDATE SET
                    quantity_on_hand = excluded.quantity_on_hand,
                    updated_at = now()
                """,
                (part_id, stock_after_use),
            )
        return {
            **part,
            "part_name": part["name"],
            "request_number": request_number,
            "quantity": quantity,
            "note": note,
            "actor": actor,
            "quantity_on_hand": stock_after_use,
            "stock_after_use": stock_after_use,
            "created_at": "" if row is None else self._format_timestamp(row["created_at"]),
        }

    def list_parts_used(self, request_number: str) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT
                rpu.request_number,
                rpu.part_id,
                pc.sku,
                pc.name AS part_name,
                pc.unit,
                rpu.quantity,
                rpu.stock_after_use,
                rpu.note,
                rpu.actor,
                rpu.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand
            FROM request_parts_used rpu
            JOIN parts_catalog pc ON pc.id = rpu.part_id
            LEFT JOIN stock_counts sc ON sc.part_id = rpu.part_id
            WHERE rpu.request_number = %s
            ORDER BY rpu.id DESC
            """,
            (request_number,),
        ).fetchall()
        return [self._parts_used_row(row) for row in rows]

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection

    def _get_part(self, part_id: int) -> dict[str, object]:
        row = self._connect().execute(
            """
            SELECT
                pc.id,
                pc.sku,
                pc.name,
                pc.brand,
                pc.model,
                pc.unit,
                pc.compatibility_note,
                pc.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand,
                sc.updated_at AS stock_updated_at
            FROM parts_catalog pc
            LEFT JOIN stock_counts sc ON sc.part_id = pc.id
            WHERE pc.id = %s
            """,
            (part_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(part_id))
        return self._part_row(row)

    def _part_row(self, row: dict[str, Any]) -> dict[str, object]:
        return {
            "part_id": row["id"],
            "sku": row["sku"],
            "name": row["name"],
            "brand": row["brand"],
            "model": row["model"],
            "unit": row["unit"],
            "compatibility_note": row["compatibility_note"],
            "created_at": self._format_timestamp(row["created_at"]),
            "quantity_on_hand": row["quantity_on_hand"],
            "stock_updated_at": None if row["stock_updated_at"] is None else self._format_timestamp(row["stock_updated_at"]),
        }

    def _parts_used_row(self, row: dict[str, Any]) -> dict[str, object]:
        return {
            "request_number": row["request_number"],
            "part_id": row["part_id"],
            "sku": row["sku"],
            "part_name": row["part_name"],
            "quantity": row["quantity"],
            "unit": row["unit"],
            "note": row["note"],
            "quantity_on_hand": row["quantity_on_hand"],
            "stock_after_use": row["stock_after_use"],
            "actor": row["actor"],
            "created_at": self._format_timestamp(row["created_at"]),
        }

    def _format_timestamp(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)


def create_inventory_repository(settings: Any, initialize: bool = True) -> SqliteInventoryRepository | PostgresInventoryRepository:
    database_url = settings.database_url.strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresInventoryRepository(database_url, initialize=initialize)
    if database_url.startswith("sqlite:///"):
        return SqliteInventoryRepository(database_url.removeprefix("sqlite:///"))
    if database_url == "sqlite:///:memory:":
        return SqliteInventoryRepository.in_memory()
    if not database_url:
        return SqliteInventoryRepository(".local/serviceops-inventory.sqlite3")
    raise ValueError(f"Unsupported SERVICEOPS_DATABASE_URL: {database_url}")
