import asyncio
from pathlib import Path

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


def test_inventory_russian_catalog_migration_normalizes_gaggia_classic_pump_seed() -> None:
    migration = Path("src/serviceops_api/migrations/0010_inventory_russian_catalog.sql").read_text(encoding="utf-8")

    assert "WHEN 'GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM' THEN 'Вибрационный насос Gaggia Classic 20 мм'" in migration
    assert (
        "GAGGIA-CLASSIC-PUMP-DIAMETER-20-MM"
        in migration[migration.index("WHERE sku IN (") : migration.index(");", migration.index("WHERE sku IN ("))]
    )
    assert "DELETE FROM part_compatibility" in migration
    assert "pc.brand = 'Jura'" in migration
    assert "pc.series = 'серия E'" in migration


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


def test_inventory_reservations_adjust_release_and_movement_history() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, ReservationPayload
    from serviceops_api.inventory.repository import InsufficientStockError, SqliteInventoryRepository
    from serviceops_api.inventory.use_cases import CreatePart, ReservePart, SetStockCount

    repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(repository).execute(CreatePartPayload(sku="FLOW-METER", name="Flow meter", unit="pcs"))
    SetStockCount(repository).execute(part.part_id, quantity_on_hand=5, low_stock_threshold=2)

    reserved = ReservePart(repository).execute(
        ReservationPayload(request_number="CFX-20260607-000001", part_id=part.part_id, quantity=3, note="Bring to visit")
    )
    adjusted = repository.adjust_reservation(reserved.reservation_id, quantity=2, note="One part not needed", actor="inventory")
    released = repository.release_reservation(reserved.reservation_id, note="Client cancelled", actor="inventory")

    part_snapshot = repository.list_parts()[0]
    movements = repository.list_stock_movements(part_id=part.part_id)

    assert reserved.status == "active"
    assert adjusted["quantity"] == 2
    assert released["status"] == "released"
    assert part_snapshot["quantity_on_hand"] == 5
    assert part_snapshot["reserved_quantity"] == 0
    assert part_snapshot["available_quantity"] == 5
    assert part_snapshot["low_stock_threshold"] == 2
    assert part_snapshot["is_low_stock"] is False
    assert [movement["movement_type"] for movement in movements] == ["release", "reservation_adjusted", "reservation_created", "manual_adjustment"]

    try:
        ReservePart(repository).execute(
            ReservationPayload(request_number="CFX-20260607-000002", part_id=part.part_id, quantity=6)
        )
    except InsufficientStockError:
        pass
    else:
        raise AssertionError("expected reservation above available stock to fail")


def test_parts_used_consumes_reserved_parts_and_records_consumption_movement() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, RecordPartsUsedPayload, ReservationPayload
    from serviceops_api.inventory.repository import SqliteInventoryRepository
    from serviceops_api.inventory.use_cases import CreatePart, RecordPartsUsed, ReservePart, SetStockCount

    repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(repository).execute(CreatePartPayload(sku="BOILER-PROBE", name="Boiler probe", unit="pcs"))
    SetStockCount(repository).execute(part.part_id, quantity_on_hand=4)
    ReservePart(repository).execute(ReservationPayload(request_number="CFX-20260607-000001", part_id=part.part_id, quantity=2))

    result = RecordPartsUsed(repository).execute(
        "CFX-20260607-000001",
        RecordPartsUsedPayload(part_id=part.part_id, quantity=1, note="Installed reserved probe"),
    )

    reservations = repository.list_reservations("CFX-20260607-000001")
    part_snapshot = repository.list_parts()[0]
    movements = repository.list_stock_movements(part_id=part.part_id)

    assert result.quantity_on_hand == 3
    assert reservations[0]["quantity"] == 1
    assert reservations[0]["status"] == "active"
    assert part_snapshot["reserved_quantity"] == 1
    assert part_snapshot["available_quantity"] == 2
    assert movements[0]["movement_type"] == "consumption"
    assert movements[0]["quantity"] == -1


