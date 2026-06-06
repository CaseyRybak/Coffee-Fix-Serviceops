import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository


def payload(
    *,
    name: str = "Anna Petrova",
    brand: str = "Jura",
    urgency: str = "today",
    problem: str = "Machine leaks water under the brew group.",
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


async def post_json(repository: ServiceRequestRepository, path: str, body: dict[str, object]) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body)


async def get_json(repository: ServiceRequestRepository, path: str) -> httpx.Response:
    app = create_app(service_request_repository=repository)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path)


async def create_request(repository: ServiceRequestRepository, body: dict[str, object]) -> str:
    response = await post_json(repository, "/service-requests", body)
    assert response.status_code == 201
    return str(response.json()["request_number"])


def test_dispatcher_can_list_and_open_request_details() -> None:
    repository = ServiceRequestRepository.in_memory()
    first_request = asyncio.run(create_request(repository, payload(name="Anna Petrova", brand="Jura")))
    second_request = asyncio.run(
        create_request(
            repository,
            payload(name="Ivan Ivanov", brand="Saeco", urgency="planned", problem="Needs planned maintenance."),
        )
    )
    repository.add_status_event(
        request_number=first_request,
        status="awaiting_assignment",
        title="Готово к назначению",
        description="Диспетчер проверил описание.",
        actor="dispatcher",
    )

    list_response = asyncio.run(get_json(repository, "/dispatcher/service-requests"))

    assert list_response.status_code == 200
    list_body = list_response.json()
    assert [item["request_number"] for item in list_body["items"]] == [second_request, first_request]
    assert list_body["items"][0] == {
        "request_number": second_request,
        "status": "new",
        "customer_name": "Ivan Ivanov",
        "customer_phone": "+7 999 111-22-33",
        "machine_label": "Saeco E8",
        "urgency": "planned",
        "address": "Tverskaya district",
        "created_at": list_body["items"][0]["created_at"],
        "latest_event_title": "Заявка создана",
    }
    assert list_body["items"][0]["created_at"]

    detail_response = asyncio.run(get_json(repository, f"/dispatcher/service-requests/{first_request}"))

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["request_number"] == first_request
    assert detail["status"] == "awaiting_assignment"
    assert detail["customer"] == {
        "name": "Anna Petrova",
        "phone": "+7 999 111-22-33",
        "telegram": "@anna_fix",
        "client_type": "coffee_shop",
    }
    assert detail["machine"] == {"brand": "Jura", "model": "E8", "location_type": "coffee_shop"}
    assert detail["problem"] == "Machine leaks water under the brew group."
    assert detail["address"] == "Tverskaya district"
    assert detail["urgency"] == "today"
    assert detail["assignment"] == {
        "technician_name": None,
        "technician_phone": None,
        "technician_region": None,
        "visit_window": None,
    }
    assert detail["clarification"] is None
    assert detail["internal_notes"] == []
    assert [event["title"] for event in detail["timeline"]] == ["Заявка создана", "Готово к назначению"]


def test_dispatcher_status_clarification_assignment_and_internal_notes_are_recorded() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository, payload()))

    status_response = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/status",
            {
                "status": "awaiting_assignment",
                "title": "Готово к назначению",
                "description": "Описание проверено диспетчером.",
            },
        )
    )
    clarification_response = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/clarifications",
            {"question": "Пришлите фото шильдика с моделью кофемашины."},
        )
    )
    assignment_response = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/assignment",
            {
                "technician_name": "Pavel Sokolov",
                "technician_phone": "+7 999 222-33-44",
                "technician_region": "ЦАО",
                "visit_window": "Завтра 14:00-16:00",
            },
        )
    )
    note_response = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/internal-notes",
            {"note": "Клиент просит звонить после 12:00."},
        )
    )

    assert status_response.status_code == 200
    assert status_response.json() == {
        "request_number": request_number,
        "status": "awaiting_assignment",
        "message": "Dispatcher status updated",
    }
    assert clarification_response.status_code == 200
    assert clarification_response.json()["status"] == "needs_clarification"
    assert clarification_response.json()["message"] == "Clarification question created"
    assert assignment_response.status_code == 200
    assert assignment_response.json() == {
        "request_number": request_number,
        "status": "visit_scheduled",
        "message": "Technician assignment recorded",
    }
    assert note_response.status_code == 200
    assert note_response.json() == {
        "request_number": request_number,
        "status": "visit_scheduled",
        "message": "Internal note saved",
    }

    detail = asyncio.run(get_json(repository, f"/dispatcher/service-requests/{request_number}")).json()
    assert detail["status"] == "visit_scheduled"
    assert detail["assignment"] == {
        "technician_name": "Pavel Sokolov",
        "technician_phone": "+7 999 222-33-44",
        "technician_region": "ЦАО",
        "visit_window": "Завтра 14:00-16:00",
    }
    assert detail["clarification"]["question"] == "Пришлите фото шильдика с моделью кофемашины."
    assert detail["internal_notes"][0]["note"] == "Клиент просит звонить после 12:00."
    assert detail["internal_notes"][0]["actor"] == "dispatcher"
    assert [event["status"] for event in detail["timeline"]] == [
        "new",
        "awaiting_assignment",
        "needs_clarification",
        "visit_scheduled",
    ]

    public_status = asyncio.run(get_json(repository, f"/service-requests/{request_number}/status")).json()
    public_text = str(public_status)
    assert public_status["status"] == "visit_scheduled"
    assert public_status["clarification"]["question"] == "Пришлите фото шильдика с моделью кофемашины."
    assert "Клиент просит звонить" not in public_text
    assert "Pavel Sokolov" not in public_text
    assert "+7 999 222-33-44" not in public_text


def test_dispatcher_assignment_without_visit_window_marks_technician_assigned() -> None:
    repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(repository, payload()))

    response = asyncio.run(
        post_json(
            repository,
            f"/dispatcher/service-requests/{request_number}/assignment",
            {
                "technician_name": "Sergey Morozov",
                "technician_region": "ЦАО",
            },
        )
    )

    assert response.status_code == 200
    assert response.json() == {
        "request_number": request_number,
        "status": "technician_assigned",
        "message": "Technician assignment recorded",
    }

    detail = asyncio.run(get_json(repository, f"/dispatcher/service-requests/{request_number}")).json()
    assert detail["status"] == "technician_assigned"
    assert detail["assignment"] == {
        "technician_name": "Sergey Morozov",
        "technician_phone": None,
        "technician_region": "ЦАО",
        "visit_window": None,
    }
    assert detail["timeline"][-1]["status"] == "technician_assigned"
    assert detail["timeline"][-1]["actor"] == "dispatcher"


def test_dispatcher_routes_return_404_for_missing_request() -> None:
    repository = ServiceRequestRepository.in_memory()

    response = asyncio.run(get_json(repository, "/dispatcher/service-requests/CFX-20260605-999999"))

    assert response.status_code == 404
