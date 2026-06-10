# Project Notes

This is the current operating dashboard. Historical phase chronology and older decisions live in `docs/harness/project-history.md`.

## Current Status

Coffee Fix ServiceOps has completed implementation slices through Phase 13:

- Public repair intake, request numbers, public status snapshots, clarification answers, and Telegram opt-in link contracts.
- Dispatcher, staff login/RBAC, admin staff management, technician assigned-visit workflow, and inventory basics.
- Knowledge-base RAG, deterministic source-backed dispatcher suggestion framework, and accepted diagnostic-question suggestion lifecycle.
- PostgreSQL/pgvector Docker Compose persistence with sqlite in-memory/local fallback for tests and direct Python use.
- Production-oriented Dokploy/VPS operations artifacts: production Compose, environment docs, JSON logging, migration command, backup/restore scripts, smoke-test script, n8n workflow design records, deployment runbook, and Phase 10 review artifact.
- Production launch readiness artifacts: one-time first-admin bootstrap command, optional persisted-staff smoke check, first-launch evidence template, updated deployment runbook, and Phase 11 review artifact.
- Notification automation artifacts: backend-to-n8n webhook emission, delivery-result persistence, staff delivery visibility, production n8n workflow exports, and live n8n workflows for request-created, status-changed, clarification-requested, and customer-answered events.
- Live AI provider and knowledge-base content artifacts: OpenAI-compatible AI suggestion and embedding adapters, deterministic local/test provider selection, curated repair knowledge seed set, RAG evaluation fixtures, and AI provider operations guidance.

## Active Focus

Phase 14: Operational Hardening.

Before executing Phase 14, create a detailed implementation plan in `docs/execution-plans/detailed/` and keep the review gate in `docs/review/subagent-review-protocol.md`.

## Next Steps

1. Create the detailed Phase 14 implementation plan for operational hardening.
2. Configure production n8n, Telegram, AI, and embedding provider environment variables before enabling public notification or live AI traffic.
3. Run deployment smoke checks against a real Dokploy/VPS environment before public launch and record evidence with `docs/operations/launch-smoke-evidence.md`.
4. Keep repository docs, tests, production Compose config, and operations scripts passing after changes.

## Current Entry Points

- Project map: `AGENTS.md`
- Architecture: `ARCHITECTURE.md`
- Phase index: `docs/execution-plans/index.md`
- Repository map: `docs/harness/repository-map.md`
- Project history: `docs/harness/project-history.md`
- Documentation audit: `docs/review/documentation-audit-2026-06-07.md`
- Current documentation audit: `docs/review/documentation-audit-2026-06-10.md`
- Review protocol: `docs/review/subagent-review-protocol.md`
- Phase 10 review: `docs/review/phase-10-review.md`
- Operations runbook: `docs/operations/deployment-runbook.md`
- AI provider operations: `docs/operations/ai-providers.md`

## Verification Commands

- `python3 tools/repo-checks/check_docs.py`
- `cd apps/api && uv run --extra dev pytest`
- `cd apps/worker && uv run --extra dev pytest`
- `cd apps/telegram-bot && uv run --extra dev pytest`
- `npm run web:test`
- `npm run web:lint`
- `npm run web:build`
- `docker compose -f docker-compose.production.yml --env-file .env.example config`
- `bash -n tools/operations/postgres_backup.sh`
- `bash -n tools/operations/postgres_restore.sh`
- `bash -n tools/operations/smoke_test.sh`
- `python3 tools/operations/test_smoke_script_contract.py`

## Current Decisions

- The backend remains a modular monolith with DDD/hexagonal boundaries.
- Hand-written SQL migrations plus sqlite/psycopg repositories are the current persistence approach; SQLAlchemy/Alembic are deferred choices.
- Public status snapshots must remain customer-safe and must not expose internal notes, AI internals, staff data, audit data, technician internal details, or inventory metadata.
- Staff workspaces are role-protected; public navigation still does not expose staff login, dispatcher, admin, technician, or inventory routes.
- Production deployment uses `docker-compose.production.yml`; local Compose remains localhost-only.
- PostgreSQL and Redis stay private in production; web, API, and n8n are routed through Dokploy or the reverse proxy.
- n8n workflow records are operational artifacts. Phase 12 created live n8n workflows and repository exports; backend webhook emission and delivery-result persistence are implemented.
- Production staff bootstrap uses `python -m serviceops_api.operations.bootstrap_admin`; local seed users remain disabled outside local/dev/test.
- AI and embedding providers default to deterministic mode for local development and tests; OpenAI-compatible live adapters are configurable for production through secret-backed environment variables.
