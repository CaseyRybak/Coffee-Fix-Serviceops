# Phase 16 Inventory Reservations Implementation Plan

## Goal

Connect the existing inventory basics to service execution with request-level reservations, stock movement audit records, available/reserved stock visibility, low-stock indicators, structured part identity, duplicate protection, and compatibility metadata.

## Design

- Keep inventory logic inside `serviceops_api.inventory`.
- Add `part_reservations` for active/released/consumed request reservations.
- Add `stock_movements` as the durable audit trail for manual adjustment, reservation, release, and consumption.
- Add part identity fields and a factual-key uniqueness guard for true duplicate prevention without fuzzy name blocking.
- Add `part_compatibility` rows for exact model, series, and generic machine-group compatibility.
- Keep public service-request snapshots unchanged: inventory remains staff-only.
- Extend existing inventory part list DTOs with `reserved_quantity`, `available_quantity`, `low_stock_threshold`, and `is_low_stock`.
- Use request number as the primary reservation link; appointment id remains optional metadata.
- Technician parts usage consumes active reservations for the same request/part first, then available unreserved stock if needed.

## Files

- Modify `apps/api/src/serviceops_api/inventory/models.py`
- Modify `apps/api/src/serviceops_api/inventory/repository.py`
- Modify `apps/api/src/serviceops_api/inventory/use_cases.py`
- Modify `apps/api/src/serviceops_api/inventory/api.py`
- Modify `apps/api/src/serviceops_api/main.py`
- Add `apps/api/src/serviceops_api/migrations/0008_inventory_reservations.sql`
- Add `apps/api/src/serviceops_api/migrations/0009_part_compatibility.sql`
- Modify `apps/api/tests/test_inventory_parts.py`
- Modify `apps/api/tests/test_technician_workflow.py`
- Modify `apps/web/src/App.tsx`
- Modify `apps/web/src/App.test.tsx`
- Modify `apps/web/src/styles.css`
- Modify `domains/inventory/domain.md`
- Modify `domains/service-requests/domain.md`
- Modify `domains/technicians/domain.md`
- Modify `project_notes.md`
- Modify `docs/execution-plans/index.md`

## Tasks

1. Add failing backend tests for reservation create/adjust/release, movement history, low-stock fields, role protection, technician consumption of reserved parts, duplicate factual part keys, and compatibility rows.
2. Add migration and sqlite initialization for reservation/movement tables, low-stock threshold, part identity fields, and compatibility rows.
3. Extend inventory models/use cases/API with reservation, movement, duplicate-protected part creation, and compatibility contracts.
4. Implement repository behavior for available stock, reservation lifecycle, movement audit, technician reserved consumption, factual-key checks, and compatibility listing.
5. Extend inventory UI to show on-hand/reserved/available/low-stock, provide reservation/release/movement views, dependent catalog-entry controls, duplicate warnings, and compatibility entry.
6. Update docs and project notes.
7. Run verification: API inventory/technician tests, full API suite, web lint/test/build, docs check.
8. Request subagent review before marking the slice complete.

## Verification Commands

- `cd apps/api && uv run --extra dev pytest tests/test_inventory_parts.py tests/test_technician_workflow.py -v`
- `cd apps/api && uv run --extra dev pytest`
- `npm run web:lint`
- `npm run web:test`
- `npm run web:build`
- `python3 tools/repo-checks/check_docs.py`

## Deferred

- Multi-warehouse stock.
- Purchase orders and suppliers.
- Pricing/billing.
- Barcode scanning.
- AI-created reservations.
- PostgreSQL concurrency locks beyond transactional repository operations.
