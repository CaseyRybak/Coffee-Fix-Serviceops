# Phase 08 Technician And Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a protected technician workspace for assigned visits and a basic inventory slice that tracks catalog parts, stock counts, and parts used on service requests.

**Architecture:** Add bounded `technicians` and `inventory` API modules while keeping service-request lifecycle updates in the existing service-request repository boundary. Technician actions use the `technician` staff role, inventory management uses the `inventory` staff role, and technician parts usage coordinates inventory stock changes with request status history through application services. The web app gains protected `/technician` and `/inventory` workspaces without exposing either route in public navigation.

**Tech Stack:** Python, FastAPI, Pydantic, sqlite3, psycopg, PostgreSQL migration SQL, pytest/httpx, React, Vite, TypeScript, node:test.

---

## Scope Decisions

- Phase 08 implements assigned-work visibility, diagnosis checklist capture, repair result capture, parts catalog basics, stock count basics, and parts-used recording.
- Phase 08 does not implement technician availability calendars, automatic dispatch matching, appointment rescheduling rules, barcode scanning, purchase orders, warehouses, supplier pricing, billing totals, warranty claim processing, or customer payment collection.
- Technician request lists are derived from Phase 04 assignment metadata on service requests. A request appears for a technician when `assigned_technician_name` matches the staff user's display name or username fallback.
- Technician actions append status events with actor `technician` and use existing request statuses: `diagnostics`, `waiting_for_parts`, `repair_in_progress`, and `completed`.
- Parts used on a request decrement stock immediately in this MVP. If available stock is insufficient, the API returns a validation error and does not create the usage record.
- Basic catalog compatibility is descriptive: brand and model text are stored with a part, but compatibility matching and AI-assisted reservation remain future slices.

## File Responsibility Map

- Create: `apps/api/src/serviceops_api/inventory/__init__.py` for inventory package exports.
- Create: `apps/api/src/serviceops_api/inventory/models.py` for part, stock, and parts-used DTOs.
- Create: `apps/api/src/serviceops_api/inventory/repository.py` for sqlite and PostgreSQL inventory repositories.
- Create: `apps/api/src/serviceops_api/inventory/use_cases.py` for catalog, stock, and parts-used services.
- Create: `apps/api/src/serviceops_api/inventory/api.py` for protected inventory and technician parts routes.
- Create: `apps/api/src/serviceops_api/technicians/__init__.py` for technician package exports.
- Create: `apps/api/src/serviceops_api/technicians/models.py` for technician request list/detail/action DTOs.
- Create: `apps/api/src/serviceops_api/technicians/use_cases.py` for assigned-visit list, detail, diagnosis, and result services.
- Create: `apps/api/src/serviceops_api/technicians/api.py` for protected technician routes.
- Create: `apps/api/src/serviceops_api/migrations/0004_technician_inventory.sql` for PostgreSQL catalog, stock, diagnosis, result, and parts-used tables.
- Modify: `apps/api/src/serviceops_api/service_requests/models.py` to expose technician action snapshots on internal technician detail.
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py` to add request lookup by assigned technician and technician status-event helpers.
- Modify: `apps/api/src/serviceops_api/service_requests/use_cases.py` to add ports used by technician workflows without leaking inventory details into service-request models.
- Modify: `apps/api/src/serviceops_api/main.py` to wire inventory and technician repositories, use cases, and protected routers.
- Create: `apps/api/tests/test_inventory_parts.py` for catalog, stock, parts-used, and repository selection coverage.
- Create: `apps/api/tests/test_technician_workflow.py` for technician list/detail/actions and public/private separation.
- Modify: `apps/api/tests/test_repository_selection.py` to cover inventory repository selection.
- Modify: `apps/web/src/App.tsx` to add technician and inventory route helpers, protected pages, API helpers, and compact workspaces.
- Modify: `apps/web/src/App.test.tsx` to cover technician and inventory rendering, path helpers, role guards, and public-navigation isolation.
- Modify: `apps/web/src/styles.css` to add work-focused technician and inventory workspace styles.
- Modify: `domains/technicians/domain.md`, `domains/scheduling/domain.md`, `domains/inventory/domain.md`, and `domains/service-requests/domain.md` to record Phase 08 behavior and boundaries.
- Modify: `docs/harness/repository-map.md` and `tools/repo-checks/check_docs.py` after implementation artifacts exist.
- Modify: `project_notes.md` and `docs/execution-plans/index.md` after implementation to mark Phase 09 active.
- Create: `docs/review/phase-08-review.md` after verification and review.

## Task 1: Inventory Models And Persistence

**Files:**
- Create: `apps/api/src/serviceops_api/inventory/__init__.py`
- Create: `apps/api/src/serviceops_api/inventory/models.py`
- Create: `apps/api/src/serviceops_api/inventory/repository.py`
- Create: `apps/api/src/serviceops_api/migrations/0004_technician_inventory.sql`
- Create: `apps/api/tests/test_inventory_parts.py`
- Modify: `apps/api/tests/test_repository_selection.py`

- [ ] **Step 1: Write failing inventory persistence tests**

Create `apps/api/tests/test_inventory_parts.py` with tests for:
- creating a part with `sku`, `name`, optional `brand`, optional `model`, and `unit`;
- setting stock count for a part;
- recording parts used on request `CFX-20260607-000001`;
- rejecting usage that exceeds stock;
- listing parts used by request.

Use this first test shape:

```python
def test_inventory_repository_records_stock_and_parts_used() -> None:
    from serviceops_api.inventory.models import CreatePartPayload, RecordPartsUsedPayload
    from serviceops_api.inventory.repository import SqliteInventoryRepository
    from serviceops_api.inventory.use_cases import CreatePart, RecordPartsUsed, SetStockCount

    repository = SqliteInventoryRepository.in_memory()
    part = CreatePart(repository).execute(
        CreatePartPayload(sku="E61-GASKET-73", name="E61 group gasket 73mm", brand="Rocket", model="Appartamento", unit="pcs")
    )
    SetStockCount(repository).execute(part.part_id, quantity_on_hand=4)

    result = RecordPartsUsed(repository).execute(
        "CFX-20260607-000001",
        RecordPartsUsedPayload(part_id=part.part_id, quantity=2, note="Changed worn gasket"),
    )

    assert result.request_number == "CFX-20260607-000001"
    assert result.quantity_on_hand == 2
    assert repository.list_parts_used("CFX-20260607-000001")[0]["part_name"] == "E61 group gasket 73mm"
