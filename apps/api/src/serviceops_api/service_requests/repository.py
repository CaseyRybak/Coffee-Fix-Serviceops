from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from serviceops_api.service_requests.models import ServiceRequestRecord


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
