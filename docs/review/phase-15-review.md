# Phase 15 Review: Scheduling Depth

Date: 2026-06-15

## Reviewer Roles

- Plan/docs reviewer: checked phase scope, detailed plan compliance, acceptance criteria, project notes, phase index, and domain documentation.
- Backend/API reviewer: checked scheduling persistence, API contracts, SQLite/Postgres parity, lifecycle behavior, role access, public-safe snapshots, and test coverage.
- Frontend/UX reviewer: checked dispatcher scheduling controls, technician schedule visibility, public status rendering, legacy assignment fallback, TypeScript coverage, and responsive layout risks.

## Files Reviewed

- `docs/execution-plans/detailed/15-scheduling-depth-implementation.md`
- `docs/execution-plans/index.md`
- `project_notes.md`
- `domains/scheduling/domain.md`
- `domains/service-requests/domain.md`
- `domains/technicians/domain.md`
- `apps/api/src/serviceops_api/scheduling/`
- `apps/api/src/serviceops_api/migrations/0007_scheduling_appointments.sql`
- `apps/api/src/serviceops_api/service_requests/repository.py`
- `apps/api/src/serviceops_api/service_requests/models.py`
- `apps/api/src/serviceops_api/technicians/models.py`
- `apps/api/src/serviceops_api/main.py`
- `apps/api/tests/test_scheduling_workflow.py`
- `apps/api/tests/test_dispatcher_requests.py`
- `apps/api/tests/test_technician_workflow.py`
- `apps/web/src/App.tsx`
- `apps/web/src/App.test.tsx`
- `apps/web/src/styles.css`

## Verification Commands

- `cd apps/api && uv run --extra dev pytest tests/test_scheduling_workflow.py tests/test_technician_workflow.py tests/test_dispatcher_requests.py tests/test_service_request_status.py -v` -> 24 passed, 1 FastAPI deprecation warning.
- `npm run web:lint` -> passed.
- `npm run web:test` -> passed.
- `npm run web:build` -> passed.

Earlier full-slice verification also passed before review fixes:

- `cd apps/api && uv run --extra dev pytest` -> 132 passed, 1 FastAPI deprecation warning.
- `cd apps/worker && uv run --extra dev pytest` -> 14 passed.
- `cd apps/telegram-bot && uv run --extra dev pytest` -> 14 passed.
- Documentation checks, production Compose config, shell syntax checks, and smoke script contract checks passed.

## Blocking Issues

Resolved during review:

- Rescheduling/cancelling after technician work had started could roll the service request back from `diagnostics`, `waiting_for_parts`, or `repair_in_progress` to an earlier scheduling status. Fixed by preserving work-started lifecycle statuses while still updating scheduling windows and events.
- Creating a structured appointment after a legacy assignment could leave stale assignment phone/region metadata from the previous technician. Fixed by clearing legacy phone/region fields when structured scheduling sets the technician identifier.

Regression coverage added:

- `test_reschedule_and_cancel_preserve_started_work_status`
- `test_structured_scheduling_clears_stale_assignment_contact_metadata`

## Non-Blocking Issues

- SQLite does not enforce every appointment constraint present in PostgreSQL. API validation covers normal routes; direct repository use remains a hardening follow-up.
- Technician overlap checks are application-level and not yet protected by PostgreSQL range/exclusion constraints or transaction-level locking for concurrent dispatcher calls.
- Frontend interaction tests can be expanded to cover candidate click -> assignment payload -> technician/public visibility.
- Appointment creation remains a structured scheduling action requiring start/end datetime. Legacy `Назначение` remains compatibility metadata plus customer-safe window fallback.

## Post-Review Update: 2026-06-16

- The PostgreSQL overlap-protection follow-up is resolved: migration `0007_scheduling_appointments.sql` now adds `request_appointments_no_overlap` with `EXCLUDE USING gist`, and the PostgreSQL repository maps exclusion/unique/deadlock errors to scheduling conflicts. SQLite remains intentionally lighter and still relies on API/application validation for normal routes.

## Suggested Follow-Up Slice

Scheduling hardening follow-up:

- Bring SQLite test constraints closer to PostgreSQL where practical.
- Add focused frontend interaction tests for candidate selection and scheduling form payloads.
- Clarify create-vs-reschedule UX further if dispatchers need a single guided flow.

## Documentation Updates

Completed:

- `domains/scheduling/domain.md` now documents that reschedule/cancel after technician work starts preserve the current service-request lifecycle status.
- `domains/service-requests/domain.md` now mirrors that lifecycle rule.
- This review artifact records the independent subagent review and resolution of blockers.

## Final Recommendation

Phase 15 is approved after blocker fixes and fresh verification. The implemented slice matches the scheduling-depth plan: structured appointment persistence, dispatcher create/reschedule/cancel APIs, overlap checks, dispatcher and technician schedule views, technician-visible appointment timing, public-safe appointment snapshots, and timeline events for scheduling changes are in place.
