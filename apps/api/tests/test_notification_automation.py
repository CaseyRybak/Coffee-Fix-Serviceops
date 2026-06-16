import asyncio
import logging

import httpx

from serviceops_api.main import create_app
from serviceops_api.notifications.models import DeliveryResultPayload, NotificationEvent
from serviceops_api.notifications.repository import SqliteNotificationRepository
from serviceops_api.notifications.use_cases import NotificationPublisher, RecordN8nDeliveryResult
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


class FailingN8nClient:
    def deliver(self, event: dict[str, object]) -> dict[str, str]:
        return {"status": "failed", "error": "telegram route unavailable"}


class DuplicateNotificationStore:
    def next_sequence(self, request_number: str) -> int:
        return 1

    def create_queued_attempt(self, event: NotificationEvent) -> bool:
        return False

    def record_delivery_result(
        self,
        event_id: str,
        status: str,
        channel: str | None = None,
        provider_message_id: str | None = None,
        error: str | None = None,
        attempt_count: int = 1,
    ) -> None:
        raise AssertionError("duplicate events must not record delivery")

    def record_callback_result(self, payload: DeliveryResultPayload) -> None:
        raise AssertionError("not used by publisher")


class MissingDeliveryUpdateStore:
    def next_sequence(self, request_number: str) -> int:
        return 1

    def create_queued_attempt(self, event: NotificationEvent) -> bool:
        return True

    def record_delivery_result(
        self,
        event_id: str,
        status: str,
        channel: str | None = None,
        provider_message_id: str | None = None,
        error: str | None = None,
        attempt_count: int = 1,
    ) -> bool:
        return False

    def record_callback_result(self, payload: DeliveryResultPayload) -> None:
        raise AssertionError("not used by publisher")


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


def test_notification_publisher_logs_delivery_outcomes(caplog) -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    n8n_client = RecordingN8nClient()

    with caplog.at_level(logging.INFO, logger="serviceops_api.notifications.use_cases"):
        request_number = asyncio.run(create_request(service_repository, notification_repository, n8n_client))

    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    event_id = str(n8n_client.events[0]["event_id"])
    assert {
        "request_number": request_number,
        "event_id": event_id,
        "event_type": "service_request.created",
        "action": "notification.event_queued",
        "target": event_id,
        "outcome": "succeeded",
        "provider": "n8n",
    } in contexts
    assert {
        "request_number": request_number,
        "event_id": event_id,
        "event_type": "service_request.created",
        "action": "notification.delivery_recorded",
        "target": event_id,
        "outcome": "succeeded",
        "provider": "n8n",
    } in contexts
    assert "+7 999 111-22-33" not in str(contexts)


def test_notification_publisher_logs_failed_and_duplicate_outcomes(caplog) -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    failing_client = FailingN8nClient()

    with caplog.at_level(logging.INFO, logger="serviceops_api.notifications.use_cases"):
        response = asyncio.run(
            post_json(
                service_repository,
                notification_repository,
                failing_client,  # type: ignore[arg-type]
                "/service-requests",
                payload(),
            )
        )
        request_number = str(response.json()["request_number"])

        duplicate_publisher = NotificationPublisher(
            DuplicateNotificationStore(),
            RecordingN8nClient(),
            service_repository,
        )
        duplicate_publisher.publish_request_created(request_number)

    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    failed_context = next(
        context for context in contexts if context["action"] == "notification.delivery_recorded" and context["outcome"] == "failed"
    )
    assert failed_context["request_number"] == request_number
    assert failed_context["event_type"] == "service_request.created"
    assert failed_context["provider"] == "n8n"
    assert failed_context["reason"] == "delivery_failed"
    assert "telegram route unavailable" not in str(contexts)
    duplicate_context = next(context for context in contexts if context["action"] == "notification.event_duplicate")
    assert duplicate_context == {
        "request_number": request_number,
        "event_id": f"{request_number}:service_request.created:1",
        "event_type": "service_request.created",
        "action": "notification.event_duplicate",
        "target": f"{request_number}:service_request.created:1",
        "outcome": "skipped",
        "provider": "n8n",
    }


def test_notification_publisher_logs_missing_delivery_update_as_skipped(caplog) -> None:
    service_repository = ServiceRequestRepository.in_memory()
    notification_repository = SqliteNotificationRepository.in_memory()
    request_number = asyncio.run(create_request(service_repository, notification_repository, RecordingN8nClient()))
    publisher = NotificationPublisher(
        MissingDeliveryUpdateStore(),
        RecordingN8nClient(),
        service_repository,
    )
    caplog.clear()

    with caplog.at_level(logging.INFO, logger="serviceops_api.notifications.use_cases"):
        publisher.publish_request_created(request_number)

    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    delivery_context = next(context for context in contexts if context["action"] == "notification.delivery_recorded")
    assert delivery_context == {
        "request_number": request_number,
        "event_id": f"{request_number}:service_request.created:1",
        "event_type": "service_request.created",
        "action": "notification.delivery_recorded",
        "target": f"{request_number}:service_request.created:1",
        "outcome": "skipped",
        "provider": "n8n",
        "reason": "delivery_attempt_not_found",
    }


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


def test_n8n_delivery_result_callback_logs_safe_context(caplog) -> None:
    notification_repository = SqliteNotificationRepository.in_memory()
    event = NotificationEvent(
        event_id="CFX-20260615-000001:service_request.created:1",
        event_type="service_request.created",
        request_number="CFX-20260615-000001",
        payload={"request_number": "CFX-20260615-000001"},
    )
    assert notification_repository.create_queued_attempt(event) is True
    recorder = RecordN8nDeliveryResult(notification_repository)
    payload = DeliveryResultPayload(
        event_id=event.event_id,
        status="sent",
        channel="telegram",
        provider_message_id="tg-123",
        attempt_count=1,
    )

    with caplog.at_level(logging.INFO, logger="serviceops_api.notifications.use_cases"):
        response = recorder.execute(payload)

    assert response.event_id == payload.event_id
    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    assert {
        "request_number": "CFX-20260615-000001",
        "event_id": payload.event_id,
        "event_type": "service_request.created",
        "action": "notification.callback_recorded",
        "target": payload.event_id,
        "outcome": "succeeded",
        "provider": "n8n",
    } in contexts


def test_n8n_delivery_result_callback_logs_unknown_event_without_success(caplog) -> None:
    notification_repository = SqliteNotificationRepository.in_memory()
    recorder = RecordN8nDeliveryResult(notification_repository)
    payload = DeliveryResultPayload(
        event_id="CFX-20260615-000001:service_request.created:1",
        status="failed",
        channel="telegram",
        error="secret callback body with token",
        attempt_count=1,
    )

    with caplog.at_level(logging.INFO, logger="serviceops_api.notifications.use_cases"):
        response = recorder.execute(payload)

    assert response.event_id == payload.event_id
    contexts = [record.serviceops_context for record in caplog.records if hasattr(record, "serviceops_context")]
    assert {
        "request_number": "CFX-20260615-000001",
        "event_id": payload.event_id,
        "event_type": "service_request.created",
        "action": "notification.callback_recorded",
        "target": payload.event_id,
        "outcome": "skipped",
        "reason": "event_not_found",
        "provider": "n8n",
    } in contexts
    assert "secret callback body" not in str(contexts)


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