```

Run: `cd apps/api && uv run --extra dev pytest tests/test_inventory_parts.py -q`

Expected: fails because `serviceops_api.inventory` does not exist.

- [ ] **Step 2: Add inventory models**

In `models.py`, define Pydantic models:
- `CreatePartPayload` with required trimmed `sku`, `name`, `unit`, optional `brand`, optional `model`, and optional `compatibility_note`;
- `PartRecord` with `part_id`, catalog fields, and `created_at`;
- `StockSnapshot` with `part_id`, `quantity_on_hand`, and `updated_at`;
- `RecordPartsUsedPayload` with `part_id`, positive `quantity`, and optional `note`;
- `PartsUsedRecord` with request number, part fields, quantity, note, stock after use, and created time.

- [ ] **Step 3: Add PostgreSQL migration**

Create `0004_technician_inventory.sql` with tables:
- `parts_catalog`: id, sku unique, name, brand, model, unit, compatibility_note, created_at;
- `stock_counts`: part_id primary key, quantity_on_hand, updated_at;
- `request_parts_used`: id, request_number, part_id, quantity, note, actor, created_at.

Add indexes on `parts_catalog.sku`, `request_parts_used.request_number`, and `request_parts_used.part_id`.

- [ ] **Step 4: Implement inventory repositories**

Implement `InventoryStore` protocol, `SqliteInventoryRepository`, `PostgresInventoryRepository`, and `create_inventory_repository(settings, initialize=True)`.

Required methods:
- `create_part(payload) -> dict[str, object]`;
- `list_parts() -> list[dict[str, object]]`;
- `set_stock_count(part_id, quantity_on_hand) -> dict[str, object]`;
- `get_stock_count(part_id) -> dict[str, object]`;
- `record_parts_used(request_number, part_id, quantity, note, actor) -> dict[str, object]`;
- `list_parts_used(request_number) -> list[dict[str, object]]`.

- [ ] **Step 5: Add repository selection tests**

Extend `apps/api/tests/test_repository_selection.py` to assert:
- PostgreSQL URLs create `PostgresInventoryRepository`;
- sqlite memory URLs create `SqliteInventoryRepository`;
- unsupported URLs raise `ValueError` with `Unsupported SERVICEOPS_DATABASE_URL`.

- [ ] **Step 6: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_inventory_parts.py tests/test_repository_selection.py -q`

Expected: passes.

## Task 2: Inventory API

**Files:**
- Create: `apps/api/src/serviceops_api/inventory/api.py`
- Create: `apps/api/src/serviceops_api/inventory/use_cases.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/tests/test_inventory_parts.py`

- [ ] **Step 1: Write failing protected API tests**

Add tests that:
- login as `inventory@coffeefix.local` with password `inventory-local`;
- `POST /inventory/parts` creates a catalog part;
- `POST /inventory/parts/{part_id}/stock` sets stock;
- `GET /inventory/parts` returns stock snapshots;
- dispatcher-only or unauthenticated calls are rejected.

