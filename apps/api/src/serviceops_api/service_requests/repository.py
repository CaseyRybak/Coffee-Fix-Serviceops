from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from serviceops_api.service_requests.models import ServiceRequestRecord


MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "0001_service_request_intake.sql"


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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

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


class PostgresServiceRequestRepository:
    def __init__(self, database_url: str, initialize: bool = True) -> None:
        self._database_url = self._normalize_database_url(database_url)
        self._connection: psycopg.Connection[dict[str, Any]] | None = None
        if initialize:
            self.initialize()

    def initialize(self) -> None:
        self._connect().execute(MIGRATION_PATH.read_text(encoding="utf-8"))
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
