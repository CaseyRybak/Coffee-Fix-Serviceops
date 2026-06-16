# Phase 16 Review: Inventory Reservations

Date: 2026-06-15

## Reviewer Role

Independent phase-readiness reviewer. This review was performed after the implementation commit `03eae0b` and checked Phase 16 plan compliance, backend/API behavior, inventory consistency, technician workflow integration, public-safety boundaries, frontend coverage, documentation, and phase handoff readiness.

## Files Reviewed

- `docs/execution-plans/phases/16-inventory-reservations.md`
- `docs/execution-plans/detailed/16-inventory-reservations-implementation.md`
- `docs/execution-plans/index.md`
- `project_notes.md`
- `domains/inventory/domain.md`
- `domains/service-requests/domain.md`
- `domains/technicians/domain.md`
- `apps/api/src/serviceops_api/inventory/models.py`
- `apps/api/src/serviceops_api/inventory/repository.py`
- `apps/api/src/serviceops_api/inventory/use_cases.py`
- `apps/api/src/serviceops_api/inventory/api.py`
- `apps/api/src/serviceops_api/main.py`
- `apps/api/src/serviceops_api/technicians/api.py`
- `apps/api/src/serviceops_api/technicians/use_cases.py`
- `apps/api/src/serviceops_api/migrations/0008_inventory_reservations.sql`
- `apps/api/src/serviceops_api/migrations/0009_part_compatibility.sql`
- `apps/api/src/serviceops_api/migrations/0010_inventory_russian_catalog.sql`
- `apps/api/tests/test_inventory_parts.py`
- `apps/api/tests/test_technician_workflow.py`
- `apps/api/tests/test_service_request_status.py`
- `apps/web/src/App.tsx`
- `apps/web/src/App.test.tsx`
- `apps/web/src/styles.css`
- `tools/repo-checks/check_docs.py`

## Verification Commands

- `python3 tools/repo-checks/check_docs.py` -> passed.
- `cd apps/api && UV_CACHE_DIR=/tmp/serviceops-uv-cache uv run --extra dev pytest tests/test_inventory_parts.py tests/test_technician_workflow.py -q` -> 19 passed.
- `cd apps/api && UV_CACHE_DIR=/tmp/serviceops-uv-cache uv run --extra dev pytest -q` -> 144 passed, 1 FastAPI deprecation warning.
- `cd apps/worker && UV_CACHE_DIR=/tmp/serviceops-uv-cache uv run --extra dev pytest -q` -> 14 passed.
- `cd apps/telegram-bot && UV_CACHE_DIR=/tmp/serviceops-uv-cache uv run --extra dev pytest -q` -> 14 passed.
- `npm run web:test` -> passed.
- `npm run web:lint` -> passed.
- `npm run web:build` -> passed.
- `docker compose -f docker-compose.production.yml --env-file .env.example config` -> passed.
- `bash -n tools/operations/postgres_backup.sh` -> passed.
- `bash -n tools/operations/postgres_restore.sh` -> passed.
- `bash -n tools/operations/smoke_test.sh` -> passed.
- `python3 tools/operations/test_smoke_script_contract.py` -> passed.
- Secret scan with the documented Phase 16 pattern returned only expected false positives in documented scan commands, placeholder environment examples, shell variable references, and test assertions; no real reusable secret was found.
- `git diff --check` -> passed.

## Blocking Issues

Resolved during review:

- The implementation was marked complete in `project_notes.md` and the execution-plan index, but the required durable Phase 16 review artifact was missing. Added this review artifact.
- `tools/repo-checks/check_docs.py` still required detailed/review artifacts only through earlier phases and did not pin Phase 15/16 detailed plans, Phase 15/16 review artifacts, or the scheduling/inventory migration files. Updated the harness so future documentation checks catch this class of phase-handoff drift.
- `project_notes.md` still pointed at the Phase 14-era documentation audit as the latest current-state audit. Updated the entry-point list to include this Phase 16 review and avoid treating the older audit as the newest status source.

Re-review result: no remaining blocking issues found.

## Non-Blocking Issues

- Reservation and stock movement consistency is enforced in repository/application code. A later hardening slice should add stronger PostgreSQL transaction isolation or row-level locking around concurrent reserve/consume operations.
- SQLite remains looser than PostgreSQL on enum/check constraints. API and Pydantic validation cover normal routes, but direct repository writes are still a hardening follow-up.
- `stock_movements.movement_type = manual_adjustment` currently records the resulting on-hand quantity as the movement quantity, not a delta. This is readable as a snapshot-style audit entry but should be clarified or split into `delta_quantity`/`quantity_on_hand_after` if operators need pure delta semantics.
- Frontend tests cover render/path behavior for inventory reservations and compatibility; browser-level interaction coverage for reserve/release form flows can be added later.
- Real production smoke evidence, restore dry-run evidence, and live provider/n8n/Telegram configuration remain launch-readiness work, not Phase 16 scope.

## Post-Review Update: 2026-06-16

- The PostgreSQL row-locking follow-up is resolved for current reservation workflows: stock and reservation rows are locked before reserve/release/consume mutations, with regression coverage in `apps/api/tests/test_repository_selection.py`. SQLite remains intentionally lighter for local/test use.
- Aeza VPS/Dokploy test deployment evidence now records API/web/PostgreSQL/Redis health, migrations, first-admin bootstrap, n8n callback, backup, restore drill, and worker Redis broker fix. Public launch is still blocked on domains/HTTPS, direct test-port closure, disposable staff-route smoke, Telegram runtime review after deploy, setup-secret rotation, and real database transfer smoke checks.

## Suggested Follow-Up Slice

Backlog grooming can choose the next approved slice. Good candidates:

- Inventory consistency hardening: stricter SQLite/PostgreSQL constraint parity and clearer stock-movement delta semantics.
- Operational launch evidence: public-domain HTTPS smoke checks, disposable staff-route smoke, Telegram runtime verification, repeated backup/restore evidence after real database transfer, and log trace captures.
- Billing/estimates slice if product priority moves from service execution to commercial closure.

## Documentation Updates

Completed:

- Added this `docs/review/phase-16-review.md` artifact.
- Updated `tools/repo-checks/check_docs.py` to require Phase 15/16 detailed plans, Phase 15/16 review artifacts, and scheduling/inventory migration files.
- Updated `project_notes.md` entry points so Phase 16 review is visible from the operating dashboard.

## Final Recommendation

Phase 16 is approved to move forward after this review. The implemented slice matches the plan: request-linked reservations, reservation adjust/release, stock movement audit records, on-hand/reserved/available stock visibility, low-stock visibility, dispatcher read-only low-stock access, technician consumption of reserved parts, duplicate factual part protection, compatibility records, frontend inventory controls, tests, and domain documentation are in place. The project is ready for backlog grooming or the next approved phase, subject to the non-blocking follow-ups above.
