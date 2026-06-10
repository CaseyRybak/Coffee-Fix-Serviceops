from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from serviceops_api.service_requests.models import ServiceRequestRecord


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
MIGRATION_PATH = MIGRATIONS_DIR / "0001_service_request_intake.sql"
TECHNICIAN_INVENTORY_MIGRATION_PATH = MIGRATIONS_DIR / "0004_technician_inventory.sql"


class ServiceRequestRepository:
    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    @classmethod
    def in_memory(cls) -> "ServiceRequestRepository":
        return cls(":memory:")

    def initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                telegram TEXT,
                client_type TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                brand TEXT NOT NULL,
                model TEXT,
                location_type TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS service_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                machine_id INTEGER NOT NULL REFERENCES machines(id),
                status TEXT NOT NULL,
                problem TEXT NOT NULL,
                address TEXT NOT NULL,
                urgency TEXT NOT NULL,
                assigned_technician_name TEXT,
                assigned_technician_phone TEXT,
                assigned_technician_region TEXT,
                visit_window TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS attachment_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_request_id INTEGER NOT NULL REFERENCES service_requests(id),
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS status_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_request_id INTEGER NOT NULL REFERENCES service_requests(id),
                status TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS clarification_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_request_id INTEGER NOT NULL REFERENCES service_requests(id),
                question TEXT NOT NULL,
                answer TEXT,
                answered_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS public_access_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_request_id INTEGER NOT NULL UNIQUE REFERENCES service_requests(id),
                token TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS telegram_opt_ins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_request_id INTEGER NOT NULL REFERENCES service_requests(id),
                telegram TEXT,
                token TEXT NOT NULL UNIQUE,
                telegram_chat_id TEXT,
                linked_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS internal_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_request_id INTEGER NOT NULL REFERENCES service_requests(id),
                note TEXT NOT NULL,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS technician_diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT NOT NULL,
                machine_powered_on INTEGER NOT NULL,
                water_supply_checked INTEGER NOT NULL,
                leak_checked INTEGER NOT NULL,
                error_code_checked INTEGER NOT NULL,
                summary TEXT NOT NULL,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS technician_repair_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT NOT NULL,
                result TEXT NOT NULL,
                summary TEXT NOT NULL,
                next_step TEXT,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self._ensure_sqlite_dispatcher_columns()

    def _ensure_sqlite_dispatcher_columns(self) -> None:
        existing_columns = {
            str(row["name"])
            for row in self._connection.execute("PRAGMA table_info(service_requests)").fetchall()
        }
        for column_name in (
            "assigned_technician_name",
            "assigned_technician_phone",
            "assigned_technician_region",
            "visit_window",
        ):
            if column_name not in existing_columns:
                self._connection.execute(f"ALTER TABLE service_requests ADD COLUMN {column_name} TEXT")
        telegram_columns = {
            str(row["name"])
            for row in self._connection.execute("PRAGMA table_info(telegram_opt_ins)").fetchall()
        }
        for column_name in ("telegram_chat_id", "linked_at"):
            if column_name not in telegram_columns:
                self._connection.execute(f"ALTER TABLE telegram_opt_ins ADD COLUMN {column_name} TEXT")

    def next_sequence(self) -> int:
        row = self._connection.execute("SELECT COUNT(*) AS count FROM service_requests").fetchone()
        return int(row["count"]) + 1

    def save(self, record: ServiceRequestRecord) -> None:
        with self._connection:
            customer = record.customer
            customer_cursor = self._connection.execute(
                """
                INSERT INTO customers (name, phone, telegram, client_type)
                VALUES (?, ?, ?, ?)
                """,
                (customer.name, customer.phone, customer.telegram, customer.client_type),
            )
            customer_id = int(customer_cursor.lastrowid)

            machine = record.machine
            machine_cursor = self._connection.execute(
                """
                INSERT INTO machines (customer_id, brand, model, location_type)
                VALUES (?, ?, ?, ?)
                """,
                (customer_id, machine.brand, machine.model, machine.location_type),
            )
            machine_id = int(machine_cursor.lastrowid)

            request_cursor = self._connection.execute(
                """
                INSERT INTO service_requests (
                    request_number, customer_id, machine_id, status, problem, address, urgency
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.request_number,
                    customer_id,
                    machine_id,
                    record.status,
                    record.problem,
                    record.address,
                    record.urgency,
                ),
            )
            request_id = int(request_cursor.lastrowid)

            for attachment in record.attachment_metadata:
                self._connection.execute(
                    """
                    INSERT INTO attachment_metadata (
                        service_request_id, filename, content_type, size_bytes
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        request_id,
                        attachment.filename,
                        attachment.content_type,
                        attachment.size_bytes,
                    ),
                )

            self._connection.execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    record.status,
                    "Заявка создана",
                    "Мы получили обращение и передали его диспетчеру.",
                    "system",
                ),
            )
            self._connection.execute(
                """
                INSERT INTO public_access_tokens (service_request_id, token)
                VALUES (?, ?)
                """,
                (request_id, self._new_token("status")),
            )

    def get_request_snapshot(self, request_number: str) -> dict[str, Any]:
        request = self._connection.execute(
            """
            SELECT
                sr.request_number,
                sr.status,
                sr.problem,
                sr.address,
                sr.urgency,
                c.name,
                c.phone,
                c.telegram,
                c.client_type,
                m.brand,
                m.model,
                m.location_type
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            WHERE sr.request_number = ?
            """,
            (request_number,),
        ).fetchone()
        if request is None:
            raise KeyError(request_number)

        attachments = self._connection.execute(
            """
            SELECT am.filename, am.content_type, am.size_bytes
            FROM attachment_metadata am
            JOIN service_requests sr ON sr.id = am.service_request_id
            WHERE sr.request_number = ?
            ORDER BY am.id
            """,
            (request_number,),
        ).fetchall()

        return {
            "request": {
                "request_number": request["request_number"],
                "status": request["status"],
                "problem": request["problem"],
                "address": request["address"],
                "urgency": request["urgency"],
            },
            "customer": {
                "name": request["name"],
                "phone": request["phone"],
                "telegram": request["telegram"],
                "client_type": request["client_type"],
                "telegram_chat_id": self._latest_telegram_chat_id(request_number),
            },
            "machine": {
                "brand": request["brand"],
                "model": request["model"],
                "location_type": request["location_type"],
            },
            "attachments": [
                {
                    "filename": attachment["filename"],
                    "content_type": attachment["content_type"],
                    "size_bytes": attachment["size_bytes"],
                }
                for attachment in attachments
            ],
        }

    def add_status_event(
        self,
        request_number: str,
        status: str,
        title: str,
        description: str,
        actor: str,
    ) -> None:
        request_id = self._get_request_id(request_number)
        with self._connection:
            self._connection.execute(
                "UPDATE service_requests SET status = ? WHERE id = ?",
                (status, request_id),
            )
            self._connection.execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, status, title, description, actor),
            )

    def ask_clarification(self, request_number: str, question: str) -> int:
        request_id = self._get_request_id(request_number)
        with self._connection:
            self._connection.execute(
                "UPDATE service_requests SET status = ? WHERE id = ?",
                ("needs_clarification", request_id),
            )
            cursor = self._connection.execute(
                """
                INSERT INTO clarification_questions (service_request_id, question)
                VALUES (?, ?)
                """,
                (request_id, question),
            )
            self._connection.execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    "needs_clarification",
                    "Нужно уточнить детали",
                    "Диспетчер оставил вопрос на странице статуса.",
                    "dispatcher",
                ),
            )
        return int(cursor.lastrowid)

    def ensure_public_access_token(self, request_number: str) -> str:
        request_id = self._get_request_id(request_number)
        existing = self._connection.execute(
            """
            SELECT token
            FROM public_access_tokens
            WHERE service_request_id = ?
            """,
            (request_id,),
        ).fetchone()
        if existing is not None:
            return str(existing["token"])

        token = self._new_token("status")
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO public_access_tokens (service_request_id, token)
                VALUES (?, ?)
                """,
                (request_id, token),
            )
        return token

    def get_public_status_by_request_number(self, request_number: str) -> dict[str, Any]:
        return self._get_public_status("sr.request_number = ?", request_number)

    def get_public_status_by_token(self, token: str) -> dict[str, Any]:
        return self._get_public_status("pat.token = ?", token)

    def record_customer_answer(self, request_number: str, question_id: int, answer: str) -> str:
        request_id = self._get_request_id(request_number)
        question = self._connection.execute(
            """
            SELECT id
            FROM clarification_questions
            WHERE id = ? AND service_request_id = ?
            """,
            (question_id, request_id),
        ).fetchone()
        if question is None:
            raise KeyError(str(question_id))

        with self._connection:
            self._connection.execute(
                """
                UPDATE clarification_questions
                SET answer = ?, answered_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (answer, question_id),
            )
            self._connection.execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    "needs_clarification",
                    "Клиент ответил на уточнение",
                    "Ответ сохранен и доступен диспетчеру.",
                    "customer",
                ),
            )
        return self._get_request_status(request_number)

    def create_telegram_opt_in(self, request_number: str, telegram: str | None) -> dict[str, Any]:
        request_id = self._get_request_id(request_number)
        token = self._new_token("tg")
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO telegram_opt_ins (service_request_id, telegram, token)
                VALUES (?, ?, ?)
                """,
                (request_id, telegram, token),
            )
        return {
            "request_number": request_number,
            "telegram": telegram,
            "token": token,
            "link": f"https://t.me/coffeefix_service_bot?start={token}",
        }

    def link_telegram_opt_in(self, token: str, chat_id: str, username: str | None) -> dict[str, Any]:
        row = self._connection.execute(
            """
            SELECT
                toi.id,
                sr.request_number,
                sr.status,
                c.name AS customer_name,
                m.brand,
                m.model,
                pat.token AS public_token
            FROM telegram_opt_ins toi
            JOIN service_requests sr ON sr.id = toi.service_request_id
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            JOIN public_access_tokens pat ON pat.service_request_id = sr.id
            WHERE toi.token = ?
            """,
            (token,),
        ).fetchone()
        if row is None:
            raise KeyError(token)
        with self._connection:
            self._connection.execute(
                """
                UPDATE telegram_opt_ins
                SET telegram_chat_id = ?, telegram = COALESCE(?, telegram), linked_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (chat_id, f"@{username}" if username else None, row["id"]),
            )
        model = row["model"]
        return {
            "request_number": row["request_number"],
            "status": row["status"],
            "customer_name": row["customer_name"],
            "machine_label": f"{row['brand']}{f' {model}' if model else ''}",
            "public_status_url": f"/status/{row['public_token']}",
        }

    def list_dispatcher_requests(self) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT
                sr.request_number,
                sr.status,
                sr.urgency,
                sr.address,
                sr.created_at,
                c.name AS customer_name,
                c.phone AS customer_phone,
                m.brand,
                m.model,
                (
                    SELECT se.title
                    FROM status_events se
                    WHERE se.service_request_id = sr.id
                    ORDER BY se.id DESC
                    LIMIT 1
                ) AS latest_event_title
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            ORDER BY sr.id DESC
            """
        ).fetchall()
        return [self._dispatcher_list_item(row) for row in rows]

    def get_dispatcher_request(self, request_number: str) -> dict[str, Any]:
        request = self._connection.execute(
            """
            SELECT
                sr.id,
                sr.request_number,
                sr.status,
                sr.problem,
                sr.address,
                sr.urgency,
                sr.created_at,
                sr.assigned_technician_name,
                sr.assigned_technician_phone,
                sr.assigned_technician_region,
                sr.visit_window,
                c.name,
                c.phone,
                c.telegram,
                c.client_type,
                m.brand,
                m.model,
                m.location_type
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            WHERE sr.request_number = ?
            """,
            (request_number,),
        ).fetchone()
        if request is None:
            raise KeyError(request_number)
        return self._dispatcher_detail(request)

    def update_status(self, request_number: str, status: str, title: str, description: str, actor: str) -> str:
        self.add_status_event(request_number, status, title, description, actor)
        return self._get_request_status(request_number)

    def assign_technician(
        self,
        request_number: str,
        technician_name: str,
        technician_phone: str | None,
        technician_region: str | None,
        visit_window: str | None,
    ) -> str:
        request_id = self._get_request_id(request_number)
        status = "visit_scheduled" if visit_window else "technician_assigned"
        title = "Визит запланирован" if visit_window else "Мастер назначен"
        description = "Диспетчер назначил мастера и обновил следующий шаг по заявке."
        with self._connection:
            self._connection.execute(
                """
                UPDATE service_requests
                SET
                    status = ?,
                    assigned_technician_name = ?,
                    assigned_technician_phone = ?,
                    assigned_technician_region = ?,
                    visit_window = ?
                WHERE id = ?
                """,
                (status, technician_name, technician_phone, technician_region, visit_window, request_id),
            )
            self._connection.execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, status, title, description, "dispatcher"),
            )
        return status

    def save_internal_note(self, request_number: str, note: str, actor: str) -> str:
        request_id = self._get_request_id(request_number)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO internal_notes (service_request_id, note, actor)
                VALUES (?, ?, ?)
                """,
                (request_id, note, actor),
            )
        return self._get_request_status(request_number)

    def list_requests_for_technician(self, technician_identifier: str) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT
                sr.request_number,
                sr.status,
                sr.urgency,
                sr.address,
                sr.visit_window,
                c.name AS customer_name,
                m.brand,
                m.model,
                (
                    SELECT se.title
                    FROM status_events se
                    WHERE se.service_request_id = sr.id
                    ORDER BY se.id DESC
                    LIMIT 1
                ) AS latest_event_title
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            WHERE sr.assigned_technician_name = ?
            ORDER BY sr.id DESC
            """,
            (technician_identifier,),
        ).fetchall()
        return [
            {
                "request_number": row["request_number"],
                "status": row["status"],
                "customer_name": row["customer_name"],
                "machine_label": f"{row['brand']}{f' {row['model']}' if row['model'] else ''}",
                "urgency": row["urgency"],
                "address": row["address"],
                "visit_window": row["visit_window"],
                "latest_event_title": row["latest_event_title"] or "",
            }
            for row in rows
        ]

    def get_technician_request(self, request_number: str, technician_identifier: str) -> dict[str, Any]:
        row = self._connection.execute(
            """
            SELECT
                sr.request_number,
                sr.status,
                sr.problem,
                sr.address,
                sr.urgency,
                sr.visit_window,
                c.name AS customer_name,
                c.phone AS customer_phone,
                m.brand,
                m.model
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            WHERE sr.request_number = ? AND sr.assigned_technician_name = ?
            """,
            (request_number, technician_identifier),
        ).fetchone()
        if row is None:
            raise KeyError(request_number)
        diagnosis = self._latest_technician_diagnosis(request_number)
        repair_result = self._latest_technician_repair_result(request_number)
        return {
            "request_number": row["request_number"],
            "status": row["status"],
            "customer_name": row["customer_name"],
            "customer_phone": row["customer_phone"],
            "machine_label": f"{row['brand']}{f' {row['model']}' if row['model'] else ''}",
            "problem": row["problem"],
            "address": row["address"],
            "urgency": row["urgency"],
            "visit_window": row["visit_window"],
            "diagnosis": diagnosis,
            "repair_result": repair_result,
        }

    def record_technician_diagnosis(
        self,
        request_number: str,
        technician_identifier: str,
        checklist: dict[str, bool],
        summary: str,
        actor: str,
    ) -> str:
        self.get_technician_request(request_number, technician_identifier)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO technician_diagnoses (
                    request_number, machine_powered_on, water_supply_checked, leak_checked, error_code_checked,
                    summary, actor
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_number,
                    int(checklist["machine_powered_on"]),
                    int(checklist["water_supply_checked"]),
                    int(checklist["leak_checked"]),
                    int(checklist["error_code_checked"]),
                    summary,
                    actor,
                ),
            )
        self.add_status_event(
            request_number=request_number,
            status="diagnostics",
            title="Диагностика начата",
            description="Мастер проверяет кофемашину и фиксирует результат диагностики.",
            actor=actor,
        )
        return self._get_request_status(request_number)

    def record_technician_result(
        self,
        request_number: str,
        technician_identifier: str,
        result: str,
        summary: str,
        next_step: str | None,
        actor: str,
    ) -> str:
        self.get_technician_request(request_number, technician_identifier)
        status = "completed" if result == "completed" else "waiting_for_parts" if result == "waiting_for_parts" else "repair_in_progress"
        title = "Ремонт завершен" if status == "completed" else "Ожидаем запчасти" if status == "waiting_for_parts" else "Нужен повторный шаг"
        description = "Мастер обновил результат выезда по заявке."
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO technician_repair_results (request_number, result, summary, next_step, actor)
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_number, result, summary, next_step, actor),
            )
        self.add_status_event(request_number, status, title, description, actor)
        return self._get_request_status(request_number)

    def record_technician_parts_used_status(
        self,
        request_number: str,
        technician_identifier: str,
        actor: str,
    ) -> str:
        self.get_technician_request(request_number, technician_identifier)
        self.add_status_event(
            request_number=request_number,
            status="repair_in_progress",
            title="Запчасти использованы",
            description="Мастер использовал запчасти и продолжает ремонт.",
            actor=actor,
        )
        return self._get_request_status(request_number)

    def _latest_technician_diagnosis(self, request_number: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM technician_diagnoses
            WHERE request_number = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (request_number,),
        ).fetchone()
        if row is None:
            return None
        return {
            "machine_powered_on": bool(row["machine_powered_on"]),
            "water_supply_checked": bool(row["water_supply_checked"]),
            "leak_checked": bool(row["leak_checked"]),
            "error_code_checked": bool(row["error_code_checked"]),
            "summary": row["summary"],
            "actor": row["actor"],
            "created_at": row["created_at"],
        }

    def _latest_technician_repair_result(self, request_number: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM technician_repair_results
            WHERE request_number = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (request_number,),
        ).fetchone()
        if row is None:
            return None
        return {
            "result": row["result"],
            "summary": row["summary"],
            "next_step": row["next_step"],
            "actor": row["actor"],
            "created_at": row["created_at"],
        }

    def _get_request_id(self, request_number: str) -> int:
        row = self._connection.execute(
            "SELECT id FROM service_requests WHERE request_number = ?",
            (request_number,),
        ).fetchone()
        if row is None:
            raise KeyError(request_number)
        return int(row["id"])

    def _get_request_status(self, request_number: str) -> str:
        row = self._connection.execute(
            "SELECT status FROM service_requests WHERE request_number = ?",
            (request_number,),
        ).fetchone()
        if row is None:
            raise KeyError(request_number)
        return str(row["status"])

    def _dispatcher_list_item(self, row: sqlite3.Row) -> dict[str, Any]:
        model = row["model"]
        return {
            "request_number": row["request_number"],
            "status": row["status"],
            "customer_name": row["customer_name"],
            "customer_phone": row["customer_phone"],
            "machine_label": f"{row['brand']}{f' {model}' if model else ''}",
            "urgency": row["urgency"],
            "address": row["address"],
            "created_at": row["created_at"],
            "latest_event_title": row["latest_event_title"] or "",
        }

    def _dispatcher_detail(self, request: sqlite3.Row) -> dict[str, Any]:
        events = self._connection.execute(
            """
            SELECT status, title, description, actor, created_at
            FROM status_events
            WHERE service_request_id = ?
            ORDER BY id
            """,
            (request["id"],),
        ).fetchall()
        clarification = self._connection.execute(
            """
            SELECT id, question, answer, answered_at
            FROM clarification_questions
            WHERE service_request_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (request["id"],),
        ).fetchone()
        notes = self._connection.execute(
            """
            SELECT note, actor, created_at
            FROM internal_notes
            WHERE service_request_id = ?
            ORDER BY id DESC
            """,
            (request["id"],),
        ).fetchall()
        return {
            "request_number": request["request_number"],
            "status": request["status"],
            "customer": {
                "name": request["name"],
                "phone": request["phone"],
                "telegram": request["telegram"],
                "client_type": request["client_type"],
            },
            "machine": {
                "brand": request["brand"],
                "model": request["model"],
                "location_type": request["location_type"],
            },
            "problem": request["problem"],
            "address": request["address"],
            "urgency": request["urgency"],
            "created_at": request["created_at"],
            "timeline": [
                {
                    "status": event["status"],
                    "title": event["title"],
                    "description": event["description"],
                    "actor": event["actor"],
                    "created_at": event["created_at"],
                }
                for event in events
            ],
            "clarification": None
            if clarification is None
            else {
                "question_id": clarification["id"],
                "question": clarification["question"],
                "answer": clarification["answer"],
                "answered_at": clarification["answered_at"],
            },
            "assignment": {
                "technician_name": request["assigned_technician_name"],
                "technician_phone": request["assigned_technician_phone"],
                "technician_region": request["assigned_technician_region"],
                "visit_window": request["visit_window"],
            },
            "internal_notes": [
                {
                    "note": note["note"],
                    "actor": note["actor"],
                    "created_at": note["created_at"],
                }
                for note in notes
            ],
        }

    def _get_public_status(self, predicate: str, value: str) -> dict[str, Any]:
        request = self._connection.execute(
            f"""
            SELECT
                sr.id,
                sr.request_number,
                sr.status,
                sr.problem,
                c.name,
                c.phone,
                c.telegram,
                m.brand,
                m.model,
                pat.token AS public_token
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            JOIN public_access_tokens pat ON pat.service_request_id = sr.id
            WHERE {predicate}
            """,
            (value,),
        ).fetchone()
        if request is None:
            raise KeyError(value)

        events = self._connection.execute(
            """
            SELECT status, title, description, actor, created_at
            FROM status_events
            WHERE service_request_id = ?
            ORDER BY id
            """,
            (request["id"],),
        ).fetchall()
        clarification = self._connection.execute(
            """
            SELECT id, question, answer, answered_at
            FROM clarification_questions
            WHERE service_request_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (request["id"],),
        ).fetchone()
        opt_in = self._connection.execute(
            """
            SELECT id
            FROM telegram_opt_ins
            WHERE service_request_id = ?
            LIMIT 1
            """,
            (request["id"],),
        ).fetchone()

        return {
            "request_number": request["request_number"],
            "public_token": request["public_token"],
            "status": request["status"],
            "customer": {
                "name": request["name"],
                "phone_masked": self._mask_phone(str(request["phone"])),
                "telegram": request["telegram"],
            },
            "machine": {
                "brand": request["brand"],
                "model": request["model"],
            },
            "problem_summary": request["problem"],
            "timeline": [
                {
                    "status": event["status"],
                    "title": event["title"],
                    "description": event["description"],
                    "actor": event["actor"],
                    "created_at": event["created_at"],
                }
                for event in events
            ],
            "clarification": None
            if clarification is None
            else {
                "question_id": clarification["id"],
                "question": clarification["question"],
                "answer": clarification["answer"],
                "answered_at": clarification["answered_at"],
            },
            "telegram_opt_in": {
                "enabled": opt_in is not None,
                "link": f"/service-requests/{request['request_number']}/telegram-opt-in",
            },
        }

    def _new_token(self, prefix: str) -> str:
        return f"{prefix}_{secrets.token_urlsafe(18)}"

    def _mask_phone(self, phone: str) -> str:
        if len(phone) < 9:
            return "***"
        return f"{phone[:-9]}***-**-{phone[-2:]}"

    def _latest_telegram_chat_id(self, request_number: str) -> str | None:
        row = self._connection.execute(
            """
            SELECT toi.telegram_chat_id
            FROM telegram_opt_ins toi
            JOIN service_requests sr ON sr.id = toi.service_request_id
            WHERE sr.request_number = ? AND toi.telegram_chat_id IS NOT NULL
            ORDER BY toi.id DESC
            LIMIT 1
            """,
            (request_number,),
        ).fetchone()
        return None if row is None else str(row["telegram_chat_id"])


class PostgresServiceRequestRepository:
    def __init__(self, database_url: str, initialize: bool = True) -> None:
        self._database_url = self._normalize_database_url(database_url)
        self._connection: psycopg.Connection[dict[str, Any]] | None = None
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        self._connect().execute(MIGRATION_PATH.read_text(encoding="utf-8"))
        if TECHNICIAN_INVENTORY_MIGRATION_PATH.exists():
            self._connect().execute(TECHNICIAN_INVENTORY_MIGRATION_PATH.read_text(encoding="utf-8"))
        self._connect().commit()

    def next_sequence(self) -> int:
        row = self._connect().execute("SELECT COUNT(*) AS count FROM service_requests").fetchone()
        if row is None:
            return 1
        return int(row["count"]) + 1

    def save(self, record: ServiceRequestRecord) -> None:
        connection = self._connect()
        with connection.transaction():
            customer = record.customer
            customer_row = connection.execute(
                """
                INSERT INTO customers (name, phone, telegram, client_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (customer.name, customer.phone, customer.telegram, customer.client_type),
            ).fetchone()
            if customer_row is None:
                raise RuntimeError("customer insert did not return an id")
            customer_id = int(customer_row["id"])

            machine = record.machine
            machine_row = connection.execute(
                """
                INSERT INTO machines (customer_id, brand, model, location_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (customer_id, machine.brand, machine.model, machine.location_type),
            ).fetchone()
            if machine_row is None:
                raise RuntimeError("machine insert did not return an id")
            machine_id = int(machine_row["id"])

            request_row = connection.execute(
                """
                INSERT INTO service_requests (
                    request_number, customer_id, machine_id, status, problem, address, urgency
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    record.request_number,
                    customer_id,
                    machine_id,
                    record.status,
                    record.problem,
                    record.address,
                    record.urgency,
                ),
            ).fetchone()
            if request_row is None:
                raise RuntimeError("service request insert did not return an id")
            request_id = int(request_row["id"])

            for attachment in record.attachment_metadata:
                connection.execute(
                    """
                    INSERT INTO attachment_metadata (
                        service_request_id, filename, content_type, size_bytes
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        request_id,
                        attachment.filename,
                        attachment.content_type,
                        attachment.size_bytes,
                    ),
                )

            connection.execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    record.status,
                    "Заявка создана",
                    "Мы получили обращение и передали его диспетчеру.",
                    "system",
                ),
            )
            connection.execute(
                """
                INSERT INTO public_access_tokens (service_request_id, token)
                VALUES (%s, %s)
                """,
                (request_id, self._new_token("status")),
            )

    def get_request_snapshot(self, request_number: str) -> dict[str, Any]:
        request = self._connect().execute(
            """
            SELECT
                sr.request_number,
                sr.status,
                sr.problem,
                sr.address,
                sr.urgency,
                c.name,
                c.phone,
                c.telegram,
                c.client_type,
                m.brand,
                m.model,
                m.location_type
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            WHERE sr.request_number = %s
            """,
            (request_number,),
        ).fetchone()
        if request is None:
            raise KeyError(request_number)

        attachments = self._connect().execute(
            """
            SELECT am.filename, am.content_type, am.size_bytes
            FROM attachment_metadata am
            JOIN service_requests sr ON sr.id = am.service_request_id
            WHERE sr.request_number = %s
            ORDER BY am.id
            """,
            (request_number,),
        ).fetchall()

        return {
            "request": {
                "request_number": request["request_number"],
                "status": request["status"],
                "problem": request["problem"],
                "address": request["address"],
                "urgency": request["urgency"],
            },
            "customer": {
                "name": request["name"],
                "phone": request["phone"],
                "telegram": request["telegram"],
                "client_type": request["client_type"],
                "telegram_chat_id": self._latest_telegram_chat_id(request_number),
            },
            "machine": {
                "brand": request["brand"],
                "model": request["model"],
                "location_type": request["location_type"],
            },
            "attachments": [
                {
                    "filename": attachment["filename"],
                    "content_type": attachment["content_type"],
                    "size_bytes": attachment["size_bytes"],
                }
                for attachment in attachments
            ],
        }

    def add_status_event(
        self,
        request_number: str,
        status: str,
        title: str,
        description: str,
        actor: str,
    ) -> None:
        request_id = self._get_request_id(request_number)
        with self._connect().transaction():
            self._connect().execute(
                "UPDATE service_requests SET status = %s WHERE id = %s",
                (status, request_id),
            )
            self._connect().execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (request_id, status, title, description, actor),
            )

    def ask_clarification(self, request_number: str, question: str) -> int:
        request_id = self._get_request_id(request_number)
        with self._connect().transaction():
            self._connect().execute(
                "UPDATE service_requests SET status = %s WHERE id = %s",
                ("needs_clarification", request_id),
            )
            row = self._connect().execute(
                """
                INSERT INTO clarification_questions (service_request_id, question)
                VALUES (%s, %s)
                RETURNING id
                """,
                (request_id, question),
            ).fetchone()
            if row is None:
                raise RuntimeError("clarification insert did not return an id")
            self._connect().execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    "needs_clarification",
                    "Нужно уточнить детали",
                    "Диспетчер оставил вопрос на странице статуса.",
                    "dispatcher",
                ),
            )
        return int(row["id"])

    def ensure_public_access_token(self, request_number: str) -> str:
        request_id = self._get_request_id(request_number)
        existing = self._connect().execute(
            """
            SELECT token
            FROM public_access_tokens
            WHERE service_request_id = %s
            """,
            (request_id,),
        ).fetchone()
        if existing is not None:
            return str(existing["token"])

        token = self._new_token("status")
        self._connect().execute(
            """
            INSERT INTO public_access_tokens (service_request_id, token)
            VALUES (%s, %s)
            """,
            (request_id, token),
        )
        self._connect().commit()
        return token

    def get_public_status_by_request_number(self, request_number: str) -> dict[str, Any]:
        return self._get_public_status("sr.request_number = %s", request_number)

    def get_public_status_by_token(self, token: str) -> dict[str, Any]:
        return self._get_public_status("pat.token = %s", token)

    def record_customer_answer(self, request_number: str, question_id: int, answer: str) -> str:
        request_id = self._get_request_id(request_number)
        question = self._connect().execute(
            """
            SELECT id
            FROM clarification_questions
            WHERE id = %s AND service_request_id = %s
            """,
            (question_id, request_id),
        ).fetchone()
        if question is None:
            raise KeyError(str(question_id))

        with self._connect().transaction():
            self._connect().execute(
                """
                UPDATE clarification_questions
                SET answer = %s, answered_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (answer, question_id),
            )
            self._connect().execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    "needs_clarification",
                    "Клиент ответил на уточнение",
                    "Ответ сохранен и доступен диспетчеру.",
                    "customer",
                ),
            )
        return self._get_request_status(request_number)

    def create_telegram_opt_in(self, request_number: str, telegram: str | None) -> dict[str, Any]:
        request_id = self._get_request_id(request_number)
        token = self._new_token("tg")
        self._connect().execute(
            """
            INSERT INTO telegram_opt_ins (service_request_id, telegram, token)
            VALUES (%s, %s, %s)
            """,
            (request_id, telegram, token),
        )
        self._connect().commit()
        return {
            "request_number": request_number,
            "telegram": telegram,
            "token": token,
            "link": f"https://t.me/coffeefix_service_bot?start={token}",
        }

    def link_telegram_opt_in(self, token: str, chat_id: str, username: str | None) -> dict[str, Any]:
        row = self._connect().execute(
            """
            SELECT
                toi.id,
                sr.request_number,
                sr.status,
                c.name AS customer_name,
                m.brand,
                m.model,
                pat.token AS public_token
            FROM telegram_opt_ins toi
            JOIN service_requests sr ON sr.id = toi.service_request_id
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            JOIN public_access_tokens pat ON pat.service_request_id = sr.id
            WHERE toi.token = %s
            """,
            (token,),
        ).fetchone()
        if row is None:
            raise KeyError(token)
        self._connect().execute(
            """
            UPDATE telegram_opt_ins
            SET telegram_chat_id = %s, telegram = COALESCE(%s, telegram), linked_at = now()
            WHERE id = %s
            """,
            (chat_id, f"@{username}" if username else None, row["id"]),
        )
        self._connect().commit()
        model = row["model"]
        return {
            "request_number": row["request_number"],
            "status": row["status"],
            "customer_name": row["customer_name"],
            "machine_label": f"{row['brand']}{f' {model}' if model else ''}",
            "public_status_url": f"/status/{row['public_token']}",
        }

    def list_dispatcher_requests(self) -> list[dict[str, Any]]:
        rows = self._connect().execute(
            """
            SELECT
                sr.request_number,
                sr.status,
                sr.urgency,
                sr.address,
                sr.created_at,
                c.name AS customer_name,
                c.phone AS customer_phone,
                m.brand,
                m.model,
                (
                    SELECT se.title
                    FROM status_events se
                    WHERE se.service_request_id = sr.id
                    ORDER BY se.id DESC
                    LIMIT 1
                ) AS latest_event_title
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            ORDER BY sr.id DESC
            """
        ).fetchall()
        return [self._dispatcher_list_item(row) for row in rows]

    def get_dispatcher_request(self, request_number: str) -> dict[str, Any]:
        request = self._connect().execute(
            """
            SELECT
                sr.id,
                sr.request_number,
                sr.status,
                sr.problem,
                sr.address,
                sr.urgency,
                sr.created_at,
                sr.assigned_technician_name,
                sr.assigned_technician_phone,
                sr.assigned_technician_region,
                sr.visit_window,
                c.name,
                c.phone,
                c.telegram,
                c.client_type,
                m.brand,
                m.model,
                m.location_type
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            WHERE sr.request_number = %s
            """,
            (request_number,),
        ).fetchone()
        if request is None:
            raise KeyError(request_number)
        return self._dispatcher_detail(request)

    def update_status(self, request_number: str, status: str, title: str, description: str, actor: str) -> str:
        self.add_status_event(request_number, status, title, description, actor)
        return self._get_request_status(request_number)

    def assign_technician(
        self,
        request_number: str,
        technician_name: str,
        technician_phone: str | None,
        technician_region: str | None,
        visit_window: str | None,
    ) -> str:
        request_id = self._get_request_id(request_number)
        status = "visit_scheduled" if visit_window else "technician_assigned"
        title = "Визит запланирован" if visit_window else "Мастер назначен"
        description = "Диспетчер назначил мастера и обновил следующий шаг по заявке."
        with self._connect().transaction():
            self._connect().execute(
                """
                UPDATE service_requests
                SET
                    status = %s,
                    assigned_technician_name = %s,
                    assigned_technician_phone = %s,
                    assigned_technician_region = %s,
                    visit_window = %s
                WHERE id = %s
                """,
                (status, technician_name, technician_phone, technician_region, visit_window, request_id),
            )
            self._connect().execute(
                """
                INSERT INTO status_events (
                    service_request_id, status, title, description, actor
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (request_id, status, title, description, "dispatcher"),
            )
        return status

    def save_internal_note(self, request_number: str, note: str, actor: str) -> str:
        request_id = self._get_request_id(request_number)
        self._connect().execute(
            """
            INSERT INTO internal_notes (service_request_id, note, actor)
            VALUES (%s, %s, %s)
            """,
            (request_id, note, actor),
        )
        self._connect().commit()
        return self._get_request_status(request_number)

    def list_requests_for_technician(self, technician_identifier: str) -> list[dict[str, Any]]:
        rows = self._connect().execute(
            """
            SELECT
                sr.request_number,
                sr.status,
                sr.urgency,
                sr.address,
                sr.visit_window,
                c.name AS customer_name,
                m.brand,
                m.model,
                (
                    SELECT se.title
                    FROM status_events se
                    WHERE se.service_request_id = sr.id
                    ORDER BY se.id DESC
                    LIMIT 1
                ) AS latest_event_title
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            WHERE sr.assigned_technician_name = %s
            ORDER BY sr.id DESC
            """,
            (technician_identifier,),
        ).fetchall()
        return [
            {
                "request_number": row["request_number"],
                "status": row["status"],
                "customer_name": row["customer_name"],
                "machine_label": f"{row['brand']}{f' {row['model']}' if row['model'] else ''}",
                "urgency": row["urgency"],
                "address": row["address"],
                "visit_window": row["visit_window"],
                "latest_event_title": row["latest_event_title"] or "",
            }
            for row in rows
        ]

    def get_technician_request(self, request_number: str, technician_identifier: str) -> dict[str, Any]:
        row = self._connect().execute(
            """
            SELECT
                sr.request_number,
                sr.status,
                sr.problem,
                sr.address,
                sr.urgency,
                sr.visit_window,
                c.name AS customer_name,
                c.phone AS customer_phone,
                m.brand,
                m.model
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            WHERE sr.request_number = %s AND sr.assigned_technician_name = %s
            """,
            (request_number, technician_identifier),
        ).fetchone()
        if row is None:
            raise KeyError(request_number)
        return {
            "request_number": row["request_number"],
            "status": row["status"],
            "customer_name": row["customer_name"],
            "customer_phone": row["customer_phone"],
            "machine_label": f"{row['brand']}{f' {row['model']}' if row['model'] else ''}",
            "problem": row["problem"],
            "address": row["address"],
            "urgency": row["urgency"],
            "visit_window": row["visit_window"],
            "diagnosis": self._latest_technician_diagnosis(request_number),
            "repair_result": self._latest_technician_repair_result(request_number),
        }

    def record_technician_diagnosis(
        self,
        request_number: str,
        technician_identifier: str,
        checklist: dict[str, bool],
        summary: str,
        actor: str,
    ) -> str:
        self.get_technician_request(request_number, technician_identifier)
        self._connect().execute(
            """
            INSERT INTO technician_diagnoses (
                request_number, machine_powered_on, water_supply_checked, leak_checked, error_code_checked,
                summary, actor
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                request_number,
                checklist["machine_powered_on"],
                checklist["water_supply_checked"],
                checklist["leak_checked"],
                checklist["error_code_checked"],
                summary,
                actor,
            ),
        )
        self._connect().commit()
        self.add_status_event(
            request_number=request_number,
            status="diagnostics",
            title="Диагностика начата",
            description="Мастер проверяет кофемашину и фиксирует результат диагностики.",
            actor=actor,
        )
        return self._get_request_status(request_number)

    def record_technician_result(
        self,
        request_number: str,
        technician_identifier: str,
        result: str,
        summary: str,
        next_step: str | None,
        actor: str,
    ) -> str:
        self.get_technician_request(request_number, technician_identifier)
        status = "completed" if result == "completed" else "waiting_for_parts" if result == "waiting_for_parts" else "repair_in_progress"
        title = "Ремонт завершен" if status == "completed" else "Ожидаем запчасти" if status == "waiting_for_parts" else "Нужен повторный шаг"
        self._connect().execute(
            """
            INSERT INTO technician_repair_results (request_number, result, summary, next_step, actor)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (request_number, result, summary, next_step, actor),
        )
        self._connect().commit()
        self.add_status_event(request_number, status, title, "Мастер обновил результат выезда по заявке.", actor)
        return self._get_request_status(request_number)

    def record_technician_parts_used_status(
        self,
        request_number: str,
        technician_identifier: str,
        actor: str,
    ) -> str:
        self.get_technician_request(request_number, technician_identifier)
        self.add_status_event(
            request_number=request_number,
            status="repair_in_progress",
            title="Запчасти использованы",
            description="Мастер использовал запчасти и продолжает ремонт.",
            actor=actor,
        )
        return self._get_request_status(request_number)

    def _latest_technician_diagnosis(self, request_number: str) -> dict[str, Any] | None:
        row = self._connect().execute(
            """
            SELECT *
            FROM technician_diagnoses
            WHERE request_number = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (request_number,),
        ).fetchone()
        if row is None:
            return None
        return {
            "machine_powered_on": row["machine_powered_on"],
            "water_supply_checked": row["water_supply_checked"],
            "leak_checked": row["leak_checked"],
            "error_code_checked": row["error_code_checked"],
            "summary": row["summary"],
            "actor": row["actor"],
            "created_at": self._format_timestamp(row["created_at"]),
        }

    def _latest_technician_repair_result(self, request_number: str) -> dict[str, Any] | None:
        row = self._connect().execute(
            """
            SELECT *
            FROM technician_repair_results
            WHERE request_number = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (request_number,),
        ).fetchone()
        if row is None:
            return None
        return {
            "result": row["result"],
            "summary": row["summary"],
            "next_step": row["next_step"],
            "actor": row["actor"],
            "created_at": self._format_timestamp(row["created_at"]),
        }

    def _connect(self) -> psycopg.Connection[dict[str, Any]]:
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self._database_url, row_factory=dict_row, autocommit=True)
        return self._connection

    def _get_request_id(self, request_number: str) -> int:
        row = self._connect().execute(
            "SELECT id FROM service_requests WHERE request_number = %s",
            (request_number,),
        ).fetchone()
        if row is None:
            raise KeyError(request_number)
        return int(row["id"])

    def _get_request_status(self, request_number: str) -> str:
        row = self._connect().execute(
            "SELECT status FROM service_requests WHERE request_number = %s",
            (request_number,),
        ).fetchone()
        if row is None:
            raise KeyError(request_number)
        return str(row["status"])

    def _dispatcher_list_item(self, row: dict[str, Any]) -> dict[str, Any]:
        model = row["model"]
        return {
            "request_number": row["request_number"],
            "status": row["status"],
            "customer_name": row["customer_name"],
            "customer_phone": row["customer_phone"],
            "machine_label": f"{row['brand']}{f' {model}' if model else ''}",
            "urgency": row["urgency"],
            "address": row["address"],
            "created_at": self._format_timestamp(row["created_at"]),
            "latest_event_title": row["latest_event_title"] or "",
        }

    def _dispatcher_detail(self, request: dict[str, Any]) -> dict[str, Any]:
        events = self._connect().execute(
            """
            SELECT status, title, description, actor, created_at
            FROM status_events
            WHERE service_request_id = %s
            ORDER BY id
            """,
            (request["id"],),
        ).fetchall()
        clarification = self._connect().execute(
            """
            SELECT id, question, answer, answered_at
            FROM clarification_questions
            WHERE service_request_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (request["id"],),
        ).fetchone()
        notes = self._connect().execute(
            """
            SELECT note, actor, created_at
            FROM internal_notes
            WHERE service_request_id = %s
            ORDER BY id DESC
            """,
            (request["id"],),
        ).fetchall()
        return {
            "request_number": request["request_number"],
            "status": request["status"],
            "customer": {
                "name": request["name"],
                "phone": request["phone"],
                "telegram": request["telegram"],
                "client_type": request["client_type"],
            },
            "machine": {
                "brand": request["brand"],
                "model": request["model"],
                "location_type": request["location_type"],
            },
            "problem": request["problem"],
            "address": request["address"],
            "urgency": request["urgency"],
            "created_at": self._format_timestamp(request["created_at"]),
            "timeline": [
                {
                    "status": event["status"],
                    "title": event["title"],
                    "description": event["description"],
                    "actor": event["actor"],
                    "created_at": self._format_timestamp(event["created_at"]),
                }
                for event in events
            ],
            "clarification": None
            if clarification is None
            else {
                "question_id": clarification["id"],
                "question": clarification["question"],
                "answer": clarification["answer"],
                "answered_at": None
                if clarification["answered_at"] is None
                else self._format_timestamp(clarification["answered_at"]),
            },
            "assignment": {
                "technician_name": request["assigned_technician_name"],
                "technician_phone": request["assigned_technician_phone"],
                "technician_region": request["assigned_technician_region"],
                "visit_window": request["visit_window"],
            },
            "internal_notes": [
                {
                    "note": note["note"],
                    "actor": note["actor"],
                    "created_at": self._format_timestamp(note["created_at"]),
                }
                for note in notes
            ],
        }

    def _get_public_status(self, predicate: str, value: str) -> dict[str, Any]:
        request = self._connect().execute(
            f"""
            SELECT
                sr.id,
                sr.request_number,
                sr.status,
                sr.problem,
                c.name,
                c.phone,
                c.telegram,
                m.brand,
                m.model,
                pat.token AS public_token
            FROM service_requests sr
            JOIN customers c ON c.id = sr.customer_id
            JOIN machines m ON m.id = sr.machine_id
            JOIN public_access_tokens pat ON pat.service_request_id = sr.id
            WHERE {predicate}
            """,
            (value,),
        ).fetchone()
        if request is None:
            raise KeyError(value)

        events = self._connect().execute(
            """
            SELECT status, title, description, actor, created_at
            FROM status_events
            WHERE service_request_id = %s
            ORDER BY id
            """,
            (request["id"],),
        ).fetchall()
        clarification = self._connect().execute(
            """
            SELECT id, question, answer, answered_at
            FROM clarification_questions
            WHERE service_request_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (request["id"],),
        ).fetchone()
        opt_in = self._connect().execute(
            """
            SELECT id
            FROM telegram_opt_ins
            WHERE service_request_id = %s
            LIMIT 1
            """,
            (request["id"],),
        ).fetchone()

        return {
            "request_number": request["request_number"],
            "public_token": request["public_token"],
            "status": request["status"],
            "customer": {
                "name": request["name"],
                "phone_masked": self._mask_phone(str(request["phone"])),
                "telegram": request["telegram"],
            },
            "machine": {
                "brand": request["brand"],
                "model": request["model"],
            },
            "problem_summary": request["problem"],
            "timeline": [
                {
                    "status": event["status"],
                    "title": event["title"],
                    "description": event["description"],
                    "actor": event["actor"],
                    "created_at": self._format_timestamp(event["created_at"]),
                }
                for event in events
            ],
            "clarification": None
            if clarification is None
            else {
                "question_id": clarification["id"],
                "question": clarification["question"],
                "answer": clarification["answer"],
                "answered_at": None
                if clarification["answered_at"] is None
                else self._format_timestamp(clarification["answered_at"]),
            },
            "telegram_opt_in": {
                "enabled": opt_in is not None,
                "link": f"/service-requests/{request['request_number']}/telegram-opt-in",
            },
        }

    def _format_timestamp(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def _new_token(self, prefix: str) -> str:
        return f"{prefix}_{secrets.token_urlsafe(18)}"

    def _mask_phone(self, phone: str) -> str:
        if len(phone) < 9:
            return "***"
        return f"{phone[:-9]}***-**-{phone[-2:]}"

    def _latest_telegram_chat_id(self, request_number: str) -> str | None:
        row = self._connect().execute(
            """
            SELECT toi.telegram_chat_id
            FROM telegram_opt_ins toi
            JOIN service_requests sr ON sr.id = toi.service_request_id
            WHERE sr.request_number = %s AND toi.telegram_chat_id IS NOT NULL
            ORDER BY toi.id DESC
            LIMIT 1
            """,
            (request_number,),
        ).fetchone()
        return None if row is None else str(row["telegram_chat_id"])

    def _normalize_database_url(self, database_url: str) -> str:
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def create_service_request_repository(settings: Any, initialize: bool = True) -> ServiceRequestRepository | PostgresServiceRequestRepository:
    database_url = settings.database_url.strip()
    if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        return PostgresServiceRequestRepository(database_url, initialize=initialize)
    if database_url.startswith("sqlite:///"):
        return ServiceRequestRepository(database_url.removeprefix("sqlite:///"))
    if database_url == "sqlite:///:memory:":
        return ServiceRequestRepository.in_memory()
    if not database_url:
        return ServiceRequestRepository(settings.intake_sqlite_path)
    raise ValueError(f"Unsupported SERVICEOPS_DATABASE_URL: {database_url}")