Run: `cd apps/api && uv run --extra dev pytest tests/test_inventory_parts.py -q`

Expected: fails because `/inventory` routes are missing.

- [ ] **Step 2: Implement inventory use cases**

Add `CreatePart`, `ListParts`, and `SetStockCount`. Keep validation in Pydantic models and persistence invariants in the repository.

- [ ] **Step 3: Implement protected inventory router**

Create `create_inventory_router(create_part, list_parts, set_stock_count, staff_dependency)` with:
- `GET /inventory/parts`;
- `POST /inventory/parts`;
- `POST /inventory/parts/{part_id}/stock`.

Wire the router in `main.py` with `require_staff_role("inventory", authenticator)`.

- [ ] **Step 4: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_inventory_parts.py -q`

Expected: passes.

## Task 3: Technician Service-Request Workflow

**Files:**
- Create: `apps/api/src/serviceops_api/technicians/__init__.py`
- Create: `apps/api/src/serviceops_api/technicians/models.py`
- Create: `apps/api/src/serviceops_api/technicians/use_cases.py`
- Create: `apps/api/src/serviceops_api/technicians/api.py`
- Modify: `apps/api/src/serviceops_api/service_requests/models.py`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/src/serviceops_api/service_requests/use_cases.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Create: `apps/api/tests/test_technician_workflow.py`

- [ ] **Step 1: Write failing technician workflow tests**

Create `apps/api/tests/test_technician_workflow.py` with tests that:
- create a service request;
- assign `technician@coffeefix.local` from dispatcher API;
- login as the technician;
- list assigned visits through `GET /technician/service-requests`;
- load detail through `GET /technician/service-requests/{request_number}`;
- submit diagnosis checklist through `POST /technician/service-requests/{request_number}/diagnosis`;
- submit repair result through `POST /technician/service-requests/{request_number}/result`;
- confirm the public status timeline shows technician status events but not technician-only checklist notes.

Run: `cd apps/api && uv run --extra dev pytest tests/test_technician_workflow.py -q`

Expected: fails because `serviceops_api.technicians` does not exist.

- [ ] **Step 2: Add technician models**

Define:
- `TechnicianRequestListItem`;
- `TechnicianRequestListResponse`;
- `TechnicianRequestDetail`;
- `DiagnosisChecklistPayload` with booleans for `machine_powered_on`, `water_supply_checked`, `leak_checked`, `error_code_checked`, and a required trimmed `summary`;
- `RepairResultPayload` with `result` as `completed`, `waiting_for_parts`, or `follow_up_required`, required trimmed `summary`, and optional `next_step`;
- `TechnicianActionResponse`.

- [ ] **Step 3: Extend service-request repository port**

Add repository methods:
- `list_requests_for_technician(technician_identifier)`;
- `get_technician_request(request_number, technician_identifier)`;
- `record_technician_diagnosis(request_number, checklist, summary, actor)`;
- `record_technician_result(request_number, result, summary, next_step, actor)`.

Persist diagnosis and result snapshots in sqlite helper tables and PostgreSQL migration `0004_technician_inventory.sql`.

- [ ] **Step 4: Implement technician use cases and router**

Add `ListTechnicianRequests`, `GetTechnicianRequest`, `RecordTechnicianDiagnosis`, and `RecordTechnicianResult`.

Create routes under `/technician/service-requests` and protect them with `require_staff_role("technician", authenticator)`.

- [ ] **Step 5: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_technician_workflow.py tests/test_dispatcher_requests.py tests/test_service_request_status.py -q`

Expected: passes.

## Task 4: Technician Parts Used Integration

**Files:**
- Modify: `apps/api/src/serviceops_api/inventory/api.py`
- Modify: `apps/api/src/serviceops_api/inventory/use_cases.py`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/tests/test_inventory_parts.py`
- Modify: `apps/api/tests/test_technician_workflow.py`

- [ ] **Step 1: Write failing integration tests**

Add tests that:
- seed a part and stock count;
- assign a request to the technician;
- `POST /technician/service-requests/{request_number}/parts-used` records usage;
- stock count decreases;
- service request status moves to `repair_in_progress`;
- timeline receives actor `technician`;
- insufficient stock returns HTTP 422 and leaves stock unchanged.

Run: `cd apps/api && uv run --extra dev pytest tests/test_inventory_parts.py tests/test_technician_workflow.py -q`

Expected: fails because the technician parts-used route is missing.

- [ ] **Step 2: Implement parts-used use case**

Add `RecordTechnicianPartsUsed` that:
- verifies the request is assigned to the current technician;
- records parts usage through `InventoryStore`;
- appends a service-request status event with status `repair_in_progress`, title `Запчасти использованы`, and actor `technician`.

- [ ] **Step 3: Implement route**

Add `POST /technician/service-requests/{request_number}/parts-used` to the technician router.

- [ ] **Step 4: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_inventory_parts.py tests/test_technician_workflow.py -q`

