import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository


def payload(name: str = "Anna Petrova") -> dict[str, object]:
    return {
        "customer": {
            "name": name,
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


async def post_json(
    repository: ServiceRequestRepository,
    path: str,
    body: dict[str, object],
    token: str | None = None,
) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(repository: ServiceRequestRepository, path: str, token: str | None = None) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def create_request(repository: ServiceRequestRepository, body: dict[str, object] | None = None) -> str:
    response = await post_json(repository, "/service-requests", body or payload())
    assert response.status_code == 201
    return str(response.json()["request_number"])


async def staff_token(repository: ServiceRequestRepository, username: str, password: str) -> str:
    response = await post_json(repository, "/staff/login", {"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def appointment_payload(
    technician_identifier: str = "technician@coffeefix.local",
    starts_at: str = "2026-06-16T14:00:00+03:00",
    ends_at: str = "2026-06-16T16:00:00+03:00",
    window_label: str | None = "16 июня 14:00-16:00",
) -> dict[str, object]:
    body: dict[str, object] = {
        "technician_identifier": technician_identifier,
        "starts_at": starts_at,
        "ends_at": ends_at,
    }
    if window_label is not None:
        body["window_label"] = window_label
    return body


def test_dispatcher_can_create_structured_appointment_and_schedule_view() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    token = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))

    response = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/appointments",
            {
                **appointment_payload(),
                "technician_name": "Pavel Sokolov",
            },
            token=token,
        )
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_number"] == request_number
    assert body["status"] == "visit_scheduled"
    assert body["appointment"]["status"] == "scheduled"
    assert body["appointment"]["window_label"] == "16 июня 14:00-16:00"

    schedule = asyncio.run(get_json(repository, "/dispatcher/schedule", token=token)).json()
    assert [item["appointment"]["request_number"] for item in schedule["items"]] == [request_number]
    assert schedule["items"][0]["appointment"]["technician_identifier"] == "technician@coffeefix.local"

    detail = asyncio.run(get_json(repository, f"/dispatcher/service-requests/{request_number}", token=token)).json()
    assert detail["status"] == "visit_scheduled"
    assert detail["assignment"]["technician_name"] == "technician@coffeefix.local"
    assert detail["assignment"]["visit_window"] == "16 июня 14:00-16:00"
    assert detail["appointment"]["window_label"] == "16 июня 14:00-16:00"
    assert detail["timeline"][-1]["title"] == "Визит запланирован"


def test_scheduling_rejects_overlapping_technician_window() -> None:
    repository = ServiceRequestRepository.in_memory()
    first = asyncio.run(create_request(repository, payload("Anna Petrova")))
    second = asyncio.run(create_request(repository, payload("Ivan Ivanov")))
    token = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))

    first_response = asyncio.run(
        post_json(repository, f"/dispatcher/service-requests/{first}/appointments", appointment_payload(), token=token)
    )
    second_response = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{second}/appointments",
            appointment_payload(starts_at="2026-06-16T15:00:00+03:00", ends_at="2026-06-16T17:00:00+03:00"),
            token=token,
        )
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Technician already has an appointment in this window"


def test_reschedule_and_cancel_update_history_technician_and_public_snapshots() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    dispatcher = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    technician = asyncio.run(staff_token(repository, "technician@coffeefix.local", "technician-local"))
    created = asyncio.run(
        post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments", appointment_payload(), token=dispatcher)
    ).json()

    appointment_id = created["appointment"]["appointment_id"]
    rescheduled = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/appointments/{appointment_id}/reschedule",
            {
                "starts_at": "2026-06-17T10:00:00+03:00",
                "ends_at": "2026-06-17T12:00:00+03:00",
                "window_label": "17 июня 10:00-12:00",
                "reason": "Клиент попросил утро",
            },
            token=dispatcher,
        )
    )
    new_appointment_id = rescheduled.json()["appointment"]["appointment_id"]
    cancelled = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/appointments/{new_appointment_id}/cancel",
            {"reason": "Клиент перенесет позже"},
            token=dispatcher,
        )
    )

    assert rescheduled.status_code == 200
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "technician_assigned"

    tech_detail = asyncio.run(get_json(repository, f"/technician/service-requests/{request_number}", token=technician)).json()
    assert tech_detail["visit_window"] is None
    assert tech_detail["appointment"] is None

    public_status = asyncio.run(get_json(repository, f"/service-requests/{request_number}/status")).json()
    public_text = str(public_status)
    assert public_status["status"] == "technician_assigned"
    assert public_status["appointment"] is None
    assert "Визит перенесен" in public_text
    assert "Визит отменен" in public_text
    assert "Клиент попросил утро" not in public_text
    assert "Клиент перенесет позже" not in public_text
    assert "appointment_id" not in public_text


