import asyncio

import httpx
import pytest

from serviceops_api.inventory.models import CreatePartPayload
from serviceops_api.inventory.repository import SqliteInventoryRepository
from serviceops_api.inventory.use_cases import CreatePart, SetStockCount
from serviceops_api.main import create_app
from serviceops_api.notifications.repository import SqliteNotificationRepository
from serviceops_api.service_requests.repository import ServiceRequestRepository


def intake_payload(
    *,
    name: str = "Anna Petrova",
    brand: str = "Jura",
    model: str = "E8",
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
            "model": model,
            "location_type": "coffee_shop",
        },
        "problem": problem,
        "address": "Tverskaya district",
        "urgency": urgency,
    }


async def post_json(
    service_repository: ServiceRequestRepository,
    notification_repository: SqliteNotificationRepository,
    path: str,
    body: dict[str, object],
    inventory_repository: SqliteInventoryRepository | None = None,
    callback_secret: str | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=service_repository,
        notification_repository=notification_repository,
        inventory_repository=inventory_repository,
        n8n_callback_secret="callback-secret",
    )
    headers = {"X-ServiceOps-Callback-Secret": callback_secret} if callback_secret is not None else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(
    service_repository: ServiceRequestRepository,
    notification_repository: SqliteNotificationRepository,
    path: str,
    *,
    secret: str | None = "callback-secret",
    inventory_repository: SqliteInventoryRepository | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=service_repository,
        notification_repository=notification_repository,
        inventory_repository=inventory_repository,
        n8n_callback_secret="callback-secret",
    )
    headers = {"X-ServiceOps-Callback-Secret": secret} if secret is not None else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def create_request(
    service_repository: ServiceRequestRepository,
    notification_repository: SqliteNotificationRepository,
    body: dict[str, object],
) -> str:
    response = await post_json(service_repository, notification_repository, "/service-requests", body)
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


@pytest.mark.parametrize(
    "path",
    [
        "/notifications/n8n/operations/sla-reminders",
        "/notifications/n8n/operations/red-alerts",
        "/notifications/n8n/operations/owner-daily-report",
        "/notifications/n8n/operations/low-stock-alerts",
    ],
)
def test_operational_endpoints_require_n8n_callback_secret(path: str) -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()

    missing = asyncio.run(
        get_json(service_repository, notification_repository, path, secret=None)
    )
    wrong = asyncio.run(
        get_json(service_repository, notification_repository, path, secret="wrong-secret")
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401


def test_sla_and_red_alert_payloads_are_safe_and_idempotent() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    overdue = asyncio.run(
        create_request(
            service_repository,
            notification_repository,
            intake_payload(name="Overdue Client", problem="No coffee flow after descaling", urgency="today"),
        )
    )
    near = asyncio.run(
        create_request(
            service_repository,
            notification_repository,
            intake_payload(name="Near Client", brand="Saeco", problem="Grinder blocked", urgency="one_two_days"),
        )
    )
    set_request_created_at(service_repository, overdue, "2026-06-17T03:00:00+00:00")
    set_request_created_at(service_repository, near, "2026-06-15T20:00:00+00:00")
    service_repository.add_status_event(near, "repair_in_progress", "Ремонт в работе", "Мастер работает.", "technician")

    preview = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/sla-reminders?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17T12&mark_sent=false",
        )
    )
    first = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/sla-reminders?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17T12",
        )
    )
    duplicate = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/sla-reminders?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17T12",
        )
    )
    red_alert = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/red-alerts?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17T12",
        )
    )

    assert preview.status_code == 200
    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert red_alert.status_code == 200
    preview_body = preview.json()
    first_body = first.json()
    duplicate_body = duplicate.json()
    red_body = red_alert.json()
    assert preview_body["automation"] == "sla_reminder"
    assert [item["request_number"] for item in preview_body["items"]] == [near]
    assert [item["request_number"] for item in first_body["items"]] == [near]
    assert first_body["items"][0]["event_id"] == f"operational:sla_reminder:2026-06-17T12:{near}"
    assert first_body["items"][0]["dashboard_url"] == "/owner"
    assert duplicate_body["items"] == []
    assert duplicate_body["suppressed_count"] == 1
    assert [item["request_number"] for item in red_body["items"]] == [overdue]
    assert red_body["items"][0]["event_id"] == f"operational:red_alert:2026-06-17T12:{overdue}"
    assert notification_repository.list_for_request(near)[0]["event_type"] == "operational.sla_reminder"
    safe_text = str(first_body) + str(red_body)
    assert "+7 999 111-22-33" not in safe_text
    assert "telegram_chat_id" not in safe_text
    assert "Tverskaya" not in safe_text