Expected: passes.

## Task 5: Technician And Inventory Web Workspaces

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Write failing web tests**

Extend `apps/web/src/App.test.tsx` to cover:
- `buildTechnicianListPath()`;
- `buildTechnicianDetailPath(requestNumber)`;
- `buildTechnicianDiagnosisPath(requestNumber)`;
- `buildTechnicianResultPath(requestNumber)`;
- `buildTechnicianPartsUsedPath(requestNumber)`;
- `buildInventoryPartsPath()`;
- `buildInventoryStockPath(partId)`;
- technician route guard requires `technician` role;
- inventory route guard requires `inventory` role;
- public page does not link to `/technician` or `/inventory`;
- technician page renders assigned visit cards, diagnosis checklist, repair result form, and parts-used form;
- inventory page renders catalog creation and stock count controls.

Run: `npm run web:test`

Expected: fails because the helpers and pages are missing.

- [ ] **Step 2: Add route helpers and types**

Add TypeScript interfaces matching the API DTOs and exported path builders for technician and inventory routes.

- [ ] **Step 3: Add protected pages**

Add:
- `ProtectedTechnicianPage`;
- `TechnicianPage`;
- `ProtectedInventoryPage`;
- `InventoryPage`.

Use the existing staff session storage and `staffAuthHeaders` helpers. Keep these workspaces compact, operational, and separate from public marketing chrome.

- [ ] **Step 4: Add route switching**

Update `App()` so:
- `/technician` renders `ProtectedTechnicianPage`;
- `/inventory` renders `ProtectedInventoryPage`;
- `/staff/login` remains the shared staff login route.

- [ ] **Step 5: Style workspaces**

Add workspace styles that keep lists, detail panes, forms, checklist controls, and stock table readable on desktop and mobile. Avoid public landing-page hero treatment inside staff workspaces.

- [ ] **Step 6: Verify**

Run:

```bash
npm run web:test
npm run web:lint
npm run web:build
```

Expected: all pass.

## Task 6: Documentation, Harness, And Review Prep

**Files:**
- Modify: `domains/technicians/domain.md`
- Modify: `domains/scheduling/domain.md`
- Modify: `domains/inventory/domain.md`
- Modify: `domains/service-requests/domain.md`
- Modify: `docs/harness/repository-map.md`
- Modify: `tools/repo-checks/check_docs.py`
- Modify: `project_notes.md`
- Modify: `docs/execution-plans/index.md`
- Create: `docs/review/phase-08-review.md`

- [ ] **Step 1: Update domain docs**

Record Phase 08 behavior:
- technicians own assigned visit workflow and action capture;
- scheduling remains a simple visit-window reference, not a calendar engine;
- inventory owns catalog, stock count, and parts-used records;
- service requests receive technician status events and keep public snapshots customer-safe.

- [ ] **Step 2: Update harness docs and checks**

Add Phase 08 implementation artifacts to `docs/harness/repository-map.md` and `tools/repo-checks/check_docs.py` once files exist:
- detailed Phase 08 plan;
- inventory module files and tests;
- technician module files and tests;
- migration `0004_technician_inventory.sql`;
- Phase 08 review artifact.

- [ ] **Step 3: Update operational status**

After implementation and review, update `project_notes.md` to mark Phase 08 complete and Phase 09 active. Update `docs/execution-plans/index.md` so active phase is `phases/09-deployment-and-operations.md` and detailed Phase 08 is listed as completed.

- [ ] **Step 4: Run full verification**

Run:

```bash
python3 tools/repo-checks/check_docs.py
cd apps/api && uv run --extra dev pytest
cd ../worker && uv run --extra dev pytest
cd ../telegram-bot && uv run --extra dev pytest
cd ../..
npm run web:test
npm run web:lint
npm run web:build
```

Expected: all pass.

- [ ] **Step 5: Prepare subagent review**

Create `docs/review/phase-08-review.md` using `docs/review/subagent-review-protocol.md`. Include changed files, verification output, findings grouped by blocking issues, non-blocking issues, suggested follow-up slice, documentation updates needed, and final recommendation.

## Review Handoff

Before implementation starts, review this plan against `docs/execution-plans/phases/08-technician-and-inventory.md`. The review should specifically check mobile workflow practicality, inventory consistency, technician-driven request history, and whether deferred scheduling, billing, and warehouse features stayed deferred.
