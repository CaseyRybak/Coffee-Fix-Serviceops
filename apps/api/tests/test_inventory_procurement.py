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
    service_request_repository: ServiceRequestRepository | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=service_request_repository or ServiceRequestRepository.in_memory(),
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
    service_request_repository: ServiceRequestRepository | None = None,
) -> httpx.Response:
    app = create_app(
        service_request_repository=service_request_repository or ServiceRequestRepository.in_memory(),
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


def test_inventory_repository_procurement_state_machine_receiving_and_low_stock_draft() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, PurchaseRequestItemPayload, SupplierPayload
    from serviceops_api.inventory.repository import InvalidPurchaseRequestTransitionError
    from serviceops_api.inventory.use_cases import CreatePart, CreateSupplier, CreatePurchaseRequest, CreateLowStockPurchaseDraft, SetStockCount

    repository = SqliteInventoryRepository.in_memory()
    pump = CreatePart(repository).execute(CreatePartPayload(sku="PUMP-01", name="Pump", unit="pcs"))
    gasket = CreatePart(repository).execute(CreatePartPayload(sku="GASKET-01", name="Group gasket", unit="pcs"))
    SetStockCount(repository).execute(pump.part_id, quantity_on_hand=1, low_stock_threshold=3)
    SetStockCount(repository).execute(gasket.part_id, quantity_on_hand=8, low_stock_threshold=2)
    supplier = CreateSupplier(repository).execute(SupplierPayload(name="Parts Partner", contact_name="Mira", phone="+100"))

    draft = CreatePurchaseRequest(repository, actor="inventory@coffeefix.local").execute(
        supplier_id=supplier.supplier_id,
        items=[PurchaseRequestItemPayload(part_id=pump.part_id, quantity=4, note="Reorder pumps")],
        note="Manual purchase",
    )
    pending = repository.submit_purchase_request(draft.purchase_request_id, actor="inventory@coffeefix.local")
    approved = repository.approve_purchase_request(pending["purchase_request_id"], actor="admin@coffeefix.local")
    ordered = repository.mark_purchase_request_ordered(approved["purchase_request_id"], actor="inventory@coffeefix.local")
    low_stock_draft = CreateLowStockPurchaseDraft(repository, actor="inventory@coffeefix.local").execute(supplier.supplier_id)
    received = repository.receive_purchase_request(ordered["purchase_request_id"], actor="inventory@coffeefix.local", note="Box arrived")
    stock = repository.get_stock_count(pump.part_id)
    movements = repository.list_stock_movements(part_id=pump.part_id)

    assert received["status"] == "received"
    assert stock["quantity_on_hand"] == 5
    assert movements[0]["movement_type"] == "procurement_receipt"
    assert movements[0]["quantity"] == 4
    assert low_stock_draft.items[0].part_id == pump.part_id
    assert low_stock_draft.items[0].quantity == 5
    assert all(item.part_id != gasket.part_id for item in low_stock_draft.items)

    try:
        repository.cancel_purchase_request(received["purchase_request_id"], actor="inventory@coffeefix.local")
    except InvalidPurchaseRequestTransitionError:
        pass
    else:
        raise AssertionError("received purchase requests must not be cancellable")


def test_inventory_procurement_blocks_invalid_transitions_and_non_draft_item_edits() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, PurchaseRequestItemPayload, SupplierPayload
    from serviceops_api.inventory.repository import InvalidPurchaseRequestTransitionError
    from serviceops_api.inventory.use_cases import CreatePart, CreatePurchaseRequest, CreateSupplier, SetStockCount

    repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(repository).execute(CreatePartPayload(sku="VALVE-02", name="Valve", unit="pcs"))
    SetStockCount(repository).execute(part.part_id, quantity_on_hand=1, low_stock_threshold=2)
    supplier = CreateSupplier(repository).execute(SupplierPayload(name="Transition Supplier"))
    draft = CreatePurchaseRequest(repository).execute(
        supplier_id=supplier.supplier_id,
        items=[PurchaseRequestItemPayload(part_id=part.part_id, quantity=2)],
    )

    try:
        repository.receive_purchase_request(draft.purchase_request_id, actor="inventory")
    except InvalidPurchaseRequestTransitionError:
        pass
    else:
        raise AssertionError("draft purchase requests must not be received")

    assert repository.get_stock_count(part.part_id)["quantity_on_hand"] == 1

    pending = repository.submit_purchase_request(draft.purchase_request_id, actor="inventory")
    try:
        repository.replace_purchase_request_items(
            int(pending["purchase_request_id"]),
            [PurchaseRequestItemPayload(part_id=part.part_id, quantity=3)],
            actor="inventory",
        )
    except InvalidPurchaseRequestTransitionError:
        pass
    else:
        raise AssertionError("pending purchase request items must not be editable")

    unchanged = repository.get_purchase_request(int(pending["purchase_request_id"]))
    assert unchanged["items"][0]["quantity"] == 2


def test_inventory_repository_rejects_non_positive_purchase_item_quantities() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, SupplierPayload
    from serviceops_api.inventory.use_cases import CreatePart, CreateSupplier

    repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(repository).execute(CreatePartPayload(sku="BURR-01", name="Burr set", unit="pcs"))
    supplier = CreateSupplier(repository).execute(SupplierPayload(name="Validation Supplier"))

    try:
        repository.create_purchase_request(
            supplier.supplier_id,
            [{"part_id": part.part_id, "quantity": 0, "note": "bad quantity"}],
            None,
            "inventory",
        )
    except ValueError as exc:
        assert "quantity" in str(exc).lower()
    else:
        raise AssertionError("purchase request quantities must be positive at repository boundary")


def test_postgres_procurement_migration_extends_stock_movement_constraint() -> None:
    from pathlib import Path

    migration = Path("src/serviceops_api/migrations/0013_procurement_lite.sql").read_text(encoding="utf-8")

    assert "DROP CONSTRAINT IF EXISTS stock_movements_movement_type_check" in migration
    assert "procurement_receipt" in migration


def test_postgres_purchase_transitions_lock_request_rows() -> None:
    from pathlib import Path

    source = Path("src/serviceops_api/inventory/repository.py").read_text(encoding="utf-8")

    assert "FOR UPDATE OF pr" in source
    assert "current = self._purchase_request_row(self._get_purchase_request_for_update(connection, purchase_request_id))" in source


def test_postgres_procurement_receiving_uses_atomic_stock_increment() -> None:
    from pathlib import Path

    source = Path("src/serviceops_api/inventory/repository.py").read_text(encoding="utf-8")

    assert "quantity_on_hand = stock_counts.quantity_on_hand + excluded.quantity_on_hand" in source


def test_postgres_purchase_item_insert_uses_cursor_executemany() -> None:
    from serviceops_api.inventory.models import PurchaseRequestItemPayload
    from serviceops_api.inventory.repository import PostgresInventoryRepository

    class CursorRecorder:
        def __init__(self) -> None:
            self.executemany_calls: list[tuple[str, list[tuple[object, ...]]]] = []

        def __enter__(self) -> "CursorRecorder":
            return self

        def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
            return None

        def executemany(self, query: str, params: list[tuple[object, ...]]) -> None:
            self.executemany_calls.append((query, params))

    class ConnectionWithoutExecutemany:
        def __init__(self) -> None:
            self.cursor_recorder = CursorRecorder()

        def cursor(self) -> CursorRecorder:
            return self.cursor_recorder

    repository = PostgresInventoryRepository("postgresql://unused", initialize=False)
    connection = ConnectionWithoutExecutemany()

    repository._insert_purchase_items(  # noqa: SLF001 - regression covers PostgreSQL adapter boundary.
        connection,  # type: ignore[arg-type]
        42,
        [PurchaseRequestItemPayload(part_id=7, quantity=3, note="Smoke item")],
    )

    assert connection.cursor_recorder.executemany_calls
    assert connection.cursor_recorder.executemany_calls[0][1] == [(42, 7, 3, "Smoke item")]


def test_inventory_procurement_api_authorization_and_public_boundary() -> None:
    inventory_repository = SqliteInventoryRepository.in_memory()
    service_repository = ServiceRequestRepository.in_memory()
    inventory_token = asyncio.run(staff_token("inventory@coffeefix.local", "inventory-local"))
    admin_token = asyncio.run(staff_token("admin@coffeefix.local", "admin-local"))
    dispatcher_token = asyncio.run(staff_token("dispatcher@coffeefix.local", "dispatcher-local"))

    intake = asyncio.run(
        post_json(
            "/service-requests",
            {
                "customer": {"name": "Demo Customer", "phone": "+1000000000", "client_type": "private"},
                "machine": {"brand": "Rocket", "location_type": "home"},
                "problem": "No steam",
                "address": "Demo street",
                "urgency": "planned",
            },
            service_request_repository=service_repository,
        )
    )
    request_number = str(intake.json()["request_number"])

    create_part = asyncio.run(
        post_json(
            "/inventory/parts",
            {"sku": "VALVE-01", "name": "Steam valve", "unit": "pcs"},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    part_id = int(create_part.json()["part_id"])
    supplier = asyncio.run(
        post_json(
            "/inventory/procurement/suppliers",
            {"name": "Supplier One", "contact_name": "Nora", "phone": "+101"},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    purchase = asyncio.run(
        post_json(
            "/inventory/procurement/purchase-requests",
            {"supplier_id": supplier.json()["supplier_id"], "items": [{"part_id": part_id, "quantity": 2}], "note": "Need valves"},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    purchase_id = int(purchase.json()["purchase_request_id"])
    forbidden_approval = asyncio.run(
        post_json(
            f"/inventory/procurement/purchase-requests/{purchase_id}/approve",
            {},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    dispatcher_create = asyncio.run(
        post_json(
            "/inventory/procurement/suppliers",
            {"name": "Wrong Role Supplier"},
            token=dispatcher_token,
            inventory_repository=inventory_repository,
        )
    )
    submit = asyncio.run(
        post_json(
            f"/inventory/procurement/purchase-requests/{purchase_id}/submit",
            {},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    approve = asyncio.run(
        post_json(
            f"/inventory/procurement/purchase-requests/{purchase_id}/approve",
            {},
            token=admin_token,
            inventory_repository=inventory_repository,
        )
    )
    ordered = asyncio.run(
        post_json(
            f"/inventory/procurement/purchase-requests/{purchase_id}/mark-ordered",
            {},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    received = asyncio.run(
        post_json(
            f"/inventory/procurement/purchase-requests/{purchase_id}/receive",
            {"note": "Received from API"},
            token=inventory_token,
            inventory_repository=inventory_repository,
        )
    )
    public_status = asyncio.run(
        get_json(
            f"/service-requests/{request_number}/status",
            service_request_repository=service_repository,
        )
    )

    assert supplier.status_code == 201
    assert purchase.status_code == 201
    assert forbidden_approval.status_code == 403
    assert dispatcher_create.status_code == 403
    assert submit.json()["status"] == "pending_approval"
    assert approve.json()["status"] == "approved"
    assert ordered.json()["status"] == "ordered"
    assert received.json()["status"] == "received"
    assert inventory_repository.get_stock_count(part_id)["quantity_on_hand"] == 2
    public_body = public_status.json()
    assert "supplier" not in public_body
    assert "purchase" not in public_body
    assert "stock" not in public_body
