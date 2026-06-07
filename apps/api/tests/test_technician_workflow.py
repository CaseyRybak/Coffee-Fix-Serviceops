import asyncio

import httpx

from serviceops_api.inventory.repository import SqliteInventoryRepository
from serviceops_api.main import create_app
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
            "brand": "Rocket",
            "model": "Appartamento",
            "location_type": "coffee_shop",
        },
        "problem": "E61 group overheats after descaling.",
        "address": "Tverskaya district",
        "urgency": "today",
    }


async def post_json(
    service_repository: ServiceRequestRepository,
    path: str,
    body: dict[str, object],
    token: str | None = None,
    inventory_repository: SqliteInventoryRepository | None = None,
) -> httpx.Response:
    app = create_app(service_request_repository=service_repository, inventory_repository=inventory_repository)
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(
    service_repository: ServiceRequestRepository,
    path: str,
    token: str | None = None,
    inventory_repository: SqliteInventoryRepository | None = None,
) -> httpx.Response:
    app = create_app(service_request_repository=service_repository, inventory_repository=inventory_repository)
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def staff_token(service_repository: ServiceRequestRepository, username: str, password: str) -> str:
    response = await post_json(service_repository, "/staff/login", {"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


async def create_request(service_repository: ServiceRequestRepository) -> str:
    response = await post_json(service_repository, "/service-requests", payload())
    assert response.status_code == 201
    return str(response.json()["request_number"])


async def assign_to_technician(service_repository: ServiceRequestRepository, request_number: str) -> None:
    dispatcher_token = await staff_token(service_repository, "dispatcher@coffeefix.local", "dispatcher-local")
    response = await post_json(
        service_repository,
        f"/dispatcher/service-requests/{request_number}/assignment",
        {
            "technician_name": "technician@coffeefix.local",
            "technician_phone": "+7 999 222-33-44",
            "technician_region": "ЦАО",
            "visit_window": "Сегодня 16:00-18:00",
        },
        token=dispatcher_token,
    )
    assert response.status_code == 200


def test_technician_can_list_detail_diagnose_and_record_result() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(service_repository))
    asyncio.run(assign_to_technician(service_repository, request_number))
    technician_token = asyncio.run(staff_token(service_repository, "technician@coffeefix.local", "technician-local"))

    list_response = asyncio.run(get_json(service_repository, "/technician/service-requests", token=technician_token))
    detail_response = asyncio.run(
        get_json(service_repository, f"/technician/service-requests/{request_number}", token=technician_token)
    )
    diagnosis_response = asyncio.run(
        post_json(
            service_repository,
            f"/technician/service-requests/{request_number}/diagnosis",
            {
                "machine_powered_on": True,
                "water_supply_checked": True,
                "leak_checked": False,
                "error_code_checked": True,
                "summary": "Group overheats during idle, no active display error.",
            },
            token=technician_token,
        )
    )
    result_response = asyncio.run(
        post_json(
            service_repository,
            f"/technician/service-requests/{request_number}/result",
            {
                "result": "waiting_for_parts",
                "summary": "Thermosiphon restrictor needs replacement.",
                "next_step": "Bring E61 restrictor kit.",
            },
            token=technician_token,
        )
    )

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["request_number"] == request_number
    assert list_response.json()["items"][0]["visit_window"] == "Сегодня 16:00-18:00"
    assert detail_response.status_code == 200
    assert detail_response.json()["problem"] == "E61 group overheats after descaling."
    assert diagnosis_response.status_code == 200
    assert diagnosis_response.json() == {
        "request_number": request_number,
        "status": "diagnostics",
        "message": "Technician diagnosis recorded",
    }
    assert result_response.status_code == 200
    assert result_response.json() == {
        "request_number": request_number,
        "status": "waiting_for_parts",
        "message": "Technician result recorded",
    }

    updated_detail = asyncio.run(
        get_json(service_repository, f"/technician/service-requests/{request_number}", token=technician_token)
    ).json()
    assert updated_detail["diagnosis"]["summary"] == "Group overheats during idle, no active display error."
    assert updated_detail["repair_result"]["next_step"] == "Bring E61 restrictor kit."

    public_status = asyncio.run(get_json(service_repository, f"/service-requests/{request_number}/status")).json()
    public_text = str(public_status)
    assert public_status["status"] == "waiting_for_parts"
    assert "Диагностика начата" in public_text
    assert "Ожидаем запчасти" in public_text
    assert "Group overheats during idle" not in public_text
    assert "Bring E61 restrictor kit" not in public_text


def test_technician_api_requires_technician_role_and_assignment() -> None:
    service_repository = ServiceRequestRepository.in_memory()
    request_number = asyncio.run(create_request(service_repository))
    dispatcher_token = asyncio.run(staff_token(service_repository, "dispatcher@coffeefix.local", "dispatcher-local"))
    technician_token = asyncio.run(staff_token(service_repository, "technician@coffeefix.local", "technician-local"))

    unauthenticated = asyncio.run(get_json(service_repository, "/technician/service-requests"))
    wrong_role = asyncio.run(get_json(service_repository, "/technician/service-requests", token=dispatcher_token))
    unassigned_detail = asyncio.run(
        get_json(service_repository, f"/technician/service-requests/{request_number}", token=technician_token)
    )

    assert unauthenticated.status_code == 401
    assert wrong_role.status_code == 403
    assert unassigned_detail.status_code == 404


def test_technician_records_parts_used_and_updates_request_history() -> None:
    from serviceops_api.inventory.models import CreatePartPayload
    from serviceops_api.inventory.use_cases import CreatePart, SetStockCount

    service_repository = ServiceRequestRepository.in_memory()
    inventory_repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(inventory_repository).execute(
        CreatePartPayload(sku="E61-RESTRICTOR", name="E61 restrictor kit", unit="pcs")
    )
    SetStockCount(inventory_repository).execute(part.part_id, 3)
    request_number = asyncio.run(create_request(service_repository))
    asyncio.run(assign_to_technician(service_repository, request_number))
    technician_token = asyncio.run(staff_token(service_repository, "technician@coffeefix.local", "technician-local"))

    response = asyncio.run(
        post_json(
            service_repository,
            f"/technician/service-requests/{request_number}/parts-used",
            {"part_id": part.part_id, "quantity": 1, "note": "Installed restrictor kit"},
            token=technician_token,
            inventory_repository=inventory_repository,
        )
    )

    assert response.status_code == 200
    assert response.json()["status"] == "repair_in_progress"
    assert inventory_repository.get_stock_count(part.part_id)["quantity_on_hand"] == 2
    assert inventory_repository.list_parts_used(request_number)[0]["part_name"] == "E61 restrictor kit"

    public_status = asyncio.run(get_json(service_repository, f"/service-requests/{request_number}/status")).json()
    assert public_status["status"] == "repair_in_progress"
    assert public_status["timeline"][-1]["actor"] == "technician"
    assert public_status["timeline"][-1]["title"] == "Запчасти использованы"


def test_technician_parts_used_rejects_insufficient_stock_without_status_change() -> None:
    from serviceops_api.inventory.models import CreatePartPayload
    from serviceops_api.inventory.use_cases import CreatePart, SetStockCount

    service_repository = ServiceRequestRepository.in_memory()
    inventory_repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(inventory_repository).execute(CreatePartPayload(sku="BOILER-PROBE", name="Boiler probe", unit="pcs"))
    SetStockCount(inventory_repository).execute(part.part_id, 1)
    request_number = asyncio.run(create_request(service_repository))
    asyncio.run(assign_to_technician(service_repository, request_number))
    technician_token = asyncio.run(staff_token(service_repository, "technician@coffeefix.local", "technician-local"))

    response = asyncio.run(
        post_json(
            service_repository,
            f"/technician/service-requests/{request_number}/parts-used",
            {"part_id": part.part_id, "quantity": 2},
            token=technician_token,
            inventory_repository=inventory_repository,
        )
    )

    assert response.status_code == 422
    assert inventory_repository.get_stock_count(part.part_id)["quantity_on_hand"] == 1
    public_status = asyncio.run(get_json(service_repository, f"/service-requests/{request_number}/status")).json()
    assert public_status["status"] == "visit_scheduled"
