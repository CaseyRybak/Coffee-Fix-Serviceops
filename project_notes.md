# Project Notes

This is the current operating dashboard. Historical phase chronology and older decisions live in `docs/harness/project-history.md`.

## Current Status

Coffee Fix ServiceOps has completed implementation slices through Phase 16:

- Public repair intake, request numbers, public status snapshots, clarification answers, and Telegram opt-in link contracts.
- Dispatcher, staff login/RBAC, admin staff management, technician assigned-visit workflow, and inventory basics.
- Knowledge-base RAG with source metadata, relevance-filtered prompt context, deterministic dispatcher suggestions, and accepted diagnostic-question suggestion lifecycle.
- PostgreSQL/pgvector Docker Compose persistence with sqlite in-memory/local fallback for tests and direct Python use.
- Production-oriented Dokploy/VPS operations artifacts: production Compose, environment docs, JSON logging, migration command, backup/restore scripts, smoke-test script, n8n workflow design records, deployment runbook, and Phase 10 review artifact.
- Production launch readiness artifacts: one-time first-admin bootstrap command, optional persisted-staff smoke check, first-launch evidence template, updated deployment runbook, and Phase 11 review artifact.
- Notification automation artifacts: backend-to-n8n webhook emission, delivery-result persistence, staff delivery visibility, production n8n workflow exports, and live n8n workflows for request-created, status-changed, clarification-requested, and customer-answered events.
- Live AI provider and knowledge-base content artifacts: OpenAI-compatible AI suggestion and embedding adapters, deterministic local/test provider selection, curated repair knowledge seed set, RAG evaluation fixtures, safety triage and knowledge-gap fallback behavior, and AI provider operations guidance.
- Operational hardening implementation artifacts: structured safe operational log contexts for API, worker, and Telegram bot; staff-auth audit expansion; request, dispatcher, notification, AI, embedding, and Telegram opt-in trace logs; restore dry-run procedure; operational diagnostics guide; incident response checklist; and launch evidence updates.
- Scheduling depth artifacts: structured appointment window persistence, dispatcher create/reschedule/cancel scheduling APIs, technician overlap capacity checks, dispatcher and technician schedule views, technician-visible appointment timing, customer-safe public appointment snapshots, and request timeline events for scheduling changes.
- Inventory reservation and catalog-control artifacts: request-linked part reservations, reservation release/adjustment, stock movement audit records, available/reserved/on-hand stock visibility, low-stock thresholds, dispatcher read-only low-stock visibility, technician consumption of reserved parts, structured factual part keys, duplicate catalog protection, and exact-model/series/generic-group compatibility records.
- Post-Phase-16 production hardening: atomic PostgreSQL request-number sequence, PostgreSQL appointment overlap exclusion, scheduling deadlock-to-conflict handling, row locks for stock/reservation mutations, safer notification delivery rowcount logging, default production Telegram bot service, no direct n8n port publication, and frontend redirect for expired staff sessions.
- First real Aeza VPS/Dokploy test deployment evidence: Docker/Dokploy installed, `production` branch deployed, API/web/PostgreSQL/Redis healthy, migrations and first-admin bootstrap completed, n8n Cloud notification path verified through Telegram and backend delivery callback, PostgreSQL backup/restore drill recorded, and worker Redis broker dependency fixed/redeployed.

## Active Focus

Backlog grooming after Phase 16, with a live VPS test deployment available for launch-readiness follow-up.

Choose the next approved implementation phase and create its detailed implementation plan before execution. Keep the review gate in `docs/review/subagent-review-protocol.md`.

## Next Steps

1. Define the next approved phase or backlog slice after inventory reservations.
2. Before public launch, configure domains and HTTPS for web/API/Dokploy, then close temporary direct test ports that should not remain public.
3. Rerun staff-route smoke with disposable staff credentials, review Telegram bot opt-in runtime after each production deploy, and repeat deployment smoke checks after the real database transfer.
4. Rotate setup-exposed secrets such as the n8n MCP API key before public launch.
5. Keep repository docs, tests, production Compose config, and operations scripts passing after changes.

