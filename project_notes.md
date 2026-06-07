# Project Notes

This is the current operating dashboard. Historical phase chronology and older decisions live in `docs/harness/project-history.md`.

## Current Status

Coffee Fix ServiceOps has completed implementation slices through Phase 10:

- Public repair intake, request numbers, public status snapshots, clarification answers, and Telegram opt-in link contracts.
- Dispatcher, staff login/RBAC, admin staff management, technician assigned-visit workflow, and inventory basics.
- Knowledge-base RAG, source-backed AI dispatcher suggestions, and accepted diagnostic-question suggestions.
- PostgreSQL/pgvector Docker Compose persistence with sqlite in-memory/local fallback for tests and direct Python use.
- Production-oriented Dokploy/VPS operations artifacts: production Compose, environment docs, JSON logging, migration command, backup/restore scripts, smoke-test script, n8n workflow design records, deployment runbook, and Phase 10 review artifact.

## Active Focus

Backlog grooming / next user-approved slice selection.

Before executing the next slice, create a detailed implementation plan in `docs/execution-plans/detailed/` and keep the review gate in `docs/review/subagent-review-protocol.md`.

## Next Steps

1. Select the next approved implementation slice and create its detailed plan before execution.
2. Add a production-safe first-admin bootstrap command or controlled runbook step before public launch.
3. Run deployment smoke checks against a real Dokploy/VPS environment before public launch.
4. Add backend-to-n8n webhook emission and delivery-result persistence when notification automation moves beyond design records.
5. Keep repository docs, tests, production Compose config, and operations scripts passing after changes.

## Current Entry Points

- Project map: `AGENTS.md`
- Architecture: `ARCHITECTURE.md`
- Phase index: `docs/execution-plans/index.md`
- Repository map: `docs/harness/repository-map.md`
- Project history: `docs/harness/project-history.md`
- Documentation audit: `docs/review/documentation-audit-2026-06-07.md`
- Review protocol: `docs/review/subagent-review-protocol.md`
- Phase 10 review: `docs/review/phase-10-review.md`
- Operations runbook: `docs/operations/deployment-runbook.md`

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
- n8n workflow records are design/operations artifacts. Backend webhook emission and delivery-result persistence are not implemented yet.
- Production staff bootstrap is not complete: local seed users are disabled outside local/dev/test, so public launch requires a first-admin bootstrap command or controlled database runbook.
