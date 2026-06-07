import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.inventory.repository import SqliteInventoryRepository
from serviceops_api.service_requests.repository import ServiceRequestRepository


async def post_json(
    path: str,
    body: dict[str, object],
    token: str | None = None,
    inventory_repository: SqliteInventoryRepository | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=ServiceRequestRepository.in_memory(),
        inventory_repository=inventory_repository,
    )
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body, headers=headers)


async def get_json(
    path: str,
    token: str | None = None,
    inventory_repository: SqliteInventoryRepository | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=ServiceRequestRepository.in_memory(),
        inventory_repository=inventory_repository,
    )
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def staff_token(username: str, password: str) -> str:
    response = await post_json("/staff/login", {"username": username, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def test_inventory_repository_records_stock_and_parts_used() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, RecordPartsUsedPayload
    from serviceops_api.inventory.repository import SqliteInventoryRepository
    from serviceops_api.inventory.use_cases import CreatePart, RecordPartsUsed, SetStockCount

    repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(repository).execute(
        CreatePartPayload(
            sku="E61-GASKET-73",
            name="E61 group gasket 73mm",
            brand="Rocket",
            model="Appartamento",
            unit="pcs",
        )
    )
    SetStockCount(repository).execute(part.part_id, quantity_on_hand=4)

    result = RecordPartsUsed(repository).execute(
        "CFX-20260607-000001",
        RecordPartsUsedPayload(part_id=part.part_id, quantity=2, note="Changed worn gasket"),
    )

    assert result.request_number == "CFX-20260607-000001"
    assert result.quantity_on_hand == 2
    assert result.stock_after_use == 2
    assert repository.list_parts_used("CFX-20260607-000001")[0]["part_name"] == "E61 group gasket 73mm"


def test_parts_used_history_keeps_stock_after_each_usage() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, RecordPartsUsedPayload
    from serviceops_api.inventory.repository import SqliteInventoryRepository
    from serviceops_api.inventory.use_cases import CreatePart, RecordPartsUsed, SetStockCount

    repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(repository).execute(CreatePartPayload(sku="E61-SCREEN", name="E61 shower screen", unit="pcs"))
    SetStockCount(repository).execute(part.part_id, quantity_on_hand=5)

    RecordPartsUsed(repository).execute(
        "CFX-20260607-000001",
        RecordPartsUsedPayload(part_id=part.part_id, quantity=2),
    )
    SetStockCount(repository).execute(part.part_id, quantity_on_hand=10)

    usage = repository.list_parts_used("CFX-20260607-000001")[0]

    assert usage["quantity_on_hand"] == 10
    assert usage["stock_after_use"] == 3


def test_inventory_repository_rejects_usage_that_exceeds_stock() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, RecordPartsUsedPayload
    from serviceops_api.inventory.repository import InsufficientStockError, SqliteInventoryRepository
    from serviceops_api.inventory.use_cases import CreatePart, RecordPartsUsed, SetStockCount

    repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(repository).execute(CreatePartPayload(sku="PUMP-ULKA-01", name="Ulka pump", unit="pcs"))
    SetStockCount(repository).execute(part.part_id, quantity_on_hand=1)

    try:
        RecordPartsUsed(repository).execute(
            "CFX-20260607-000001",
            RecordPartsUsedPayload(part_id=part.part_id, quantity=2),
        )
    except InsufficientStockError as exc:
        assert "Insufficient stock" in str(exc)
    else:
        raise AssertionError("expected insufficient stock to fail")

    assert repository.get_stock_count(part.part_id)["quantity_on_hand"] == 1
    assert repository.list_parts_used("CFX-20260607-000001") == []


def test_inventory_api_requires_inventory_role_and_manages_stock() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))

    create_response = asyncio.run(
        post_json(
            "/inventory/parts",
            {
                "sku": "E61-GASKET-73",
                "name": "E61 group gasket 73mm",
                "brand": "Rocket",
                "model": "Appartamento",
                "unit": "pcs",
                "compatibility_note": "Fits common E61 groups.",
            },
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    assert create_response.status_code == 201
    part_id = int(create_response.json()["part_id"])

    stock_response = asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/stock",
            {"quantity_on_hand": 6},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    list_response = asyncio.run(get_json("/inventory/parts", token=token, inventory_repository=inventory_repository))

    assert stock_response.status_code == 200
    assert stock_response.json()["quantity_on_hand"] == 6
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["sku"] == "E61-GASKET-73"
    assert list_response.json()["items"][0]["quantity_on_hand"] == 6


def test_inventory_api_rejects_unauthenticated_and_wrong_role() -> None:
    dispatcher_token = asyncio.run(staff_token("dispatcher@coffeefix.local", "dispatcher-local"))

    unauthenticated = asyncio.run(get_json("/inventory/parts"))
    wrong_role = asyncio.run(get_json("/inventory/parts", token=dispatcher_token))

    assert unauthenticated.status_code == 401
    assert wrong_role.status_code == 403
