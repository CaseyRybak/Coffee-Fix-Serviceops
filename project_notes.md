# Project Notes

This is the current operating dashboard. Historical phase chronology and older decisions live in `docs/harness/project-history.md`.

## Current Status

Coffee Fix ServiceOps has completed implementation slices through Phase 20:

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
- First real Aeza VPS/Dokploy test deployment evidence: Docker/Dokploy installed, the initial temporary `production` branch deployment was reconciled back to `main`, Dokploy now tracks `main`, API/web/PostgreSQL/Redis smoke checks passed, migrations and first-admin bootstrap completed, the legacy n8n Cloud path was verified and then replaced by self-hosted VPS n8n, PostgreSQL backup/restore drill recorded, and worker Redis broker dependency fixed/redeployed.
- Self-hosted n8n VPS production handoff: repository workflow exports were imported and published on the VPS n8n service, the production API webhook URLs now target `http://n8n:5678/webhook/serviceops/...` on the Compose network, request-created delivery was verified end-to-end on `CFX-20260616-000008`, and local Telegram polling was stopped to avoid competing with the production bot while the project intentionally uses one Telegram bot token.
- Phase 17/17a public demo closure: real domain and HTTPS routes for web/API are configured, direct public test ports are blocked externally, Dokploy is restricted to the operator IP, staff-route smoke passed, n8n/Telegram/backup/restore-readiness evidence is recorded, and the public hero image now uses responsive desktop/mobile WebP assets with PNG fallback.
- Phase 18 portfolio packaging and demo-mode policy: README is now portfolio-oriented, `docs/product/portfolio-demo-guide.md` documents safe demo scenarios, screenshot guidance, disposable credential policy, fake-data rules, and production-safe reset guidance, and `docs/review/phase-18-review.md` records the closure review.
- Phase 19 frontend workspace decomposition: the large web entry file has been split into public, staff-auth, dispatcher, technician, inventory, admin, and shared frontend modules; shared API path builders, staff auth helpers, type definitions, formatters, inventory helpers, and UI primitives now live outside `apps/web/src/App.tsx`; web tests, TypeScript lint, and production build passed.
- Phase 20 owner dashboard and SLA foundation: SLA deadlines, near-deadline, overdue, and inactive states are derived from urgency/status/creation time; admin-only owner dashboard and daily-report APIs aggregate request workload, waiting-for-parts, technician workload, top issue groups, SLA risk, and low-stock risk; the web app now has an admin owner dashboard at `/owner`; public status snapshots remain free of SLA diagnostics, staff workload, inventory quantities, and internal risk labels.

## Active Focus

Phase 21 operational n8n automation, using the Phase 20 owner daily-report and dashboard APIs as the source of truth for SLA reminders, red alerts, owner reports, and low-stock alerts.

Phase 21 needs a detailed implementation plan before changing n8n workflow exports, webhook contracts, or notification automation code. Use `docs/execution-plans/phases/21-operational-n8n-automation.md` as the slice map and keep the review gate in `docs/review/subagent-review-protocol.md`.

## Next Steps

1. Create a Phase 21 detailed implementation plan before changing n8n automation code.
2. Read the Phase 21 slice map, Phase 20 dashboard/daily-report implementation, and notifications/operations docs before planning.
3. Add SLA reminders, red alerts, owner daily reports, and low-stock automation without letting n8n own lifecycle status, staff identity, inventory counts, or repair decisions.
4. Keep demo data and credentials safe for portfolio review: use fake customer data, disposable staff accounts, deterministic AI defaults, and no production database reset.
5. After Phase 21, proceed to procurement lite, technician recommendation, and AI assistant tools.

## Current Entry Points

