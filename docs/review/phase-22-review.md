# Phase 22 Review: Procurement Lite

## Reviewer Role

Independent subagent review after implementation and local verification. Three auditors reviewed:

- Backend/data consistency: procurement state transitions, stock receiving, PostgreSQL deployability, authorization, public/private separation.
- Frontend/RBAC workflow: inventory/admin procurement UX, role-specific affordances, route discovery, public navigation boundaries.
- Plan/docs compliance: phase acceptance criteria, dashboard/index consistency, review artifact requirements, verification evidence.

## Files Reviewed

- `docs/execution-plans/phases/22-procurement-lite.md`
- `docs/execution-plans/detailed/22-procurement-lite-implementation.md`
- `apps/api/src/serviceops_api/inventory/models.py`
- `apps/api/src/serviceops_api/inventory/repository.py`
- `apps/api/src/serviceops_api/inventory/use_cases.py`
- `apps/api/src/serviceops_api/inventory/api.py`
- `apps/api/src/serviceops_api/main.py`
- `apps/api/src/serviceops_api/migrations/0013_procurement_lite.sql`
- `apps/api/tests/test_inventory_procurement.py`
- `apps/web/src/features/inventory/InventoryPage.tsx`
- `apps/web/src/features/staff-auth/StaffWorkspacePage.tsx`
- `apps/web/src/shared/api.ts`
- `apps/web/src/shared/formatters.ts`
- `apps/web/src/shared/staffAuth.ts`
- `apps/web/src/shared/types.ts`
- `apps/web/src/styles.css`
- `apps/web/src/App.test.tsx`
- `domains/inventory/domain.md`
- `domains/service-requests/domain.md`
- `docs/execution-plans/index.md`
- `project_notes.md`

## Verification Commands

- `cd apps/api && uv run --extra dev pytest`  
  Result: `176 passed, 1 warning`.
- `cd apps/api && uv run --extra dev pytest tests/test_inventory_procurement.py tests/test_inventory_parts.py -q`  
  Result: `23 passed`.
- `npm run web:test`  
  Result: passed.
- `npm run web:lint`  
  Result: passed.
- `npm run web:build`  
  Result: passed.
- `cd apps/worker && uv run --extra dev pytest`  
  Result: `15 passed`.
- `cd apps/telegram-bot && uv run --extra dev pytest`  
  Result: `15 passed`.
- `python3 tools/repo-checks/check_docs.py`  
  Result: passed.
- `docker compose -f docker-compose.production.yml --env-file .env.example config --quiet`  
  Result: passed.
- `bash -n tools/operations/postgres_backup.sh`  
  Result: passed.
- `bash -n tools/operations/postgres_restore.sh`  
  Result: passed.
- `bash -n tools/operations/smoke_test.sh`  
  Result: passed.
- `python3 tools/operations/test_smoke_script_contract.py`  
  Result: passed.
- `python3 tools/operations/test_production_compose_contract.py`  
  Result: passed.

## Findings And Resolutions

### Blocking Issues

- PostgreSQL `stock_movements.movement_type` constraint did not include `procurement_receipt`.
  - Resolution: `0013_procurement_lite.sql` now drops/recreates the movement-type check constraint with `procurement_receipt`, and procurement tests assert the migration includes the constraint update.
- PostgreSQL purchase-request transitions and receiving read status before locking.
  - Resolution: PostgreSQL transition, receive, and cancel paths now lock the purchase request row with `FOR UPDATE OF pr` inside the transaction before validating state and mutating stock/status.
- Admin approval was not reliably discoverable and admin users saw inventory-only controls.
  - Resolution: `/inventory` is now a valid admin next route, the staff workspace includes an admin procurement approval card, admin-only sessions do not load inventory-only reservation/movement endpoints, and inventory-only controls are hidden from admin-only users.
- Draft item editing was missing from the staff-facing procurement UI.
  - Resolution: draft purchase requests now render an inventory-only replacement form that calls `/inventory/procurement/purchase-requests/{id}/items`.
- Procurement receiving wrote absolute stock quantities after app-level arithmetic.
  - Resolution: receiving now uses an atomic stock increment upsert for sqlite/PostgreSQL while retaining PostgreSQL row locks for existing stock rows, and procurement tests assert the PostgreSQL contract.
- Project dashboard and review artifact were inconsistent.
  - Resolution: `project_notes.md` now says completed through Phase 22, points active focus to Phase 23, links this review artifact, and the Phase 22 detailed plan has a completion note.

### Non-Blocking Issues

- Procurement actors currently use role-level defaults (`inventory`, `admin`) rather than the authenticated username in use-case construction. This is acceptable for Phase 22 lite but should be improved when staff audit depth expands.
- Purchase request statuses are still rendered as compact API values in parts of the UI. This is operationally usable, but a later polish pass can add localized labels.
- Executable PostgreSQL procurement integration tests are not wired to a local test database; current PostgreSQL-specific coverage uses migration/source-contract assertions.

## Targeted Re-Review

After blocking fixes, two targeted subagents re-reviewed the changed backend/data and frontend/RBAC/docs areas.

- Backend/data re-review: approved. No blocking issues remained for PostgreSQL `procurement_receipt` deployability, purchase-request row locking, atomic receiving increments, repository quantity validation, or regression coverage.
- Frontend/RBAC/docs re-review: approved. No blocking issues remained for admin approval discoverability, admin-safe inventory workspace behavior, draft item editing UI wording, or dashboard/review documentation consistency.

## Suggested Follow-Up Slice

Phase 23 can proceed after this review gate. Suggested future hardening:

- Pass authenticated staff usernames into procurement actors for stronger audit trails.
- Add localized purchase-request status labels.
- Consider a richer multi-line purchase request editor only if real demo/operator use shows the single-line replacement flow is too narrow.
- Add executable PostgreSQL procurement integration coverage when a disposable test database is available.

## Final Recommendation

Approved after fixes. Phase 22 satisfies the procurement-lite acceptance criteria: staff can create low-stock drafts and purchase requests, admin can approve, inventory can order/receive/cancel, receiving updates stock with auditable movement records, authorization protects internal routes, and public status snapshots remain free of procurement data.