def test_reschedule_and_cancel_preserve_started_work_status() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    dispatcher = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    created = asyncio.run(
        post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments", appointment_payload(), token=dispatcher)
    ).json()
    repository.add_status_event(
        request_number,
        "waiting_for_parts",
        "Ожидаем запчасти",
        "Мастер ожидает поставку запчастей.",
        "technician",
    )

    rescheduled = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/appointments/{created['appointment']['appointment_id']}/reschedule",
            {
                "starts_at": "2026-06-18T10:00:00+03:00",
                "ends_at": "2026-06-18T12:00:00+03:00",
                "window_label": "18 июня 10:00-12:00",
                "reason": "Повторный визит после поставки",
            },
            token=dispatcher,
        )
    )
    new_appointment_id = rescheduled.json()["appointment"]["appointment_id"]
    cancelled = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/appointments/{new_appointment_id}/cancel",
            {"reason": "Запчасть не приехала"},
            token=dispatcher,
        )
    )

    assert rescheduled.status_code == 200
    assert rescheduled.json()["status"] == "waiting_for_parts"
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "waiting_for_parts"

    public_status = asyncio.run(get_json(repository, f"/service-requests/{request_number}/status")).json()
    assert public_status["status"] == "waiting_for_parts"
    assert public_status["appointment"] is None


def test_structured_scheduling_clears_stale_assignment_contact_metadata() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    dispatcher = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    legacy_assignment = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/assignment",
            {
                "technician_name": "legacy-tech@coffeefix.local",
                "technician_phone": "+7 999 222-33-44",
                "technician_region": "ЦАО",
                "visit_window": "Сегодня 16:00-18:00",
            },
            token=dispatcher,
        )
    )

    scheduled = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/appointments",
            appointment_payload(
                technician_identifier="technician@coffeefix.local",
                starts_at="2026-06-19T10:00:00+03:00",
                ends_at="2026-06-19T12:00:00+03:00",
                window_label="19 июня 10:00-12:00",
            ),
            token=dispatcher,
        )
    )

    detail = asyncio.run(get_json(repository, f"/dispatcher/service-requests/{request_number}", token=dispatcher)).json()
    assert legacy_assignment.status_code == 200
    assert scheduled.status_code == 200
    assert detail["assignment"] == {
        "technician_name": "technician@coffeefix.local",
        "technician_phone": None,
        "technician_region": None,
        "visit_window": "19 июня 10:00-12:00",
    }


def test_scheduling_rejects_terminal_or_in_progress_requests() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    dispatcher = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    repository.add_status_event(request_number, "diagnostics", "Диагностика начата", "Мастер уже на выезде.", "technician")

    response = asyncio.run(
        post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments", appointment_payload(), token=dispatcher)
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Request status does not allow scheduling changes"


def test_scheduling_routes_require_staff_roles() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository))
    technician_token = asyncio.run(staff_token(repository, "technician@coffeefix.local", "technician-local"))
    dispatcher_token = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))

    unauthenticated = asyncio.run(get_json(repository, "/dispatcher/schedule"))
    wrong_dispatcher_role = asyncio.run(get_json(repository, "/dispatcher/schedule", token=technician_token))
    wrong_technician_role = asyncio.run(get_json(repository, "/technician/schedule", token=dispatcher_token))
    create_without_auth = asyncio.run(
        post_json(repository, f"/dispatcher/service-requests/{request_number}/appointments", appointment_payload())
    )

    assert unauthenticated.status_code == 401
    assert wrong_dispatcher_role.status_code == 403
    assert wrong_technician_role.status_code == 403
    assert create_without_auth.status_code == 401


def test_technician_schedule_only_lists_authenticated_technician_appointments() -> None:
    repository = ServiceRequestRepository.in_memory()
    own_request = asyncio.run(create_request(repository, payload("Anna Petrova")))
    other_request = asyncio.run(create_request(repository, payload("Ivan Ivanov")))
    dispatcher = asyncio.run(staff_token(repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    technician = asyncio.run(staff_token(repository, "technician@coffeefix.local", "technician-local"))
    asyncio.run(
        post_json(repository, f"/dispatcher/service-requests/{own_request}/appointments", appointment_payload(), token=dispatcher)
    )
    asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{other_request}/appointments",
            appointment_payload(
                technician_identifier="other-tech@coffeefix.local",
                starts_at="2026-06-16T17:00:00+03:00",
                ends_at="2026-06-16T19:00:00+03:00",
                window_label="16 июня 17:00-19:00",
            ),
            token=dispatcher,
        )
    )

    response = asyncio.run(get_json(repository, "/technician/schedule", token=technician))

    assert response.status_code == 200
    assert [item["appointment"]["request_number"] for item in response.json()["items"]] == [own_request]