## Current Entry Points

- Project map: `AGENTS.md`
- Architecture: `ARCHITECTURE.md`
- Phase index: `docs/execution-plans/index.md`
- Repository map: `docs/harness/repository-map.md`
- Project history: `docs/harness/project-history.md`
- Documentation audit after Phase 10: `docs/review/documentation-audit-2026-06-07.md`
- Documentation audit after Phase 13: `docs/review/documentation-audit-2026-06-10.md`
- Documentation audit before Phase 14: `docs/review/documentation-audit-2026-06-15.md`
- Documentation audit after Phase 14: `docs/review/documentation-audit-2026-06-15-current-state.md`
- Documentation audit after Phase 16 and production hardening: `docs/review/documentation-audit-2026-06-16.md`
- Aeza VPS launch smoke evidence: `docs/operations/launch-smoke-evidence-2026-06-15-vps.md`
- Review protocol: `docs/review/subagent-review-protocol.md`
- Phase 10 review: `docs/review/phase-10-review.md`
- Phase 14 review: `docs/review/phase-14-review.md`
- Phase 15 review: `docs/review/phase-15-review.md`
- Phase 16 review: `docs/review/phase-16-review.md`
- Operations runbook: `docs/operations/deployment-runbook.md`
- AI provider operations: `docs/operations/ai-providers.md`
- Operational diagnostics: `docs/operations/operational-diagnostics.md`
- Incident response: `docs/operations/incident-response.md`

## Verification Commands

- `python3 tools/repo-checks/check_docs.py`
- `cd apps/api && uv run --extra dev pytest`
- `cd apps/worker && uv run --extra dev pytest`
- `cd apps/telegram-bot && uv run --extra dev pytest`
- `npm run web:test`
- `npm run web:lint`
- `npm run web:build`
- `docker compose -f docker-compose.production.yml --env-file .env.example config --quiet`
- `bash -n tools/operations/postgres_backup.sh`
- `bash -n tools/operations/postgres_restore.sh`
- `bash -n tools/operations/smoke_test.sh`
- `python3 tools/operations/test_smoke_script_contract.py`
- `python3 tools/operations/test_production_compose_contract.py`

## Current Decisions

- The backend remains a modular monolith with DDD/hexagonal boundaries.
- Hand-written SQL migrations plus sqlite/psycopg repositories are the current persistence approach; SQLAlchemy/Alembic are deferred choices.
- Public status snapshots must remain customer-safe and must not expose internal notes, AI internals, staff data, audit data, technician internal details, or inventory metadata.
- Staff workspaces are role-protected; public navigation still does not expose staff login, dispatcher, admin, technician, or inventory routes.
- Production deployment uses `docker-compose.production.yml`; local Compose remains localhost-only.
- PostgreSQL and Redis stay private in production; web, API, and n8n are routed through Dokploy or the reverse proxy.
- Production PostgreSQL request numbers use `service_request_number_seq`; sqlite local/test persistence keeps lightweight local counters.
- PostgreSQL appointment capacity is enforced by an exclusion constraint, and scheduling conflicts/deadlocks are surfaced as dispatcher-safe conflicts.
- PostgreSQL inventory reserve/release/consume paths lock stock and reservation rows before mutation.
- n8n workflow records are operational artifacts. Phase 12 created live n8n workflows and repository exports; backend webhook emission and delivery-result persistence are implemented.
- Production staff bootstrap uses `python -m serviceops_api.operations.bootstrap_admin`; local seed users remain disabled outside local/dev/test.
- AI and embedding providers default to deterministic mode for local development and tests; OpenAI-compatible live adapters are configurable for production through secret-backed environment variables.
- AI prompt assembly filters weakly related RAG chunks before provider calls; when no relevant source remains, both deterministic and live providers must treat the request as a knowledge gap and avoid forcing old repair scenarios onto new symptoms.
- Operational logs and audit metadata must use safe structured fields and must not expose passwords, tokens, webhook secrets, API keys, raw AI prompts, provider bodies, customer phone numbers, Telegram chat ids, internal note bodies, or unrestricted source chunk text.