def test_operational_failed_delivery_can_be_retried_in_same_window() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    near = asyncio.run(
        create_request(
            service_repository,
            notification_repository,
            intake_payload(name="Retry Client", brand="Saeco", problem="Grinder blocked", urgency="one_two_days"),
        )
    )
    set_request_created_at(service_repository, near, "2026-06-15T20:00:00+00:00")
    service_repository.add_status_event(near, "repair_in_progress", "Ремонт в работе", "Мастер работает.", "technician")

    first = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/sla-reminders?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17T12",
        )
    )
    event_id = first.json()["items"][0]["event_id"]
    callback = asyncio.run(
        post_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/delivery-results",
            {
                "event_id": event_id,
                "status": "failed",
                "channel": "telegram",
                "provider_message_id": "",
                "error": "temporary telegram failure",
                "attempt_count": 1,
            },
            callback_secret="callback-secret",
        )
    )
    retry = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/sla-reminders?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17T12",
        )
    )

    assert callback.status_code == 200
    assert retry.status_code == 200
    assert retry.json()["items"][0]["event_id"] == event_id
    attempt = notification_repository.list_for_request(near)[0]
    assert attempt["status"] == "queued"
    assert attempt["attempt_count"] == 2

    sent_callback = asyncio.run(
        post_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/delivery-results",
            {
                "event_id": event_id,
                "status": "sent",
                "channel": "telegram",
                "provider_message_id": "telegram-message-42",
                "attempt_count": 1,
            },
            callback_secret="callback-secret",
        )
    )

    assert sent_callback.status_code == 200
    sent_attempt = notification_repository.list_for_request(near)[0]
    assert sent_attempt["status"] == "sent"
    assert sent_attempt["attempt_count"] == 2


def test_operational_window_key_is_bounded_for_callback_safe_event_ids() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    too_long_window = "x" * 120

    response = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            f"/notifications/n8n/operations/owner-daily-report?window_key={too_long_window}",
        )
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid window_key"


def test_owner_report_and_low_stock_alert_payloads_are_safe_and_idempotent() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    inventory_repository = SqliteInventoryRepository.in_memory()
    waiting = asyncio.run(
        create_request(
            service_repository,
            notification_repository,
            intake_payload(name="Waiting Client", brand="Gaggia", problem="Steam wand leaks", urgency="planned"),
        )
    )
    overdue = asyncio.run(
        create_request(
            service_repository,
            notification_repository,
            intake_payload(name="Overdue Client", problem="No coffee flow", urgency="today"),
        )
    )
    set_request_created_at(service_repository, overdue, "2026-06-17T03:00:00+00:00")
    service_repository.add_status_event(overdue, "new", "Free-form staff title", "Internal event description.", "dispatcher")
    service_repository.add_status_event(waiting, "waiting_for_parts", "Ожидаем запчасти", "Нужна поставка.", "technician")
    part = CreatePart(inventory_repository).execute(CreatePartPayload(sku="FLOW-METER", name="Flow meter", unit="pcs"))
    SetStockCount(inventory_repository).execute(part.part_id, quantity_on_hand=1, low_stock_threshold=2)

    owner_report = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/owner-daily-report?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17",
            inventory_repository=inventory_repository,
        )
    )
    low_stock = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/low-stock-alerts?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17T12",
            inventory_repository=inventory_repository,
        )
    )
    duplicate_low_stock = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            "/notifications/n8n/operations/low-stock-alerts?now=2026-06-17T12:00:00+00:00&window_key=2026-06-17T12",
            inventory_repository=inventory_repository,
        )
    )

    assert owner_report.status_code == 200
    assert low_stock.status_code == 200
    assert duplicate_low_stock.status_code == 200
    report_body = owner_report.json()
    low_stock_body = low_stock.json()
    assert report_body["automation"] == "owner_daily_report"
    assert report_body["items"][0]["event_id"] == "operational:owner_daily_report:2026-06-17:report"
    assert report_body["items"][0]["report"]["report_date"] == "2026-06-17"
    assert report_body["items"][0]["report"]["dashboard_url"] == "/owner"
    assert low_stock_body["automation"] == "low_stock_alert"
    assert low_stock_body["items"][0]["event_id"] == f"operational:low_stock_alert:2026-06-17T12:part-{part.part_id}"
    assert low_stock_body["items"][0]["sku"] == "FLOW-METER"
    assert low_stock_body["items"][0]["available_quantity"] == 1
    assert duplicate_low_stock.json()["items"] == []
    assert duplicate_low_stock.json()["suppressed_count"] == 1
    safe_text = str(report_body) + str(low_stock_body)
    assert "+7 999 111-22-33" not in safe_text
    assert "telegram_chat_id" not in safe_text
    assert "latest_event_title" not in safe_text
    assert "Free-form staff title" not in safe_text