def test_inventory_api_exposes_reservations_movements_and_low_stock() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))

    create_response = asyncio.run(
        post_json(
            "/inventory/parts",
            {"sku": "E61-SEAL", "name": "E61 seal", "unit": "pcs", "brand": "Rocket", "model": "Appartamento"},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    part_id = int(create_response.json()["part_id"])
    asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/stock",
            {"quantity_on_hand": 3, "low_stock_threshold": 2},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    reservation = asyncio.run(
        post_json(
            "/inventory/reservations",
            {"request_number": "CFX-20260607-000001", "part_id": part_id, "quantity": 2},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    movements = asyncio.run(get_json("/inventory/movements", token=token, inventory_repository=inventory_repository))
    parts = asyncio.run(get_json("/inventory/parts", token=token, inventory_repository=inventory_repository))

    assert reservation.status_code == 201
    assert reservation.json()["quantity"] == 2
    assert movements.status_code == 200
    assert movements.json()["items"][0]["movement_type"] == "reservation_created"
    assert parts.json()["items"][0]["quantity_on_hand"] == 3
    assert parts.json()["items"][0]["reserved_quantity"] == 2
    assert parts.json()["items"][0]["available_quantity"] == 1
    assert parts.json()["items"][0]["is_low_stock"] is True


def test_inventory_api_rejects_numeric_unit_values() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))

    response = asyncio.run(
        post_json(
            "/inventory/parts",
            {
                "sku": "GAGGIA-CLASSIC-GASKET-55",
                "name": "Gaggia Classic gasket 55mm",
                "unit": "5",
                "brand": "Gaggia",
                "model": "Classic",
            },
            token=token,
            inventory_repository=inventory_repository,
        )
    )

    assert response.status_code == 422


def test_postgres_part_row_requires_reservation_visibility_fields() -> None:
    from serviceops_api.inventory.repository import PostgresInventoryRepository

    repository = PostgresInventoryRepository("postgresql://user:pass@localhost/db", initialize=False)

    row = repository._part_row(  # noqa: SLF001
        {
            "id": 1,
            "sku": "E61-GASKET-73",
            "name": "E61 group gasket 73mm",
            "brand": "Rocket",
            "model": "Appartamento",
            "unit": "pcs",
            "compatibility_note": "Fits common E61 groups.",
            "created_at": "2026-06-15 10:00:00",
            "quantity_on_hand": 4,
            "reserved_quantity": 3,
            "low_stock_threshold": 2,
            "stock_updated_at": "2026-06-15 10:05:00",
        }
    )

    assert row["reserved_quantity"] == 3
    assert row["available_quantity"] == 1
    assert row["is_low_stock"] is True


def test_inventory_blocks_duplicate_factual_part_key_but_allows_different_size() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))

    first = asyncio.run(
        post_json(
            "/inventory/parts",
            {
                "sku": "DELONGHI-SEAL-2IN",
                "name": "Уплотнительное кольцо DeLonghi 2 дюйма",
                "brand": "DeLonghi",
                "unit": "pcs",
                "part_type": "seal",
                "parameter_label": "diameter",
                "parameter_value": "2",
                "parameter_unit": "inch",
            },
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    duplicate = asyncio.run(
        post_json(
            "/inventory/parts",
            {
                "sku": "DELONGHI-O-RING-2",
                "name": "O-ring Delonghi 2 inch",
                "brand": "delonghi",
                "unit": "pcs",
                "part_type": "Seal",
                "parameter_label": "diameter",
                "parameter_value": "2",
                "parameter_unit": "inch",
            },
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    different_size = asyncio.run(
        post_json(
            "/inventory/parts",
            {
                "sku": "DELONGHI-SEAL-4IN",
                "name": "Уплотнительное кольцо DeLonghi 4 дюйма",
                "brand": "DeLonghi",
                "unit": "pcs",
                "part_type": "seal",
                "parameter_label": "diameter",
                "parameter_value": "4",
                "parameter_unit": "inch",
            },
            token=token,
            inventory_repository=inventory_repository,
        )
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Part with the same factual key already exists"
    assert different_size.status_code == 201


def test_inventory_part_compatibility_can_target_models_series_and_generic_groups() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))
    create_response = asyncio.run(
        post_json(
            "/inventory/parts",
            {"sku": "E61-GASKET-73", "name": "E61 group gasket 73mm", "unit": "pcs", "part_type": "seal"},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    part_id = int(create_response.json()["part_id"])

    exact = asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/compatibility",
            {"compatibility_level": "exact_model", "brand": "Rocket", "model": "Appartamento", "note": "Check thickness."},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    generic = asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/compatibility",
            {"compatibility_level": "generic_group", "machine_family": "E61 group"},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    parts = asyncio.run(get_json("/inventory/parts", token=token, inventory_repository=inventory_repository))

    assert exact.status_code == 201
    assert generic.status_code == 201
    assert parts.json()["items"][0]["compatibility"][0]["brand"] == "Rocket"
    assert parts.json()["items"][0]["compatibility"][1]["machine_family"] == "E61 group"


def test_inventory_part_compatibility_requires_fields_for_selected_level() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))
    create_response = asyncio.run(
        post_json(
            "/inventory/parts",
            {"sku": "E61-GASKET-74", "name": "E61 group gasket 74mm", "unit": "pcs", "part_type": "seal"},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    part_id = int(create_response.json()["part_id"])

    missing_model = asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/compatibility",
            {"compatibility_level": "exact_model", "brand": "Rocket"},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    missing_series = asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/compatibility",
            {"compatibility_level": "series", "brand": "Jura"},
            token=token,
            inventory_repository=inventory_repository,
        )
    )
    missing_group = asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/compatibility",
            {"compatibility_level": "generic_group", "brand": "Rocket"},
            token=token,
            inventory_repository=inventory_repository,
        )
    )

    assert missing_model.status_code == 422
    assert missing_series.status_code == 422
    assert missing_group.status_code == 422


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


def test_dispatcher_can_view_low_stock_without_inventory_write_access() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    inventory_token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))
    dispatcher_token = asyncio.run(staff_token("dispatcher@coffeefix.local", "dispatcher-local"))
    create_response = asyncio.run(
        post_json(
            "/inventory/parts",
            {"sku": "E61-LOW", "name": "Low stock gasket", "unit": "pcs"},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    part_id = int(create_response.json()["part_id"])
    asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/stock",
            {"quantity_on_hand": 1, "low_stock_threshold": 2},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )

    low_stock = asyncio.run(get_json("/inventory/low-stock", token=dispatcher_token, inventory_repository=inventory_repository))
    wrong_write = asyncio.run(
        post_json(
            "/inventory/reservations",
            {"request_number": "CFX-20260607-000001", "part_id": part_id, "quantity": 1},
            token=dispatcher_token,
            inventory_repository=inventory_repository,
        )
    )

    assert low_stock.status_code == 200
    assert low_stock.json()["items"][0]["sku"] == "E61-LOW"
    assert wrong_write.status_code == 403


def test_technician_can_view_parts_catalog_without_inventory_write_access() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    inventory_token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))
    technician_token = asyncio.run(staff_token("technician@coffeefix.local", "technician-local"))
    create_response = asyncio.run(
        post_json(
            "/inventory/parts",
            {"sku": "E61-TECH", "name": "Technician visible gasket", "unit": "pcs"},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    part_id = int(create_response.json()["part_id"])

    catalog = asyncio.run(get_json("/inventory/parts", token=technician_token, inventory_repository=inventory_repository))
    wrong_write = asyncio.run(
        post_json(
            f"/inventory/parts/{part_id}/stock",
            {"quantity_on_hand": 2},
            token=technician_token,
            inventory_repository=inventory_repository,
        )
    )

    assert catalog.status_code == 200
    assert catalog.json()["items"][0]["sku"] == "E61-TECH"
    assert wrong_write.status_code == 403