- Project map: `AGENTS.md`
- Architecture: `ARCHITECTURE.md`
- Phase index: `docs/execution-plans/index.md`
- Post-Phase-16 roadmap: `docs/execution-plans/roadmap-after-phase-16.md`
- Repository map: `docs/harness/repository-map.md`
- Project history: `docs/harness/project-history.md`
- Documentation audit after Phase 10: `docs/review/documentation-audit-2026-06-07.md`
- Documentation audit after Phase 13: `docs/review/documentation-audit-2026-06-10.md`
- Documentation audit before Phase 14: `docs/review/documentation-audit-2026-06-15.md`
- Documentation audit after Phase 14: `docs/review/documentation-audit-2026-06-15-current-state.md`
- Documentation audit after Phase 16 and production hardening: `docs/review/documentation-audit-2026-06-16.md`
- Phase 17 review: `docs/review/phase-17-review.md`
- Phase 17a review: `docs/review/phase-17a-review.md`
- Phase 18 review: `docs/review/phase-18-review.md`
- Phase 19 review: `docs/review/phase-19-review.md`
- Phase 20 review: `docs/review/phase-20-review.md`
- Portfolio demo guide: `docs/product/portfolio-demo-guide.md`
- Public demo launch evidence: `docs/operations/public-demo-launch-evidence.md`
- Aeza VPS launch smoke evidence: `docs/operations/launch-smoke-evidence-2026-06-15-vps.md`
- Self-hosted n8n VPS evidence: `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`
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
- Owner dashboard and SLA data are admin-only internal operations data. Public status snapshots must not expose SLA state, overdue labels, near-deadline labels, daily report data, staff workload, inventory quantities, low-stock thresholds, or internal risk labels.
- Staff workspaces are role-protected; public navigation still does not expose staff login, dispatcher, admin, technician, or inventory routes.
- Production deployment uses `docker-compose.production.yml`; local Compose remains localhost-only.
- Repository deployment now uses a single `main` branch; the temporary `production` and phase deployment branches were removed after `main` was fast-forwarded to the deployed revision.
- PostgreSQL and Redis stay private in production; web and API should be routed through Dokploy or the reverse proxy before public launch. n8n is reached by the API through the private Compose service URL and should not publish `5678` directly.
- Production PostgreSQL request numbers use `service_request_number_seq`; sqlite local/test persistence keeps lightweight local counters.
- PostgreSQL appointment capacity is enforced by an exclusion constraint, and scheduling conflicts/deadlocks are surfaced as dispatcher-safe conflicts.
- PostgreSQL inventory reserve/release/consume paths lock stock and reservation rows before mutation.
- n8n workflow records are operational artifacts. Phase 12 created live n8n workflows and repository exports; production now runs the imported workflow exports on self-hosted VPS n8n, and backend webhook emission plus delivery-result persistence are implemented.
- The project currently uses one Telegram bot token and one staff chat for local and production. Only one polling bot instance may run with that token; production owns real `/start` traffic, and local tests should simulate opt-in through protected API calls unless production polling is intentionally paused.
- Phases 19-24 are intentionally roadmap-level slice maps. Detailed implementation plans must still be created just in time from current code and docs before executing each phase.
- Production staff bootstrap uses `python -m serviceops_api.operations.bootstrap_admin`; local seed users remain disabled outside local/dev/test.
- Portfolio demo mode is a documentation policy and walkthrough, not a runtime switch or production database reset. Public portfolio review should use fake customer data, disposable staff accounts, deterministic AI defaults, and sanitized screenshots/evidence.
- AI and embedding providers default to deterministic mode for local development and tests; OpenAI-compatible live adapters are configurable for production through secret-backed environment variables.
- AI prompt assembly filters weakly related RAG chunks before provider calls; when no relevant source remains, both deterministic and live providers must treat the request as a knowledge gap and avoid forcing old repair scenarios onto new symptoms.
- Operational logs and audit metadata must use safe structured fields and must not expose passwords, tokens, webhook secrets, API keys, raw AI prompts, provider bodies, customer phone numbers, Telegram chat ids, internal note bodies, or unrestricted source chunk text.
