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
PROCUREMENT_LITE_MIGRATION_PATH = MIGRATIONS_DIR / "0013_procurement_lite.sql"


class InsufficientStockError(ValueError):
    """Raised when a parts usage request exceeds available stock."""


class DuplicatePartError(ValueError):
    """Raised when a new catalog part duplicates an existing factual part."""


class InvalidPurchaseRequestTransitionError(ValueError):
    """Raised when a purchase request status transition is not allowed."""


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

    def create_supplier(self, payload: Any, actor: str) -> dict[str, object]:
        """Persist a procurement supplier."""

    def list_suppliers(self) -> list[dict[str, object]]:
        """Return active and inactive procurement suppliers."""

    def create_purchase_request(
        self,
        supplier_id: int,
        items: list[Any],
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        """Create a draft purchase request."""

    def list_purchase_requests(self) -> list[dict[str, object]]:
        """Return purchase requests."""

    def get_purchase_request(self, purchase_request_id: int) -> dict[str, object]:
        """Return a purchase request with items."""

    def replace_purchase_request_items(
        self,
        purchase_request_id: int,
        items: list[Any],
        actor: str,
    ) -> dict[str, object]:
        """Replace items on a draft purchase request."""

    def submit_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        """Submit a draft purchase request for approval."""

    def approve_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        """Approve a pending purchase request."""

    def mark_purchase_request_ordered(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        """Mark an approved purchase request as ordered."""

    def receive_purchase_request(self, purchase_request_id: int, actor: str, note: str | None = None) -> dict[str, object]:
        """Receive an ordered purchase request into stock."""

    def cancel_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        """Cancel a purchase request before it is received."""

    def create_low_stock_purchase_draft(self, supplier_id: int, actor: str, note: str | None = None) -> dict[str, object]:
        """Create a purchase draft from current low-stock parts."""


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

            CREATE TABLE IF NOT EXISTS procurement_suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_name TEXT,
                phone TEXT,
                email TEXT,
                note TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                actor TEXT NOT NULL DEFAULT 'inventory',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL REFERENCES procurement_suppliers(id),
                status TEXT NOT NULL CHECK (status IN ('draft', 'pending_approval', 'approved', 'ordered', 'received', 'cancelled')),
                note TEXT,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS purchase_request_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_request_id INTEGER NOT NULL REFERENCES purchase_requests(id) ON DELETE CASCADE,
                part_id INTEGER NOT NULL REFERENCES parts_catalog(id),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                note TEXT
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

    def create_supplier(self, payload: Any, actor: str) -> dict[str, object]:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO procurement_suppliers (name, contact_name, phone, email, note, actor)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (payload.name, payload.contact_name, payload.phone, payload.email, payload.note, actor),
            )
        return self._get_supplier(int(cursor.lastrowid))

    def list_suppliers(self) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM procurement_suppliers
            ORDER BY active DESC, name, id
            """
        ).fetchall()
        return [self._supplier_row(row) for row in rows]

    def create_purchase_request(
        self,
        supplier_id: int,
        items: list[Any],
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        self._get_supplier(supplier_id)
        self._validate_purchase_items(items)
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO purchase_requests (supplier_id, status, note, actor)
                VALUES (?, 'draft', ?, ?)
                """,
                (supplier_id, note, actor),
            )
            purchase_request_id = int(cursor.lastrowid)
            self._insert_purchase_items(purchase_request_id, items)
        return self.get_purchase_request(purchase_request_id)

    def list_purchase_requests(self) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT pr.*, ps.name AS supplier_name
            FROM purchase_requests pr
            JOIN procurement_suppliers ps ON ps.id = pr.supplier_id
            ORDER BY pr.id DESC
            """
        ).fetchall()
        return [self._purchase_request_row(row) for row in rows]

    def get_purchase_request(self, purchase_request_id: int) -> dict[str, object]:
        row = self._connection.execute(
            """
            SELECT pr.*, ps.name AS supplier_name
            FROM purchase_requests pr
            JOIN procurement_suppliers ps ON ps.id = pr.supplier_id
            WHERE pr.id = ?
            """,
            (purchase_request_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(purchase_request_id))
        return self._purchase_request_row(row)

    def replace_purchase_request_items(
        self,
        purchase_request_id: int,
        items: list[Any],
        actor: str,
    ) -> dict[str, object]:
        current = self.get_purchase_request(purchase_request_id)
        if current["status"] != "draft":
            raise InvalidPurchaseRequestTransitionError("Purchase request items can be edited only in draft status")
        self._validate_purchase_items(items)
        with self._connection:
            self._connection.execute("DELETE FROM purchase_request_items WHERE purchase_request_id = ?", (purchase_request_id,))
            self._insert_purchase_items(purchase_request_id, items)
            self._touch_purchase_request(purchase_request_id, actor)
        return self.get_purchase_request(purchase_request_id)

    def submit_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        return self._transition_purchase_request(purchase_request_id, "draft", "pending_approval", actor)

    def approve_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        return self._transition_purchase_request(purchase_request_id, "pending_approval", "approved", actor)

    def mark_purchase_request_ordered(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        return self._transition_purchase_request(purchase_request_id, "approved", "ordered", actor)

    def receive_purchase_request(self, purchase_request_id: int, actor: str, note: str | None = None) -> dict[str, object]:
        current = self.get_purchase_request(purchase_request_id)
        if current["status"] != "ordered":
            raise InvalidPurchaseRequestTransitionError("Only ordered purchase requests can be received")
        with self._connection:
            for item in current["items"]:
                part_id = int(item["part_id"])
                quantity = int(item["quantity"])
                self._connection.execute(
                    """
                    INSERT INTO stock_counts (part_id, quantity_on_hand, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(part_id) DO UPDATE SET
                        quantity_on_hand = stock_counts.quantity_on_hand + excluded.quantity_on_hand,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (part_id, quantity),
                )
                movement_note = self._purchase_receipt_note(purchase_request_id, note)
                self._insert_stock_movement(part_id, "procurement_receipt", quantity, None, None, actor, movement_note)
            self._set_purchase_request_status(purchase_request_id, "received", actor)
        return self.get_purchase_request(purchase_request_id)

    def cancel_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        current = self.get_purchase_request(purchase_request_id)
        if current["status"] not in {"draft", "pending_approval", "approved", "ordered"}:
            raise InvalidPurchaseRequestTransitionError("Purchase request cannot be cancelled from its current status")
        with self._connection:
            self._set_purchase_request_status(purchase_request_id, "cancelled", actor)
        return self.get_purchase_request(purchase_request_id)

    def create_low_stock_purchase_draft(self, supplier_id: int, actor: str, note: str | None = None) -> dict[str, object]:
        self._get_supplier(supplier_id)
        low_stock_items = []
        for part in self.list_parts():
            threshold = part.get("low_stock_threshold")
            if threshold is None or not bool(part.get("is_low_stock")):
                continue
            reorder_quantity = max(int(threshold) * 2 - int(part["available_quantity"]), 1)
            low_stock_items.append(
                {
                    "part_id": int(part["part_id"]),
                    "quantity": reorder_quantity,
                    "note": "Created from low-stock inventory signal",
                }
            )
        if not low_stock_items:
            raise ValueError("No low-stock parts are available for purchase draft")
        return self.create_purchase_request(
            supplier_id,
            low_stock_items,
            note or "Low-stock purchase draft",
            actor,
        )

    def _get_supplier(self, supplier_id: int) -> dict[str, object]:
        row = self._connection.execute(
            "SELECT * FROM procurement_suppliers WHERE id = ?",
            (supplier_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(supplier_id))
        return self._supplier_row(row)

    def _supplier_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "supplier_id": row["id"],
            "name": row["name"],
            "contact_name": row["contact_name"],
            "phone": row["phone"],
            "email": row["email"],
            "note": row["note"],
            "active": bool(row["active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _validate_purchase_items(self, items: list[Any]) -> None:
        if not items:
            raise ValueError("Purchase request requires at least one item")
        for item in items:
            self._get_part(int(item.part_id if hasattr(item, "part_id") else item["part_id"]))
            quantity = int(item.quantity if hasattr(item, "quantity") else item["quantity"])
            if quantity <= 0:
                raise ValueError("Purchase request item quantity must be positive")

    def _insert_purchase_items(self, purchase_request_id: int, items: list[Any]) -> None:
        self._connection.executemany(
            """
            INSERT INTO purchase_request_items (purchase_request_id, part_id, quantity, note)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    purchase_request_id,
                    int(item.part_id if hasattr(item, "part_id") else item["part_id"]),
                    int(item.quantity if hasattr(item, "quantity") else item["quantity"]),
                    item.note if hasattr(item, "note") else item.get("note"),
                )
                for item in items
            ],
        )

    def _purchase_request_row(self, row: sqlite3.Row) -> dict[str, object]:
        purchase_request_id = int(row["id"])
        return {
            "purchase_request_id": purchase_request_id,
            "supplier_id": row["supplier_id"],
            "supplier_name": row["supplier_name"],
            "status": row["status"],
            "note": row["note"],
            "actor": row["actor"],
            "items": self._list_purchase_items(purchase_request_id),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _list_purchase_items(self, purchase_request_id: int) -> list[dict[str, object]]:
        rows = self._connection.execute(
            """
            SELECT pri.*, pc.sku, pc.name AS part_name, pc.unit
            FROM purchase_request_items pri
            JOIN parts_catalog pc ON pc.id = pri.part_id
            WHERE pri.purchase_request_id = ?
            ORDER BY pri.id
            """,
            (purchase_request_id,),
        ).fetchall()
        return [
            {
                "item_id": row["id"],
                "purchase_request_id": row["purchase_request_id"],
                "part_id": row["part_id"],
                "sku": row["sku"],
                "part_name": row["part_name"],
                "unit": row["unit"],
                "quantity": row["quantity"],
                "note": row["note"],
            }
            for row in rows
        ]

    def _transition_purchase_request(
        self,
        purchase_request_id: int,
        expected_status: str,
        next_status: str,
        actor: str,
    ) -> dict[str, object]:
        current = self.get_purchase_request(purchase_request_id)
        if current["status"] != expected_status:
            raise InvalidPurchaseRequestTransitionError(
                f"Purchase request must be {expected_status} before it can move to {next_status}"
            )
        with self._connection:
            self._set_purchase_request_status(purchase_request_id, next_status, actor)
        return self.get_purchase_request(purchase_request_id)

    def _set_purchase_request_status(self, purchase_request_id: int, status: str, actor: str) -> None:
        self._connection.execute(
            """
            UPDATE purchase_requests
            SET status = ?, actor = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, actor, purchase_request_id),
        )

    def _touch_purchase_request(self, purchase_request_id: int, actor: str) -> None:
        self._connection.execute(
            """
            UPDATE purchase_requests
            SET actor = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (actor, purchase_request_id),
        )

    def _purchase_receipt_note(self, purchase_request_id: int, note: str | None) -> str:
        base = f"Purchase request #{purchase_request_id} received"
        return base if note is None else f"{base}: {note}"

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
            PROCUREMENT_LITE_MIGRATION_PATH,
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
        connection = self._connect()
        with connection.transaction():
            stock = self._get_stock_count_for_update(connection, part_id)
            current_quantity = int(stock["quantity_on_hand"])
            usable_quantity = int(stock["available_quantity"]) + self._active_reserved_quantity_for_update(
                connection,
                part_id,
                request_number,
            )
            if usable_quantity < quantity or current_quantity < quantity:
                raise InsufficientStockError("Insufficient stock for requested parts usage")
            stock_after_use = current_quantity - quantity
            self._consume_reservations(connection, request_number, part_id, quantity)
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
        connection = self._connect()
        with connection.transaction():
            stock = self._get_stock_count_for_update(connection, part_id)
            if int(stock["available_quantity"]) < quantity:
                raise InsufficientStockError("Insufficient available stock for reservation")
            row = connection.execute(
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
        reservation = self._get_reservation(reservation_id)
        part_id = int(reservation["part_id"])
        connection = self._connect()
        with connection.transaction():
            stock = self._get_stock_count_for_update(connection, part_id)
            current = self._get_reservation_for_update(connection, reservation_id)
            if current["status"] != "active":
                raise KeyError(str(reservation_id))
            old_quantity = int(current["quantity"])
            delta = quantity - old_quantity
            if delta > 0 and int(stock["available_quantity"]) < delta:
                raise InsufficientStockError("Insufficient available stock for reservation adjustment")
            connection.execute(
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
        connection = self._connect()
        with connection.transaction():
            current = self._get_reservation_for_update(connection, reservation_id)
            if current["status"] != "active":
                raise KeyError(str(reservation_id))
            connection.execute(
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

    def create_supplier(self, payload: Any, actor: str) -> dict[str, object]:
        row = self._connect().execute(
            """
            INSERT INTO procurement_suppliers (name, contact_name, phone, email, note, actor)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (payload.name, payload.contact_name, payload.phone, payload.email, payload.note, actor),
        ).fetchone()
        if row is None:
            raise RuntimeError("supplier insert did not return an id")
        self._connect().commit()
        return self._get_supplier(int(row["id"]))

    def list_suppliers(self) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT *
            FROM procurement_suppliers
            ORDER BY active DESC, name, id
            """
        ).fetchall()
        return [self._supplier_row(row) for row in rows]

    def create_purchase_request(
        self,
        supplier_id: int,
        items: list[Any],
        note: str | None,
        actor: str,
    ) -> dict[str, object]:
        self._get_supplier(supplier_id)
        self._validate_purchase_items(items)
        connection = self._connect()
        with connection.transaction():
            row = connection.execute(
                """
                INSERT INTO purchase_requests (supplier_id, status, note, actor)
                VALUES (%s, 'draft', %s, %s)
                RETURNING id
                """,
                (supplier_id, note, actor),
            ).fetchone()
            if row is None:
                raise RuntimeError("purchase request insert did not return an id")
            purchase_request_id = int(row["id"])
            self._insert_purchase_items(connection, purchase_request_id, items)
        return self.get_purchase_request(purchase_request_id)

    def list_purchase_requests(self) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT pr.*, ps.name AS supplier_name
            FROM purchase_requests pr
            JOIN procurement_suppliers ps ON ps.id = pr.supplier_id
            ORDER BY pr.id DESC
            """
        ).fetchall()
        return [self._purchase_request_row(row) for row in rows]

    def get_purchase_request(self, purchase_request_id: int) -> dict[str, object]:
        row = self._connect().execute(
            """
            SELECT pr.*, ps.name AS supplier_name
            FROM purchase_requests pr
            JOIN procurement_suppliers ps ON ps.id = pr.supplier_id
            WHERE pr.id = %s
            """,
            (purchase_request_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(purchase_request_id))
        return self._purchase_request_row(row)

    def replace_purchase_request_items(
        self,
        purchase_request_id: int,
        items: list[Any],
        actor: str,
    ) -> dict[str, object]:
        current = self.get_purchase_request(purchase_request_id)
        if current["status"] != "draft":
            raise InvalidPurchaseRequestTransitionError("Purchase request items can be edited only in draft status")
        self._validate_purchase_items(items)
        connection = self._connect()
        with connection.transaction():
            connection.execute("DELETE FROM purchase_request_items WHERE purchase_request_id = %s", (purchase_request_id,))
            self._insert_purchase_items(connection, purchase_request_id, items)
            self._touch_purchase_request(connection, purchase_request_id, actor)
        return self.get_purchase_request(purchase_request_id)

    def submit_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        return self._transition_purchase_request(purchase_request_id, "draft", "pending_approval", actor)

    def approve_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        return self._transition_purchase_request(purchase_request_id, "pending_approval", "approved", actor)

    def mark_purchase_request_ordered(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        return self._transition_purchase_request(purchase_request_id, "approved", "ordered", actor)

    def receive_purchase_request(self, purchase_request_id: int, actor: str, note: str | None = None) -> dict[str, object]:
        connection = self._connect()
        with connection.transaction():
            current = self._purchase_request_row(self._get_purchase_request_for_update(connection, purchase_request_id))
            if current["status"] != "ordered":
                raise InvalidPurchaseRequestTransitionError("Only ordered purchase requests can be received")
            for item in current["items"]:
                part_id = int(item["part_id"])
                quantity = int(item["quantity"])
                self._get_stock_count_for_update(connection, part_id)
                connection.execute(
                    """
                    INSERT INTO stock_counts (part_id, quantity_on_hand, updated_at)
                    VALUES (%s, %s, now())
                    ON CONFLICT(part_id) DO UPDATE SET
                        quantity_on_hand = stock_counts.quantity_on_hand + excluded.quantity_on_hand,
                        updated_at = now()
                    """,
                    (part_id, quantity),
                )
                self._insert_stock_movement(
                    part_id,
                    "procurement_receipt",
                    quantity,
                    None,
                    None,
                    actor,
                    self._purchase_receipt_note(purchase_request_id, note),
                )
            self._set_purchase_request_status(connection, purchase_request_id, "received", actor)
        return self.get_purchase_request(purchase_request_id)

    def cancel_purchase_request(self, purchase_request_id: int, actor: str) -> dict[str, object]:
        connection = self._connect()
        with connection.transaction():
            current = self._purchase_request_row(self._get_purchase_request_for_update(connection, purchase_request_id))
            if current["status"] not in {"draft", "pending_approval", "approved", "ordered"}:
                raise InvalidPurchaseRequestTransitionError("Purchase request cannot be cancelled from its current status")
            self._set_purchase_request_status(connection, purchase_request_id, "cancelled", actor)
        return self.get_purchase_request(purchase_request_id)

    def create_low_stock_purchase_draft(self, supplier_id: int, actor: str, note: str | None = None) -> dict[str, object]:
        self._get_supplier(supplier_id)
        low_stock_items = []
        for part in self.list_parts():
            threshold = part.get("low_stock_threshold")
            if threshold is None or not bool(part.get("is_low_stock")):
                continue
            low_stock_items.append(
                {
                    "part_id": int(part["part_id"]),
                    "quantity": max(int(threshold) * 2 - int(part["available_quantity"]), 1),
                    "note": "Created from low-stock inventory signal",
                }
            )
        if not low_stock_items:
            raise ValueError("No low-stock parts are available for purchase draft")
        return self.create_purchase_request(supplier_id, low_stock_items, note or "Low-stock purchase draft", actor)

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

    def _get_reservation_for_update(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        reservation_id: int,
    ) -> dict[str, object]:
        row = connection.execute(
            """
            SELECT pr.*, pc.sku, pc.name AS part_name
            FROM part_reservations pr
            JOIN parts_catalog pc ON pc.id = pr.part_id
            WHERE pr.id = %s
            FOR UPDATE OF pr
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

    def _active_reserved_quantity_for_update(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        part_id: int,
        request_number: str | None = None,
    ) -> int:
        request_filter = "" if request_number is None else "AND request_number = %s"
        params: tuple[object, ...] = (part_id,) if request_number is None else (part_id, request_number)
        rows = connection.execute(
            f"""
            SELECT quantity
            FROM part_reservations
            WHERE part_id = %s AND status = 'active' {request_filter}
            FOR UPDATE
            """,
            params,
        ).fetchall()
        return sum(int(row["quantity"]) for row in rows)

    def _get_stock_count_for_update(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        part_id: int,
    ) -> dict[str, object]:
        row = connection.execute(
            """
            SELECT part_id, quantity_on_hand, low_stock_threshold, updated_at
            FROM stock_counts
            WHERE part_id = %s
            FOR UPDATE
            """,
            (part_id,),
        ).fetchone()
        reserved = self._active_reserved_quantity_for_update(connection, part_id)
        if row is None:
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

    def _consume_reservations(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        request_number: str,
        part_id: int,
        quantity: int,
    ) -> None:
        remaining = quantity
        rows = connection.execute(
            """
            SELECT id, quantity
            FROM part_reservations
            WHERE request_number = %s AND part_id = %s AND status = 'active'
            ORDER BY id
            FOR UPDATE
            """,
            (request_number, part_id),
        ).fetchall()
        for row in rows:
            if remaining <= 0:
                return
            reservation_quantity = int(row["quantity"])
            reservation_id = int(row["id"])
            if reservation_quantity <= remaining:
                connection.execute(
                    "UPDATE part_reservations SET status = 'consumed', updated_at = now() WHERE id = %s",
                    (reservation_id,),
                )
                remaining -= reservation_quantity
            else:
                connection.execute(
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

    def _get_supplier(self, supplier_id: int) -> dict[str, object]:
        row = self._connect().execute(
            "SELECT * FROM procurement_suppliers WHERE id = %s",
            (supplier_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(supplier_id))
        return self._supplier_row(row)

    def _supplier_row(self, row: dict[str, Any]) -> dict[str, object]:
        return {
            "supplier_id": row["id"],
            "name": row["name"],
            "contact_name": row["contact_name"],
            "phone": row["phone"],
            "email": row["email"],
            "note": row["note"],
            "active": bool(row["active"]),
            "created_at": self._format_timestamp(row["created_at"]),
            "updated_at": self._format_timestamp(row["updated_at"]),
        }

    def _validate_purchase_items(self, items: list[Any]) -> None:
        if not items:
            raise ValueError("Purchase request requires at least one item")
        for item in items:
            self._get_part(int(item.part_id if hasattr(item, "part_id") else item["part_id"]))
            quantity = int(item.quantity if hasattr(item, "quantity") else item["quantity"])
            if quantity <= 0:
                raise ValueError("Purchase request item quantity must be positive")

    def _insert_purchase_items(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        purchase_request_id: int,
        items: list[Any],
    ) -> None:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO purchase_request_items (purchase_request_id, part_id, quantity, note)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (
                        purchase_request_id,
                        int(item.part_id if hasattr(item, "part_id") else item["part_id"]),
                        int(item.quantity if hasattr(item, "quantity") else item["quantity"]),
                        item.note if hasattr(item, "note") else item.get("note"),
                    )
                    for item in items
                ],
            )

    def _purchase_request_row(self, row: dict[str, Any]) -> dict[str, object]:
        purchase_request_id = int(row["id"])
        return {
            "purchase_request_id": purchase_request_id,
            "supplier_id": row["supplier_id"],
            "supplier_name": row["supplier_name"],
            "status": row["status"],
            "note": row["note"],
            "actor": row["actor"],
            "items": self._list_purchase_items(purchase_request_id),
            "created_at": self._format_timestamp(row["created_at"]),
            "updated_at": self._format_timestamp(row["updated_at"]),
        }

    def _list_purchase_items(self, purchase_request_id: int) -> list[dict[str, object]]:
        rows = self._connect().execute(
            """
            SELECT pri.*, pc.sku, pc.name AS part_name, pc.unit
            FROM purchase_request_items pri
            JOIN parts_catalog pc ON pc.id = pri.part_id
            WHERE pri.purchase_request_id = %s
            ORDER BY pri.id
            """,
            (purchase_request_id,),
        ).fetchall()
        return [
            {
                "item_id": row["id"],
                "purchase_request_id": row["purchase_request_id"],
                "part_id": row["part_id"],
                "sku": row["sku"],
                "part_name": row["part_name"],
                "unit": row["unit"],
                "quantity": row["quantity"],
                "note": row["note"],
            }
            for row in rows
        ]

    def _transition_purchase_request(
        self,
        purchase_request_id: int,
        expected_status: str,
        next_status: str,
        actor: str,
    ) -> dict[str, object]:
        connection = self._connect()
        with connection.transaction():
            current = self._purchase_request_row(self._get_purchase_request_for_update(connection, purchase_request_id))
            if current["status"] != expected_status:
                raise InvalidPurchaseRequestTransitionError(
                    f"Purchase request must be {expected_status} before it can move to {next_status}"
                )
            self._set_purchase_request_status(connection, purchase_request_id, next_status, actor)
        return self.get_purchase_request(purchase_request_id)

    def _get_purchase_request_for_update(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        purchase_request_id: int,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT pr.*, ps.name AS supplier_name
            FROM purchase_requests pr
            JOIN procurement_suppliers ps ON ps.id = pr.supplier_id
            WHERE pr.id = %s
            FOR UPDATE OF pr
            """,
            (purchase_request_id,),
        ).fetchone()
        if row is None:
            raise KeyError(str(purchase_request_id))
        return row

    def _set_purchase_request_status(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        purchase_request_id: int,
        status: str,
        actor: str,
    ) -> None:
        connection.execute(
            """
            UPDATE purchase_requests
            SET status = %s, actor = %s, updated_at = now()
            WHERE id = %s
            """,
            (status, actor, purchase_request_id),
        )

    def _touch_purchase_request(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        purchase_request_id: int,
        actor: str,
    ) -> None:
        connection.execute(
            """
            UPDATE purchase_requests
            SET actor = %s, updated_at = now()
            WHERE id = %s
            """,
            (actor, purchase_request_id),
        )

    def _purchase_receipt_note(self, purchase_request_id: int, note: str | None) -> str:
        base = f"Purchase request #{purchase_request_id} received"
        return base if note is None else f"{base}: {note}"

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
