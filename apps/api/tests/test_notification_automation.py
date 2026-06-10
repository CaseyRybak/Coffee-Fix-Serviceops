import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.notifications.repository import SqliteNotificationRepository
from serviceops_api.service_requests.repository import ServiceRequestRepository


def payload() -> dict[str, object]:
    return {
        "customer": {
            "name": "Anna Petrova",
            "phone": "+7 999 111-22-33",
            "telegram": "@anna_fix",
            "client_type": "coffee_shop",
        },
        "machine": {
            "brand": "Jura",
            "model": "E8",
            "location_type": "coffee_shop",
        },
        "problem": "Machine leaks water under the brew group.",
        "address": "Tverskaya district",
        "urgency": "today",
    }


class RecordingN8nClient:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def deliver(self, event: dict[str, object]) -> dict[str, str]:
        self.events.append(event)
        return {"status": "sent", "provider_message_id": f"n8n-{event['event_id']}"}


async def post_json(
    service_repository: ServiceRequestRepository,
    notification_repository: SqliteNotificationRepository,
    n8n_client: RecordingN8nClient,
    path: str,
    body: dict[str, object],
    token: str | None = None,
    callback_secret: str = "callback-secret",
) -> httpx.Response:
    app = create_app(
        service_request_repository=service_repository,
        notification_repository=notification_repository,
        n8n_client=n8n_client,
        n8n_callback_secret=callback_secret,
    )
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(
    service_repository: ServiceRequestRepository,
    notification_repository: SqliteNotificationRepository,
    n8n_client: RecordingN8nClient,
    path: str,
    token: str | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=service_repository,
        notification_repository=notification_repository,
        n8n_client=n8n_client,
        n8n_callback_secret="callback-secret",
    )
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def create_request(
    service_repository: ServiceRequestRepository,
    notification_repository: SqliteNotificationRepository,
    n8n_client: RecordingN8nClient,
) -> str:
    response = await post_json(service_repository, notification_repository, n8n_client, "/service-requests", payload())
    assert response.status_code == 201
    return str(response.json()["request_number"])


async def dispatcher_token(
    service_repository: ServiceRequestRepository,
    notification_repository: SqliteNotificationRepository,
    n8n_client: RecordingN8nClient,
) -> str:
    response = await post_json(
        service_repository,
        notification_repository,
        n8n_client,
        "/staff/login",
        {"username": "dispatcher@coffeefix.local", "password": "dispatcher-local"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def test_request_created_event_is_public_safe_and_persisted() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    n8n_client = RecordingN8nClient()

    request_number = asyncio.run(create_request(service_repository, notification_repository, n8n_client))

    assert len(n8n_client.events) == 1
    event = n8n_client.events[0]
    assert event["event_type"] == "service_request.created"
    assert event["request_number"] == request_number
    assert event["payload"] == {
        "request_number": request_number,
        "customer_name": "Anna Petrova",
        "customer_phone_masked": "+7 999 ***-**-33",
        "machine_brand": "Jura",
        "machine_model": "E8",
        "urgency": "today",
        "public_status_url": event["payload"]["public_status_url"],
    }
    assert "111-22-33" not in str(event)
    assert "Tverskaya" not in str(event)
    assert notification_repository.list_for_request(request_number)[0]["status"] == "sent"


def test_lifecycle_events_are_emitted_and_deduplicated_by_event_id() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    n8n_client = RecordingN8nClient()
    request_number = asyncio.run(create_request(service_repository, notification_repository, n8n_client))
    opt_in = service_repository.create_telegram_opt_in(request_number, "@anna_fix")
    service_repository.link_telegram_opt_in(str(opt_in["token"]), "123456789", "anna_fix")
    token = asyncio.run(dispatcher_token(service_repository, notification_repository, n8n_client))

    status_response = asyncio.run(
        post_json(
            service_repository,
            notification_repository,
            n8n_client,
            f"/dispatcher/service-requests/{request_number}/status",
            {
                "status": "awaiting_assignment",
                "title": "Готово к назначению",
                "description": "Описание проверено диспетчером.",
            },
            token=token,
        )
    )
    clarification_response = asyncio.run(
        post_json(
            service_repository,
            notification_repository,
            n8n_client,
            f"/dispatcher/service-requests/{request_number}/clarifications",
            {"question": "Пришлите фото шильдика с моделью кофемашины."},
            token=token,
        )
    )

    question_id = service_repository.get_dispatcher_request(request_number)["clarification"]["question_id"]
    answer_response = asyncio.run(
        post_json(
            service_repository,
            notification_repository,
            n8n_client,
            f"/service-requests/{request_number}/answers",
            {"question_id": question_id, "answer": "Фото отправили в Telegram."},
        )
    )

    assert status_response.status_code == 200
    assert clarification_response.status_code == 200
    assert answer_response.status_code == 200
    assert [event["event_type"] for event in n8n_client.events] == [
        "service_request.created",
        "service_request.status_changed",
        "service_request.clarification_requested",
        "service_request.customer_answered",
    ]
    assert n8n_client.events[1]["payload"]["telegram_chat_id"] == "123456789"
    assert n8n_client.events[2]["payload"]["telegram_chat_id"] == "123456789"
    event_ids = [str(event["event_id"]) for event in n8n_client.events]
    assert len(event_ids) == len(set(event_ids))
    assert all(event_id.startswith(f"{request_number}:") for event_id in event_ids)


def test_n8n_delivery_result_callback_updates_attempt_without_changing_request_status() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    n8n_client = RecordingN8nClient()
    request_number = asyncio.run(create_request(service_repository, notification_repository, n8n_client))
    event_id = str(n8n_client.events[0]["event_id"])

    app = create_app(
        service_request_repository=service_repository,
        notification_repository=notification_repository,
        n8n_client=n8n_client,
        n8n_callback_secret="callback-secret",
    )
    transport = httpx.ASGITransport(app=app)

    async def send_callback() -> httpx.Response:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post(
                "/notifications/n8n/delivery-results",
                json={
                    "event_id": event_id,
                    "status": "failed",
                    "channel": "telegram",
                    "provider_message_id": "tg-123",
                    "error": "chat not found",
                    "attempt_count": 2,
                },
                headers={"X-ServiceOps-Callback-Secret": "callback-secret"},
            )

    response = asyncio.run(send_callback())

    assert response.status_code == 200
    assert response.json() == {"event_id": event_id, "status": "failed"}
    assert notification_repository.list_for_request(request_number)[0]["status"] == "failed"
    assert service_repository.get_public_status_by_request_number(request_number)["status"] == "new"


def test_dispatcher_detail_shows_notification_delivery_status_but_public_status_does_not() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    n8n_client = RecordingN8nClient()
    request_number = asyncio.run(create_request(service_repository, notification_repository, n8n_client))
    token = asyncio.run(dispatcher_token(service_repository, notification_repository, n8n_client))

    detail_response = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            n8n_client,
            f"/dispatcher/service-requests/{request_number}",
            token=token,
        )
    )
    public_response = asyncio.run(
        get_json(
            service_repository,
            notification_repository,
            n8n_client,
            f"/service-requests/{request_number}/status",
        )
    )

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["notification_deliveries"][0]["event_type"] == "service_request.created"
    assert detail["notification_deliveries"][0]["status"] == "sent"
    assert "notification_deliveries" not in public_response.json()
