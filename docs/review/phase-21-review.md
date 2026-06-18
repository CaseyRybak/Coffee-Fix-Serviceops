# Phase 21 Review: Operational n8n Automation

## Scope

Phase 21 extends n8n from event notification delivery into scheduled operational automation:

- SLA reminder payloads for near-deadline requests.
- Red-alert payloads for overdue requests.
- Owner daily report payloads from backend-owned dashboard data.
- Low-stock alert payloads from backend-owned inventory risk data.
- Inactive n8n workflow exports for the four scheduled automation paths.
- Operations/domain documentation for import, preview, idempotency, diagnostics, and privacy boundaries.

## Files Reviewed

- `apps/api/src/serviceops_api/main.py`
- `apps/api/src/serviceops_api/notifications/api.py`
- `apps/api/src/serviceops_api/notifications/models.py`
- `apps/api/src/serviceops_api/notifications/use_cases.py`
- `apps/api/src/serviceops_api/notifications/repository.py`
- `apps/api/tests/test_operational_n8n_automation.py`
- `docs/execution-plans/detailed/21-operational-n8n-automation-implementation.md`
- `docs/execution-plans/index.md`
- `docs/operations/n8n-workflows/sla-reminder-alert.json`
- `docs/operations/n8n-workflows/red-alert.json`
- `docs/operations/n8n-workflows/owner-daily-report.json`
- `docs/operations/n8n-workflows/low-stock-alert.json`
- `docs/operations/n8n-workflows.md`
- `docs/operations/deployment-runbook.md`
- `docs/operations/smoke-tests.md`
- `docs/operations/operational-diagnostics.md`
- `domains/notifications/domain.md`
- `domains/service-requests/domain.md`
- `domains/inventory/domain.md`
- `project_notes.md`

## Verification

- `cd apps/api && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest tests/test_operational_n8n_automation.py -q`
  - Final result after consistency fixes: `8 passed`
- `cd apps/api && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest tests/test_operational_n8n_automation.py tests/test_notification_automation.py tests/test_owner_dashboard.py -q`
  - Final result after consistency fixes: `21 passed`
- `cd apps/api && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`
  - Final result after consistency fixes: `169 passed, 1 warning`
- `python3 tools/repo-checks/check_docs.py`
  - Final result after review fixes: `documentation harness check passed`
- `python3 -m json.tool` on the four new Phase 21 n8n exports
  - Final result after review fixes: all four parsed successfully
- `python3 -m json.tool` on all repository n8n workflow exports
  - Final result after consistency fixes: all exports parsed successfully
- `rg -n "caseyrybak|active\": true|activeVersion|triggerInfo|canExecute|scopes|triggerCount" docs/operations/n8n-workflows/*.json`
  - Final result after consistency fixes: no matches

## Review Findings

### Blocking Issues

None remained after review fixes.

### Issues Found And Resolved

- Plan-compliance review found stale phase-state docs:
  - `project_notes.md` still described Phase 21 as active.
  - `docs/execution-plans/index.md` still pointed active work at Phase 21.
  - `docs/review/phase-21-review.md` did not exist yet.
  - Resolution: phase-state docs now mark Phase 21 complete and Phase 22 active; this review artifact records the closure.

- Architecture/privacy audit found operational payloads included `latest_event_title`, a free-form staff-entered field.
  - Resolution: removed `latest_event_title` from the Phase 21 request alert response model and owner daily report payload mapping.

- Architecture/privacy audit noted operational callback coverage was missing.
  - Resolution: added coverage that fetches an operational alert item, posts a delivery-result callback using its `event_id`, and verifies retry behavior.

- Bug-finding review found failed operational deliveries were suppressed for the rest of the same idempotency window.
  - Resolution: duplicate suppression now suppresses existing `queued` or `sent` events but allows existing `failed` or `retried` events to be re-queued with an incremented attempt count.

- Follow-up consistency audit found retry callbacks could overwrite an incremented operational `attempt_count` with `1`, matching the current n8n export callback body.
  - Resolution: delivery-result persistence now preserves the greater of the existing attempt count and callback attempt count.

- Bug-finding review found unbounded `window_key` input could create `event_id` values too long for the delivery-result callback contract.
  - Resolution: operational routes now accept only 1-80 character `window_key` values using letters, numbers, `_`, `.`, `:`, and `-`; invalid values return `422`.

- Bug-finding review found new scheduled workflow exports were marked active.
  - Resolution: all four Phase 21 workflow exports are stored with `"active": false`.

- Documentation/workflow audit found Phase 21 scheduled exports were listed next to June 16 production evidence, making them read as already imported and active.
  - Resolution: n8n workflow docs now distinguish Phase 12 live event-notification workflows from inactive Phase 21 scheduled exports and include a Phase 21 activation checklist.

- Documentation/workflow audit found older repository workflow exports still carried raw runtime metadata, including active flags, active-version metadata, execution permissions, and stale n8n Cloud trigger info.
  - Resolution: repository workflow exports are sanitized to inactive state and the import preparation script strips active/runtime metadata before import.

### Non-Blocking Issues

- Operational idempotency is still claim-on-fetch for rows that remain `queued`. If n8n fetches an item and crashes before any callback, the item stays suppressed for that window. This is an accepted Phase 21 tradeoff; a later hardening slice can add age-based retry for stale queued rows.
- The n8n workflow exports are repository-safe but not yet live production evidence. Operators should run `mark_sent=false` previews and import/publish in the target n8n runtime before activating schedules.

### Suggested Follow-Up Slice

- Add retry policy for stale queued operational rows, for example allowing re-queue after a short timeout when no callback has been received.
- Capture sanitized production or staging evidence for all four `mark_sent=false` previews before activating the scheduled workflows.

## Final Recommendation

Phase 21 is ready to move forward after final verification. n8n remains a delivery/reporting layer, while ServiceOps API owns SLA state, owner report data, low-stock calculations, idempotency keys, and delivery evidence.
