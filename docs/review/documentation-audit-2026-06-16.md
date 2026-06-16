# Documentation Audit: 2026-06-16

## Scope

This audit reviewed the documentation harness after Phase 16 inventory reservations and the post-phase production hardening commits on June 16, 2026. The goal was to verify that the repository can guide the next implementation slice without relying on chat history, and that current docs do not send future workers toward issues already fixed in code.

Primary sources checked:

- `AGENTS.md`
- `project_notes.md`
- `ARCHITECTURE.md`
- `README.md`
- `docs/execution-plans/index.md`
- `docs/execution-plans/detailed/README.md`
- `docs/harness/repository-map.md`
- `docs/harness/project-history.md`
- `docs/product/mvp-scope.md`
- `domains/service-requests/domain.md`
- `domains/scheduling/domain.md`
- `domains/inventory/domain.md`
- `domains/technicians/domain.md`
- `domains/notifications/domain.md`
- `docs/operations/deployment-runbook.md`
- `docs/operations/backup-restore.md`
- `docs/operations/smoke-tests.md`
- `docs/operations/operational-diagnostics.md`
- `docs/operations/incident-response.md`
- `docs/operations/launch-smoke-evidence-2026-06-15-vps.md`
- `docs/review/phase-02-review.md`
- `docs/review/phase-14-review.md`
- `docs/review/phase-15-review.md`
- `docs/review/phase-16-review.md`
- `tools/repo-checks/check_docs.py`

## Findings Fixed

- `project_notes.md` still treated Phase 16 as the latest meaningful state and did not summarize the post-phase hardening commits. It now records atomic PostgreSQL request-number sequencing, appointment overlap exclusion, scheduling deadlock handling, inventory row locks, notification rowcount logging, default production Telegram bot startup, direct n8n port closure, and expired staff-session redirects.
- `project_notes.md` and `docs/harness/repository-map.md` still pointed to the Phase-14 current-state documentation audit as the latest audit. They now point to this Phase-16/post-hardening audit.
- `docs/harness/project-history.md` did not record the June 16 hardening work and still listed rescheduling rules as deferred. It now records the hardening work and narrows deferred scheduling work to technician profiles, durable availability, automatic matching, route optimization, and customer self-scheduling.
- `domains/service-requests/domain.md` described request-number sequencing generically. It now documents PostgreSQL `service_request_number_seq` and the sqlite local/test counter boundary.
- `domains/scheduling/domain.md` described the overlap capacity rule but not the current PostgreSQL enforcement. It now records the exclusion constraint and conflict/deadlock mapping.
- `domains/inventory/domain.md` still described Phase 16 reservations as later work from the Phase 07 perspective and did not mention row-locking guards. It now describes Phase 16 as implemented and documents PostgreSQL row locks for stock/reservation mutations.
- `domains/technicians/domain.md` still used Phase 08 wording that could be read as deferring all rescheduling. It now distinguishes technician-owned rescheduling controls from dispatcher-owned structured rescheduling introduced in Phase 15.
- Phase review artifacts for Phase 02, Phase 14, Phase 15, and Phase 16 contained non-blocking findings that were later resolved. They now have dated post-review updates so historical findings remain readable without becoming stale current guidance.
- `tools/repo-checks/check_docs.py` now requires this audit and current documentation anchors for request-number sequencing, appointment overlap enforcement, and inventory row locks.

## Consistency Assessment

- Current status is anchored in `project_notes.md`: Phase 16 is complete, post-phase production hardening is recorded, and no next implementation slice has been approved yet.
- Execution plan index and detailed-plan README agree that the next detailed implementation plan should be created just in time after backlog grooming selects the next slice.
- Architecture, product, domain, operations, and repository-map docs agree on the implemented runtime: FastAPI API, React/Vite web, Celery worker, Telegram bot, PostgreSQL/pgvector, Redis, n8n, deterministic local providers, OpenAI-compatible live adapters, safe structured logs, staff audit expansion, scheduling depth, inventory reservations, production concurrency guards, operational diagnostics, incident response, and VPS/Dokploy deployment evidence.
- Public/private boundaries remain consistent: public status snapshots do not expose internal notes, staff data, audit data, AI suggestions, provider metadata, notification internals, technician internal details, appointment ids, inventory quantities, part ids, stock movements, or reservation metadata.
- Operations docs now agree that the Telegram bot is part of default production Compose, n8n should not publish port `5678` directly, and public launch remains blocked until domains/HTTPS, direct test-port closure, disposable staff-route smoke, Telegram runtime review, setup-secret rotation, and real database transfer smoke checks are complete.
- Historical detailed plans and older review artifacts intentionally preserve old phase language. Current-state docs, this audit, and dated post-review updates identify which historical risks have been resolved.

## Remaining Risks

- Backlog grooming has not selected the next approved implementation slice. A detailed implementation plan is still required before any new slice starts.
- The June 16 hardening commits do not have their own phase-level review artifact; this audit records documentation consistency, but a future implementation slice should still use the normal review protocol.
- Public launch is still not approved: domains and HTTPS are missing, temporary direct test ports must be closed, disposable staff-route smoke must be rerun, Telegram bot runtime should be reviewed after deploy, setup-exposed secrets must be rotated, and smoke/backup/restore checks must be repeated after real database transfer.
- SQLite remains intentionally lighter than PostgreSQL for some enum/check/constraint behavior. API and Pydantic validation cover normal routes, but direct repository writes remain a hardening edge.
- Historical detailed implementation plans remain noisy by design because they are durable records of completed work. Contributors should use `project_notes.md`, `docs/execution-plans/index.md`, current domain docs, operations docs, and the latest audit for current state.

## Quality Score

Current documentation quality after this audit: **9.4/10**.

The documentation is strong enough for backlog grooming and next-slice planning. The strongest areas are entry-point clarity, phase sequencing, domain boundaries, public/private safety rules, operations runbooks, and production hardening notes. The main gaps are expected next-step work: choose the next slice, create its detailed plan, complete public-launch evidence, and decide whether the June 16 hardening work needs a dedicated review artifact before broader launch activity.
