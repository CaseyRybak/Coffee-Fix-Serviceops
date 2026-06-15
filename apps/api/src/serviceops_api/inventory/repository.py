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
INVENTORY_RESERVATIONS_MIGRATION_PATH = MIGRATIONS_DIR / "0008_inventory_reservations.sql"
PART_COMPATIBILITY_MIGRATION_PATH = MIGRATIONS_DIR / "0009_part_compatibility.sql"
INVENTORY_RUSSIAN_CATALOG_MIGRATION_PATH = MIGRATIONS_DIR / "0010_inventory_russian_catalog.sql"


class InsufficientStockError(ValueError):
    """Raised when a parts usage request exceeds available stock."""


class DuplicatePartError(ValueError):
    """Raised when a new catalog part duplicates an existing factual part."""


class InventoryStore(Protocol):
    def create_part(self, payload: CreatePartPayload) -> dict[str, object]:
        """Persist a catalog part."""

    def list_parts(self) -> list[dict[str, object]]:
        """Return catalog parts with stock counts."""

    def set_stock_count(self, part_id: int, quantity_on_hand: int, low_stock_threshold: int | None = None) -> dict[str, object]:
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

    def reserve_part(
        self,
        request_number: str,
        part_id: int,
        quantity: int,
        appointment_id: int | None,
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        """Reserve stock for a service request."""

    def adjust_reservation(self, reservation_id: int, quantity: int, note: str | None, actor: str) -> dict[str, object]:
        """Adjust an active reservation."""

    def release_reservation(self, reservation_id: int, note: str | None, actor: str) -> dict[str, object]:
        """Release an active reservation."""

    def list_reservations(self, request_number: str | None = None) -> list[dict[str, object]]:
        """Return reservations."""

    def list_stock_movements(self, part_id: int | None = None, request_number: str | None = None) -> list[dict[str, object]]:
        """Return stock movement audit records."""

    def add_compatibility(self, part_id: int, payload: Any) -> dict[str, object]:
        """Add compatibility metadata for a part."""


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
                part_type TEXT,
                parameter_label TEXT,
                parameter_value TEXT,
                parameter_unit TEXT,
                factual_key TEXT UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS stock_counts (
                part_id INTEGER PRIMARY KEY REFERENCES parts_catalog(id),
                quantity_on_hand INTEGER NOT NULL,
                low_stock_threshold INTEGER,
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

            CREATE TABLE IF NOT EXISTS part_reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT NOT NULL,
                appointment_id INTEGER,
                part_id INTEGER NOT NULL REFERENCES parts_catalog(id),
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER NOT NULL REFERENCES parts_catalog(id),
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                quantity_on_hand_after INTEGER NOT NULL,
                reserved_quantity_after INTEGER NOT NULL,
                available_quantity_after INTEGER NOT NULL,
                request_number TEXT,
                reservation_id INTEGER REFERENCES part_reservations(id),
                note TEXT,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS part_compatibility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER NOT NULL REFERENCES parts_catalog(id),
                compatibility_level TEXT NOT NULL,
                brand TEXT,
                model TEXT,
                series TEXT,
                machine_family TEXT,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self._ensure_sqlite_parts_used_columns()
        self._ensure_sqlite_reservation_columns()
        self._ensure_sqlite_part_identity_columns()

    def _ensure_sqlite_parts_used_columns(self) -> None:
        existing_columns = {
            str(row["name"])
            for row in self._connection.execute("PRAGMA table_info(request_parts_used)").fetchall()
        }
        if "stock_after_use" not in existing_columns:
            self._connection.execute(
                "ALTER TABLE request_parts_used ADD COLUMN stock_after_use INTEGER NOT NULL DEFAULT 0"
            )

    def _ensure_sqlite_reservation_columns(self) -> None:
        stock_columns = {
            str(row["name"])
            for row in self._connection.execute("PRAGMA table_info(stock_counts)").fetchall()
        }
        if "low_stock_threshold" not in stock_columns:
            self._connection.execute("ALTER TABLE stock_counts ADD COLUMN low_stock_threshold INTEGER")

    def _ensure_sqlite_part_identity_columns(self) -> None:
        existing_columns = {
            str(row["name"])
            for row in self._connection.execute("PRAGMA table_info(parts_catalog)").fetchall()
        }
        for column in ("part_type", "parameter_label", "parameter_value", "parameter_unit", "factual_key"):
            if column not in existing_columns:
                self._connection.execute(f"ALTER TABLE parts_catalog ADD COLUMN {column} TEXT")
        self._connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_parts_catalog_factual_key ON parts_catalog (factual_key)"
        )

    def create_part(self, payload: CreatePartPayload) -> dict[str, object]:
        factual_key = self._factual_key(payload)
        if factual_key and self._part_exists_by_factual_key(factual_key):
            raise DuplicatePartError("Part with the same factual key already exists")
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO parts_catalog (
                    sku, name, brand, model, unit, compatibility_note,
                    part_type, parameter_label, parameter_value, parameter_unit, factual_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.sku,
                    payload.name,
                    payload.brand,
                    payload.model,
                    payload.unit,
                    payload.compatibility_note,
                    payload.part_type,
                    payload.parameter_label,
                    payload.parameter_value,
                    payload.parameter_unit,
                    factual_key,
                ),
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
                pc.part_type,
                pc.parameter_label,
                pc.parameter_value,
                pc.parameter_unit,
                pc.factual_key,
                pc.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand,
                COALESCE((
                    SELECT SUM(pr.quantity)
                    FROM part_reservations pr
                    WHERE pr.part_id = pc.id AND pr.status = 'active'
                ), 0) AS reserved_quantity,
                sc.low_stock_threshold,
                sc.updated_at AS stock_updated_at
            FROM parts_catalog pc
            LEFT JOIN stock_counts sc ON sc.part_id = pc.id
            ORDER BY pc.name, pc.id
            """
        ).fetchall()
        return [self._part_row(row) for row in rows]

    def set_stock_count(self, part_id: int, quantity_on_hand: int, low_stock_threshold: int | None = None) -> dict[str, object]:
        self._get_part(part_id)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO stock_counts (part_id, quantity_on_hand, low_stock_threshold, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(part_id) DO UPDATE SET
                    quantity_on_hand = excluded.quantity_on_hand,
                    low_stock_threshold = COALESCE(excluded.low_stock_threshold, stock_counts.low_stock_threshold),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (part_id, quantity_on_hand, low_stock_threshold),
            )
            self._insert_stock_movement(part_id, "manual_adjustment", quantity_on_hand, None, None, "inventory", None)
        return self.get_stock_count(part_id)

    def get_stock_count(self, part_id: int) -> dict[str, object]:
        self._get_part(part_id)
        row = self._connection.execute(
            """
            SELECT part_id, quantity_on_hand, low_stock_threshold, updated_at
            FROM stock_counts
            WHERE part_id = ?
            """,
            (part_id,),
        ).fetchone()
        if row is None:
            reserved = self._active_reserved_quantity(part_id)
            return {
                "part_id": part_id,
                "quantity_on_hand": 0,
                "reserved_quantity": reserved,
                "available_quantity": 0,
                "low_stock_threshold": None,
                "is_low_stock": False,
                "updated_at": "",
            }
        quantity_on_hand = int(row["quantity_on_hand"])
        reserved = self._active_reserved_quantity(part_id)
        threshold = row["low_stock_threshold"]
        available = max(quantity_on_hand - reserved, 0)
        return {
            "part_id": row["part_id"],
            "quantity_on_hand": quantity_on_hand,
            "reserved_quantity": reserved,
            "available_quantity": available,
            "low_stock_threshold": threshold,
            "is_low_stock": threshold is not None and available <= int(threshold),
            "updated_at": row["updated_at"],
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
        usable_quantity = int(stock["available_quantity"]) + self._active_reserved_quantity(part_id, request_number)
        if usable_quantity < quantity or current_quantity < quantity:
            raise InsufficientStockError("Insufficient stock for requested parts usage")
        stock_after_use = current_quantity - quantity
        with self._connection:
            self._consume_reservations(request_number, part_id, quantity)
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
            self._insert_stock_movement(part_id, "consumption", -quantity, request_number, None, actor, note)
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

    def reserve_part(
        self,
        request_number: str,
        part_id: int,
        quantity: int,
        appointment_id: int | None,
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        self._get_part(part_id)
        stock = self.get_stock_count(part_id)
        if int(stock["available_quantity"]) < quantity:
            raise InsufficientStockError("Insufficient available stock for reservation")
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO part_reservations (request_number, appointment_id, part_id, quantity, status, note, actor)
                VALUES (?, ?, ?, ?, 'active', ?, ?)
                """,
                (request_number, appointment_id, part_id, quantity, note, actor),
            )
            reservation_id = int(cursor.lastrowid)
            self._insert_stock_movement(part_id, "reservation_created", quantity, request_number, reservation_id, actor, note)
        return self._get_reservation(reservation_id)

    def adjust_reservation(self, reservation_id: int, quantity: int, note: str | None, actor: str) -> dict[str, object]:
        current = self._get_reservation(reservation_id)
        if current["status"] != "active":
            raise KeyError(str(reservation_id))
        old_quantity = int(current["quantity"])
        part_id = int(current["part_id"])
        delta = quantity - old_quantity
        stock = self.get_stock_count(part_id)
        if delta > 0 and int(stock["available_quantity"]) < delta:
            raise InsufficientStockError("Insufficient available stock for reservation adjustment")
        with self._connection:
            self._connection.execute(
                """
                UPDATE part_reservations
                SET quantity = ?, note = COALESCE(?, note), actor = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (quantity, note, actor, reservation_id),
            )
            self._insert_stock_movement(
                part_id,
                "reservation_adjusted",
                delta,
                str(current["request_number"]),
                reservation_id,
                actor,
                note,
            )
        return self._get_reservation(reservation_id)

    def release_reservation(self, reservation_id: int, note: str | None, actor: str) -> dict[str, object]:
        current = self._get_reservation(reservation_id)
        if current["status"] != "active":
            raise KeyError(str(reservation_id))
        with self._connection:
            self._connection.execute(
                """
                UPDATE part_reservations
                SET status = 'released', note = COALESCE(?, note), actor = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (note, actor, reservation_id),
            )
            self._insert_stock_movement(
                int(current["part_id"]),
                "release",
                -int(current["quantity"]),
                str(current["request_number"]),
                reservation_id,
                actor,
                note,
            )
        return self._get_reservation(reservation_id)

    def list_reservations(self, request_number: str | None = None) -> list[dict[str, object]]:
        where = "" if request_number is None else "WHERE pr.request_number = ?"
        params: tuple[object, ...] = () if request_number is None else (request_number,)
        rows = self._connection.execute(
            f"""
            SELECT pr.*, pc.sku, pc.name AS part_name
            FROM part_reservations pr
            JOIN parts_catalog pc ON pc.id = pr.part_id
            {where}
            ORDER BY pr.id DESC
            """,
            params,
        ).fetchall()
        return [self._reservation_row(row) for row in rows]

    def list_stock_movements(self, part_id: int | None = None, request_number: str | None = None) -> list[dict[str, object]]:
        clauses: list[str] = []
        params: list[object] = []
        if part_id is not None:
            clauses.append("sm.part_id = ?")
            params.append(part_id)
        if request_number is not None:
            clauses.append("sm.request_number = ?")
            params.append(request_number)
        where = "" if not clauses else "WHERE " + " AND ".join(clauses)
        rows = self._connection.execute(
            f"""
            SELECT sm.*, pc.sku, pc.name AS part_name
            FROM stock_movements sm
            JOIN parts_catalog pc ON pc.id = sm.part_id
            {where}
            ORDER BY sm.id DESC
            """,
            tuple(params),
        ).fetchall()
        return [self._movement_row(row) for row in rows]

    def add_compatibility(self, part_id: int, payload: Any) -> dict[str, object]:
        self._get_part(part_id)
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO part_compatibility (
                    part_id, compatibility_level, brand, model, series, machine_family, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    part_id,
                    payload.compatibility_level,
                    payload.brand,
                    payload.model,
                    payload.series,
                    payload.machine_family,
                    payload.note,
                ),
            )
        return self._get_compatibility(int(cursor.lastrowid))

    def _get_reservation(self, reservation_id: int) -> dict[str, object]:
        row = self._connection.execute(
            """
            SELECT pr.*, pc.sku, pc.name AS part_name
            FROM part_reservations pr
            JOIN parts_catalog pc ON pc.id = pr.part_id
            WHERE pr.id = ?
            """,
            (reservation_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(reservation_id))
        return self._reservation_row(row)

    def _active_reserved_quantity(self, part_id: int, request_number: str | None = None) -> int:
        request_filter = "" if request_number is None else "AND request_number = ?"
        params: tuple[object, ...] = (part_id,) if request_number is None else (part_id, request_number)
        row = self._connection.execute(
            f"""
            SELECT COALESCE(SUM(quantity), 0) AS reserved_quantity
            FROM part_reservations
            WHERE part_id = ? AND status = 'active' {request_filter}
            """,
            params,
        ).fetchone()
        return 0 if row is None else int(row["reserved_quantity"])

    def _consume_reservations(self, request_number: str, part_id: int, quantity: int) -> None:
        remaining = quantity
        rows = self._connection.execute(
            """
            SELECT id, quantity
            FROM part_reservations
            WHERE request_number = ? AND part_id = ? AND status = 'active'
            ORDER BY id
            """,
            (request_number, part_id),
        ).fetchall()
        for row in rows:
            if remaining <= 0:
                return
            reservation_quantity = int(row["quantity"])
            reservation_id = int(row["id"])
            if reservation_quantity <= remaining:
                self._connection.execute(
                    "UPDATE part_reservations SET status = 'consumed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (reservation_id,),
                )
                remaining -= reservation_quantity
            else:
                self._connection.execute(
                    "UPDATE part_reservations SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (reservation_quantity - remaining, reservation_id),
                )
                remaining = 0

    def _insert_stock_movement(
        self,
        part_id: int,
        movement_type: str,
        quantity: int,
        request_number: str | None,
        reservation_id: int | None,
        actor: str,
        note: str | None,
    ) -> None:
        stock = self.get_stock_count(part_id)
        self._connection.execute(
            """
            INSERT INTO stock_movements (
                part_id, movement_type, quantity, quantity_on_hand_after, reserved_quantity_after,
                available_quantity_after, request_number, reservation_id, note, actor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part_id,
                movement_type,
                quantity,
                stock["quantity_on_hand"],
                stock["reserved_quantity"],
                stock["available_quantity"],
                request_number,
                reservation_id,
                note,
                actor,
            ),
        )

    def _factual_key(self, payload: CreatePartPayload) -> str | None:
        values = [
            payload.part_type,
            payload.brand,
            payload.parameter_label,
            payload.parameter_value,
            payload.parameter_unit,
        ]
        normalized = [self._normalize_key_part(value) for value in values]
        if not normalized[0] or not normalized[3]:
            return None
        return "|".join(normalized)

    def _normalize_key_part(self, value: str | None) -> str:
        return "" if value is None else " ".join(value.strip().lower().split())

    def _part_exists_by_factual_key(self, factual_key: str) -> bool:
        row = self._connection.execute(
            "SELECT id FROM parts_catalog WHERE factual_key = ? LIMIT 1",
            (factual_key,),
        ).fetchone()
        return row is not None

    def _list_compatibility(self, part_id: int) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM part_compatibility
            WHERE part_id = ?
            ORDER BY id
            """,
            (part_id,),
        ).fetchall()
        return [self._compatibility_row(row) for row in rows]

    def _get_compatibility(self, compatibility_id: int) -> dict[str, object]:
        row = self._connection.execute(
            "SELECT * FROM part_compatibility WHERE id = ?",
            (compatibility_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(compatibility_id))
        return self._compatibility_row(row)

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
                pc.part_type,
                pc.parameter_label,
                pc.parameter_value,
                pc.parameter_unit,
                pc.factual_key,
                pc.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand,
                COALESCE((
                    SELECT SUM(pr.quantity)
                    FROM part_reservations pr
                    WHERE pr.part_id = pc.id AND pr.status = 'active'
                ), 0) AS reserved_quantity,
                sc.low_stock_threshold,
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
        quantity_on_hand = int(row["quantity_on_hand"])
        reserved_quantity = int(row["reserved_quantity"])
        available_quantity = max(quantity_on_hand - reserved_quantity, 0)
        threshold = row["low_stock_threshold"]
        return {
            "part_id": row["id"],
            "sku": row["sku"],
            "name": row["name"],
            "brand": row["brand"],
            "model": row["model"],
            "unit": row["unit"],
            "compatibility_note": row["compatibility_note"],
            "part_type": row["part_type"],
            "parameter_label": row["parameter_label"],
            "parameter_value": row["parameter_value"],
            "parameter_unit": row["parameter_unit"],
            "factual_key": row["factual_key"],
            "compatibility": self._list_compatibility(int(row["id"])),
            "created_at": row["created_at"],
            "quantity_on_hand": quantity_on_hand,
            "reserved_quantity": reserved_quantity,
            "available_quantity": available_quantity,
            "low_stock_threshold": threshold,
            "is_low_stock": threshold is not None and available_quantity <= int(threshold),
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

    def _reservation_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "reservation_id": row["id"],
            "request_number": row["request_number"],
            "appointment_id": row["appointment_id"],
            "part_id": row["part_id"],
            "sku": row["sku"],
            "part_name": row["part_name"],
            "quantity": row["quantity"],
            "status": row["status"],
            "note": row["note"],
            "actor": row["actor"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _movement_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "movement_id": row["id"],
            "part_id": row["part_id"],
            "sku": row["sku"],
            "part_name": row["part_name"],
            "movement_type": row["movement_type"],
            "quantity": row["quantity"],
            "quantity_on_hand_after": row["quantity_on_hand_after"],
            "reserved_quantity_after": row["reserved_quantity_after"],
            "available_quantity_after": row["available_quantity_after"],
            "request_number": row["request_number"],
            "reservation_id": row["reservation_id"],
            "note": row["note"],
            "actor": row["actor"],
            "created_at": row["created_at"],
        }

    def _compatibility_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "compatibility_id": row["id"],
            "part_id": row["part_id"],
            "compatibility_level": row["compatibility_level"],
            "brand": row["brand"],
            "model": row["model"],
            "series": row["series"],
            "machine_family": row["machine_family"],
            "note": row["note"],
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
            INVENTORY_RESERVATIONS_MIGRATION_PATH,
            PART_COMPATIBILITY_MIGRATION_PATH,
            INVENTORY_RUSSIAN_CATALOG_MIGRATION_PATH,
        ):
            connection.execute(migration_path.read_text(encoding="utf-8"))
        connection.commit()

    def create_part(self, payload: CreatePartPayload) -> dict[str, object]:
        factual_key = self._factual_key(payload)
        if factual_key and self._part_exists_by_factual_key(factual_key):
            raise DuplicatePartError("Part with the same factual key already exists")
        row = self._connect().execute(
            """
            INSERT INTO parts_catalog (
                sku, name, brand, model, unit, compatibility_note,
                part_type, parameter_label, parameter_value, parameter_unit, factual_key
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                payload.sku,
                payload.name,
                payload.brand,
                payload.model,
                payload.unit,
                payload.compatibility_note,
                payload.part_type,
                payload.parameter_label,
                payload.parameter_value,
                payload.parameter_unit,
                factual_key,
            ),
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
                pc.part_type,
                pc.parameter_label,
                pc.parameter_value,
                pc.parameter_unit,
                pc.factual_key,
                pc.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand,
                COALESCE((
                    SELECT SUM(pr.quantity)
                    FROM part_reservations pr
                    WHERE pr.part_id = pc.id AND pr.status = 'active'
                ), 0) AS reserved_quantity,
                sc.low_stock_threshold,
                sc.updated_at AS stock_updated_at
            FROM parts_catalog pc
            LEFT JOIN stock_counts sc ON sc.part_id = pc.id
            ORDER BY pc.name, pc.id
            """
        ).fetchall()
        return [self._part_row(row) for row in rows]

    def set_stock_count(self, part_id: int, quantity_on_hand: int, low_stock_threshold: int | None = None) -> dict[str, object]:
        self._get_part(part_id)
        with self._connect().transaction():
            self._connect().execute(
                """
                INSERT INTO stock_counts (part_id, quantity_on_hand, low_stock_threshold, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT(part_id) DO UPDATE SET
                    quantity_on_hand = excluded.quantity_on_hand,
                    low_stock_threshold = COALESCE(excluded.low_stock_threshold, stock_counts.low_stock_threshold),
                    updated_at = now()
                """,
                (part_id, quantity_on_hand, low_stock_threshold),
            )
            self._insert_stock_movement(part_id, "manual_adjustment", quantity_on_hand, None, None, "inventory", None)
        return self.get_stock_count(part_id)

    def get_stock_count(self, part_id: int) -> dict[str, object]:
        self._get_part(part_id)
        row = self._connect().execute(
            "SELECT part_id, quantity_on_hand, low_stock_threshold, updated_at FROM stock_counts WHERE part_id = %s",
            (part_id,),
        ).fetchone()
        if row is None:
            reserved = self._active_reserved_quantity(part_id)
            return {
                "part_id": part_id,
                "quantity_on_hand": 0,
                "reserved_quantity": reserved,
                "available_quantity": 0,
                "low_stock_threshold": None,
                "is_low_stock": False,
                "updated_at": "",
            }
        quantity_on_hand = int(row["quantity_on_hand"])
        reserved = self._active_reserved_quantity(part_id)
        threshold = row["low_stock_threshold"]
        available = max(quantity_on_hand - reserved, 0)
        return {
            "part_id": row["part_id"],
            "quantity_on_hand": quantity_on_hand,
            "reserved_quantity": reserved,
            "available_quantity": available,
            "low_stock_threshold": threshold,
            "is_low_stock": threshold is not None and available <= int(threshold),
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
        usable_quantity = int(stock["available_quantity"]) + self._active_reserved_quantity(part_id, request_number)
        if usable_quantity < quantity or current_quantity < quantity:
            raise InsufficientStockError("Insufficient stock for requested parts usage")
        stock_after_use = current_quantity - quantity
        connection = self._connect()
        with connection.transaction():
            self._consume_reservations(request_number, part_id, quantity)
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
            self._insert_stock_movement(part_id, "consumption", -quantity, request_number, None, actor, note)
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

    def reserve_part(
        self,
        request_number: str,
        part_id: int,
        quantity: int,
        appointment_id: int | None,
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        self._get_part(part_id)
        stock = self.get_stock_count(part_id)
        if int(stock["available_quantity"]) < quantity:
            raise InsufficientStockError("Insufficient available stock for reservation")
        with self._connect().transaction():
            row = self._connect().execute(
                """
                INSERT INTO part_reservations (request_number, appointment_id, part_id, quantity, status, note, actor)
                VALUES (%s, %s, %s, %s, 'active', %s, %s)
                RETURNING id
                """,
                (request_number, appointment_id, part_id, quantity, note, actor),
            ).fetchone()
            if row is None:
                raise RuntimeError("reservation insert did not return an id")
            reservation_id = int(row["id"])
            self._insert_stock_movement(part_id, "reservation_created", quantity, request_number, reservation_id, actor, note)
        return self._get_reservation(reservation_id)

    def adjust_reservation(self, reservation_id: int, quantity: int, note: str | None, actor: str) -> dict[str, object]:
        current = self._get_reservation(reservation_id)
        if current["status"] != "active":
            raise KeyError(str(reservation_id))
        old_quantity = int(current["quantity"])
        part_id = int(current["part_id"])
        delta = quantity - old_quantity
        stock = self.get_stock_count(part_id)
        if delta > 0 and int(stock["available_quantity"]) < delta:
            raise InsufficientStockError("Insufficient available stock for reservation adjustment")
        with self._connect().transaction():
            self._connect().execute(
                """
                UPDATE part_reservations
                SET quantity = %s, note = COALESCE(%s, note), actor = %s, updated_at = now()
                WHERE id = %s
                """,
                (quantity, note, actor, reservation_id),
            )
            self._insert_stock_movement(part_id, "reservation_adjusted", delta, str(current["request_number"]), reservation_id, actor, note)
        return self._get_reservation(reservation_id)

    def release_reservation(self, reservation_id: int, note: str | None, actor: str) -> dict[str, object]:
        current = self._get_reservation(reservation_id)
        if current["status"] != "active":
            raise KeyError(str(reservation_id))
        with self._connect().transaction():
            self._connect().execute(
                """
                UPDATE part_reservations
                SET status = 'released', note = COALESCE(%s, note), actor = %s, updated_at = now()
                WHERE id = %s
                """,
                (note, actor, reservation_id),
            )
            self._insert_stock_movement(int(current["part_id"]), "release", -int(current["quantity"]), str(current["request_number"]), reservation_id, actor, note)
        return self._get_reservation(reservation_id)

    def list_reservations(self, request_number: str | None = None) -> list[dict[str, object]]:
        where = "" if request_number is None else "WHERE pr.request_number = %s"
        params: tuple[object, ...] = () if request_number is None else (request_number,)
        rows = self._connect().execute(
            f"""
            SELECT pr.*, pc.sku, pc.name AS part_name
            FROM part_reservations pr
            JOIN parts_catalog pc ON pc.id = pr.part_id
            {where}
            ORDER BY pr.id DESC
            """,
            params,
        ).fetchall()
        return [self._reservation_row(row) for row in rows]

    def list_stock_movements(self, part_id: int | None = None, request_number: str | None = None) -> list[dict[str, object]]:
        clauses: list[str] = []
        params: list[object] = []
        if part_id is not None:
            clauses.append("sm.part_id = %s")
            params.append(part_id)
        if request_number is not None:
            clauses.append("sm.request_number = %s")
            params.append(request_number)
        where = "" if not clauses else "WHERE " + " AND ".join(clauses)
        rows = self._connect().execute(
            f"""
            SELECT sm.*, pc.sku, pc.name AS part_name
            FROM stock_movements sm
            JOIN parts_catalog pc ON pc.id = sm.part_id
            {where}
            ORDER BY sm.id DESC
            """,
            tuple(params),
        ).fetchall()
        return [self._movement_row(row) for row in rows]

    def add_compatibility(self, part_id: int, payload: Any) -> dict[str, object]:
        self._get_part(part_id)
        row = self._connect().execute(
            """
            INSERT INTO part_compatibility (
                part_id, compatibility_level, brand, model, series, machine_family, note
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                part_id,
                payload.compatibility_level,
                payload.brand,
                payload.model,
                payload.series,
                payload.machine_family,
                payload.note,
            ),
        ).fetchone()
        if row is None:
            raise RuntimeError("compatibility insert did not return an id")
        self._connect().commit()
        return self._get_compatibility(int(row["id"]))

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
                pc.part_type,
                pc.parameter_label,
                pc.parameter_value,
                pc.parameter_unit,
                pc.factual_key,
                pc.created_at,
                COALESCE(sc.quantity_on_hand, 0) AS quantity_on_hand,
                COALESCE((
                    SELECT SUM(pr.quantity)
                    FROM part_reservations pr
                    WHERE pr.part_id = pc.id AND pr.status = 'active'
                ), 0) AS reserved_quantity,
                sc.low_stock_threshold,
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
        quantity_on_hand = int(row["quantity_on_hand"])
        reserved_quantity = int(row["reserved_quantity"])
        available_quantity = max(quantity_on_hand - reserved_quantity, 0)
        threshold = row["low_stock_threshold"]
        return {
            "part_id": row["id"],
            "sku": row["sku"],
            "name": row["name"],
            "brand": row["brand"],
            "model": row["model"],
            "unit": row["unit"],
            "compatibility_note": row["compatibility_note"],
            "part_type": row.get("part_type"),
            "parameter_label": row.get("parameter_label"),
            "parameter_value": row.get("parameter_value"),
            "parameter_unit": row.get("parameter_unit"),
            "factual_key": row.get("factual_key"),
            "compatibility": row["compatibility"]
            if "compatibility" in row
            else self._list_compatibility(int(row["id"]))
            if "part_type" in row
            else [],
            "created_at": self._format_timestamp(row["created_at"]),
            "quantity_on_hand": quantity_on_hand,
            "reserved_quantity": reserved_quantity,
            "available_quantity": available_quantity,
            "low_stock_threshold": threshold,
            "is_low_stock": threshold is not None and available_quantity <= int(threshold),
            "stock_updated_at": None if row["stock_updated_at"] is None else self._format_timestamp(row["stock_updated_at"]),
        }

    def _factual_key(self, payload: CreatePartPayload) -> str | None:
        values = [
            payload.part_type,
            payload.brand,
            payload.parameter_label,
            payload.parameter_value,
            payload.parameter_unit,
        ]
        normalized = [self._normalize_key_part(value) for value in values]
        if not normalized[0] or not normalized[3]:
            return None
        return "|".join(normalized)

    def _normalize_key_part(self, value: str | None) -> str:
        return "" if value is None else " ".join(value.strip().lower().split())

    def _part_exists_by_factual_key(self, factual_key: str) -> bool:
        row = self._connect().execute(
            "SELECT id FROM parts_catalog WHERE factual_key = %s LIMIT 1",
            (factual_key,),
        ).fetchone()
        return row is not None

    def _list_compatibility(self, part_id: int) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT *
            FROM part_compatibility
            WHERE part_id = %s
            ORDER BY id
            """,
            (part_id,),
        ).fetchall()
        return [self._compatibility_row(row) for row in rows]

    def _get_compatibility(self, compatibility_id: int) -> dict[str, object]:
        row = self._connect().execute(
            "SELECT * FROM part_compatibility WHERE id = %s",
            (compatibility_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(compatibility_id))
        return self._compatibility_row(row)

    def _compatibility_row(self, row: dict[str, Any]) -> dict[str, object]:
        return {
            "compatibility_id": row["id"],
            "part_id": row["part_id"],
            "compatibility_level": row["compatibility_level"],
            "brand": row["brand"],
            "model": row["model"],
            "series": row["series"],
            "machine_family": row["machine_family"],
            "note": row["note"],
            "created_at": self._format_timestamp(row["created_at"]),
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

    def _get_reservation(self, reservation_id: int) -> dict[str, object]:
        row = self._connect().execute(
            """
            SELECT pr.*, pc.sku, pc.name AS part_name
            FROM part_reservations pr
            JOIN parts_catalog pc ON pc.id = pr.part_id
            WHERE pr.id = %s
            """,
            (reservation_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(reservation_id))
        return self._reservation_row(row)

    def _active_reserved_quantity(self, part_id: int, request_number: str | None = None) -> int:
        request_filter = "" if request_number is None else "AND request_number = %s"
        params: tuple[object, ...] = (part_id,) if request_number is None else (part_id, request_number)
        row = self._connect().execute(
            f"""
            SELECT COALESCE(SUM(quantity), 0) AS reserved_quantity
            FROM part_reservations
            WHERE part_id = %s AND status = 'active' {request_filter}
            """,
            params,
        ).fetchone()
        return 0 if row is None else int(row["reserved_quantity"])

    def _consume_reservations(self, request_number: str, part_id: int, quantity: int) -> None:
        remaining = quantity
        rows = self._connect().execute(
            """
            SELECT id, quantity
            FROM part_reservations
            WHERE request_number = %s AND part_id = %s AND status = 'active'
            ORDER BY id
            """,
            (request_number, part_id),
        ).fetchall()
        for row in rows:
            if remaining <= 0:
                return
            reservation_quantity = int(row["quantity"])
            reservation_id = int(row["id"])
            if reservation_quantity <= remaining:
                self._connect().execute(
                    "UPDATE part_reservations SET status = 'consumed', updated_at = now() WHERE id = %s",
                    (reservation_id,),
                )
                remaining -= reservation_quantity
            else:
                self._connect().execute(
                    "UPDATE part_reservations SET quantity = %s, updated_at = now() WHERE id = %s",
                    (reservation_quantity - remaining, reservation_id),
                )
                remaining = 0

    def _insert_stock_movement(
        self,
        part_id: int,
        movement_type: str,
        quantity: int,
        request_number: str | None,
        reservation_id: int | None,
        actor: str,
        note: str | None,
    ) -> None:
        stock = self.get_stock_count(part_id)
        self._connect().execute(
            """
            INSERT INTO stock_movements (
                part_id, movement_type, quantity, quantity_on_hand_after, reserved_quantity_after,
                available_quantity_after, request_number, reservation_id, note, actor
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                part_id,
                movement_type,
                quantity,
                stock["quantity_on_hand"],
                stock["reserved_quantity"],
                stock["available_quantity"],
                request_number,
                reservation_id,
                note,
                actor,
            ),
        )

    def _reservation_row(self, row: dict[str, Any]) -> dict[str, object]:
        return {
            "reservation_id": row["id"],
            "request_number": row["request_number"],
            "appointment_id": row["appointment_id"],
            "part_id": row["part_id"],
            "sku": row["sku"],
            "part_name": row["part_name"],
            "quantity": row["quantity"],
            "status": row["status"],
            "note": row["note"],
            "actor": row["actor"],
            "created_at": self._format_timestamp(row["created_at"]),
            "updated_at": self._format_timestamp(row["updated_at"]),
        }

    def _movement_row(self, row: dict[str, Any]) -> dict[str, object]:
        return {
            "movement_id": row["id"],
            "part_id": row["part_id"],
            "sku": row["sku"],
            "part_name": row["part_name"],
            "movement_type": row["movement_type"],
            "quantity": row["quantity"],
            "quantity_on_hand_after": row["quantity_on_hand_after"],
            "reserved_quantity_after": row["reserved_quantity_after"],
            "available_quantity_after": row["available_quantity_after"],
            "request_number": row["request_number"],
            "reservation_id": row["reservation_id"],
            "note": row["note"],
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
