import asyncio
from datetime import UTC, datetime

import httpx

from serviceops_api.inventory.models import CreatePartPayload
from serviceops_api.inventory.repository import SqliteInventoryRepository
from serviceops_api.inventory.use_cases import CreatePart, SetStockCount
from serviceops_api.main import create_app
from serviceops_api.owner_dashboard.sla import calculate_sla_snapshot
from serviceops_api.service_requests.repository import ServiceRequestRepository


def intake_payload(
    *,
    name: str = "Anna Petrova",
    brand: str = "Jura",
    problem: str = "Machine leaks water under the brew group.",
    urgency: str = "today",
) -> dict[str, object]:
    return {
        "customer": {
            "name": name,
            "phone": "+7 999 111-22-33",
            "telegram": "@anna_fix",
            "client_type": "coffee_shop",
        },
        "machine": {
            "brand": brand,
            "model": "E8",
            "location_type": "coffee_shop",
        },
        "problem": problem,
        "address": "Tverskaya district",
        "urgency": urgency,
    }


async def post_json(
    service_repository: ServiceRequestRepository,
    path: str,
    body: dict[str, object],
    token: str | None = None,
    inventory_repository: SqliteInventoryRepository | None = None,
) -> httpx.Response:
    app = create_app(service_request_repository=service_repository, inventory_repository=inventory_repository)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(
    service_repository: ServiceRequestRepository,
    path: str,
    token: str | None = None,
    inventory_repository: SqliteInventoryRepository | None = None,
) -> httpx.Response:
    app = create_app(service_request_repository=service_repository, inventory_repository=inventory_repository)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def staff_token(service_repository: ServiceRequestRepository, username: str, password: str) -> str:
    response = await post_json(service_repository, "/staff/login", {"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


async def create_request(service_repository: ServiceRequestRepository, body: dict[str, object]) -> str:
    response = await post_json(service_repository, "/service-requests", body)
    assert response.status_code == 201
    return str(response.json()["request_number"])


def set_request_created_at(repository: ServiceRequestRepository, request_number: str, created_at: str) -> None:
    with repository._connection:
        repository._connection.execute(
            "UPDATE service_requests SET created_at = ? WHERE request_number = ?",
            (created_at, request_number),
        )
        repository._connection.execute(
            """
            UPDATE status_events
            SET created_at = ?
            WHERE service_request_id = (SELECT id FROM service_requests WHERE request_number = ?)
            """,
            (created_at, request_number),
        )


def test_sla_policy_calculates_deadline_near_deadline_and_overdue_states() -> None:
    now = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)

    overdue = calculate_sla_snapshot(
        request_number="CFX-20260617-000001",
        urgency="today",
        status="new",
        created_at="2026-06-17T03:00:00+00:00",
        now=now,
    )
    near_deadline = calculate_sla_snapshot(
        request_number="CFX-20260617-000002",
        urgency="one_two_days",
        status="repair_in_progress",
        created_at="2026-06-15T20:00:00+00:00",
        now=now,
    )
    healthy = calculate_sla_snapshot(
        request_number="CFX-20260617-000003",
        urgency="planned",
        status="visit_scheduled",
        created_at="2026-06-16T12:00:00+00:00",
        now=now,
    )
    terminal = calculate_sla_snapshot(
        request_number="CFX-20260617-000004",
        urgency="today",
        status="completed",
        created_at="2026-06-16T12:00:00+00:00",
        now=now,
    )

    assert overdue.deadline_at == "2026-06-17T11:00:00+00:00"
    assert overdue.state == "overdue"
    assert overdue.is_overdue is True
    assert overdue.is_near_deadline is False
    assert near_deadline.state == "near_deadline"
    assert near_deadline.hours_remaining == 8.0
    assert healthy.state == "on_track"
    assert terminal.state == "inactive"
    assert terminal.deadline_at is None


def test_owner_dashboard_api_is_admin_only_and_keeps_public_status_safe() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(service_repository, intake_payload()))
    admin_token = asyncio.run(staff_token(service_repository, "admin@coffeefix.local", "admin-local"))
    technician_token = asyncio.run(staff_token(service_repository, "technician@coffeefix.local", "technician-local"))

    anonymous = asyncio.run(get_json(service_repository, "/owner/dashboard"))
    forbidden = asyncio.run(get_json(service_repository, "/owner/dashboard", token=technician_token))
    dashboard = asyncio.run(get_json(service_repository, "/owner/dashboard", token=admin_token))
    public_status = asyncio.run(get_json(service_repository, f"/service-requests/{request_number}/status"))

    assert anonymous.status_code == 401
    assert forbidden.status_code == 403
    assert dashboard.status_code == 200
    assert dashboard.json()["metrics"]["new_requests"] == 1
    public_text = str(public_status.json())
    assert "sla" not in public_text.lower()
    assert "overdue" not in public_text.lower()
    assert "technician_workload" not in public_text
    assert "low_stock" not in public_text


def test_owner_dashboard_metrics_and_daily_report_payload() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    inventory_repository = SqliteInventoryRepository.in_memory()
    overdue = asyncio.run(
        create_request(
            service_repository,
            intake_payload(name="Overdue", problem="No coffee flow after descaling", urgency="today"),
        )
    )
    waiting = asyncio.run(
        create_request(
            service_repository,
            intake_payload(name="Waiting", brand="Saeco", problem="No coffee flow and loud pump", urgency="one_two_days"),
        )
    )
    completed = asyncio.run(
        create_request(
            service_repository,
            intake_payload(name="Completed", brand="Gaggia", problem="Steam wand leaks", urgency="planned"),
        )
    )
    near = asyncio.run(
        create_request(
            service_repository,
            intake_payload(name="Near", brand="Jura", problem="Grinder blocked with error", urgency="one_two_days"),
        )
    )
    set_request_created_at(service_repository, overdue, "2026-06-17T03:00:00+00:00")
    set_request_created_at(service_repository, waiting, "2026-06-16T09:00:00+00:00")
    set_request_created_at(service_repository, completed, "2026-06-17T08:00:00+00:00")
    set_request_created_at(service_repository, near, "2026-06-15T20:00:00+00:00")
    service_repository.add_status_event(waiting, "waiting_for_parts", "Ожидаем запчасти", "Нужна поставка.", "technician")
    service_repository.assign_technician(waiting, "technician@coffeefix.local", None, None, None)
    service_repository.add_status_event(waiting, "waiting_for_parts", "Ожидаем запчасти", "Нужна поставка.", "technician")
    service_repository.add_status_event(completed, "completed", "Ремонт завершен", "Готово.", "technician")
    service_repository.add_status_event(near, "repair_in_progress", "Ремонт в работе", "Мастер работает.", "technician")
    service_repository.assign_technician(near, "technician@coffeefix.local", None, None, None)
    service_repository.add_status_event(near, "repair_in_progress", "Ремонт в работе", "Мастер работает.", "technician")
    part = CreatePart(inventory_repository).execute(CreatePartPayload(sku="FLOW-METER", name="Flow meter", unit="pcs"))
    SetStockCount(inventory_repository).execute(part.part_id, quantity_on_hand=1, low_stock_threshold=2)
    admin_token = asyncio.run(staff_token(service_repository, "admin@coffeefix.local", "admin-local"))

    dashboard = asyncio.run(
        get_json(service_repository, "/owner/dashboard?now=2026-06-17T12:00:00+00:00", token=admin_token, inventory_repository=inventory_repository)
    )
    daily_report = asyncio.run(
        get_json(service_repository, "/owner/daily-report?now=2026-06-17T12:00:00+00:00", token=admin_token, inventory_repository=inventory_repository)
    )

    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["metrics"] == {
        "total_requests": 4,
        "new_requests": 1,
        "in_progress_requests": 2,
        "waiting_for_parts_requests": 1,
        "completed_requests": 1,
        "overdue_requests": 1,
        "near_deadline_requests": 1,
    }
    assert [risk["request_number"] for risk in body["sla_risks"]] == [overdue, near]
    assert body["technician_workload"] == [
        {
            "technician_identifier": "technician@coffeefix.local",
            "active_requests": 2,
            "scheduled_visits": 0,
            "waiting_for_parts": 1,
        }
    ]
    assert body["top_issue_groups"][0] == {"label": "no coffee flow", "count": 2}
    assert body["low_stock_risk"][0]["sku"] == "FLOW-METER"
    assert body["low_stock_risk"][0]["available_quantity"] == 1
    assert daily_report.status_code == 200
    assert daily_report.json()["report_date"] == "2026-06-17"
    assert daily_report.json()["summary"] == body["metrics"]
    assert "Всего заявок: 4" in daily_report.json()["highlights"]
    assert daily_report.json()["dashboard_url"] == "/owner"
