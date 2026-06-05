# Project Notes

## Current Status

The repository currently contains a Figma-exported React/Vite reference in `reference/figma`, a documentation harness for repository-guided development, the Phase 01 runtime foundation, and the Phase 02 service request intake flow. The API can create persisted service requests with customer and machine intake data, and the web app presents the public CoffeeFix Pro request form with a request-number success state.

## Latest Changes

- 2026-06-05: Captured product vision, stack choices, harness-engineering approach, DDD/hexagonal direction, Figma reference assessment, and phased implementation strategy as repository artifacts.
- 2026-06-05: Added `project_notes.md` as the operational status file for future work.
- 2026-06-05: Added phase-based execution plans with review gates.
- 2026-06-05: Removed the redundant operational status file naming path; `project_notes.md` is the single operational status file.
- 2026-06-05: Added the process decision that each phase requires a detailed implementation plan before execution.
- 2026-06-05: Started Phase 00 execution and added `docs/execution-plans/detailed/00-repository-harness-implementation.md`.
- 2026-06-05: Completed Phase 00 repository harness implementation after Git initialization became available.
- 2026-06-05: Added `.gitignore` so local `.agents/` runtime files stay out of repository commits.
- 2026-06-05: Added `.gitkeep` placeholders for empty scaffold directories and extended repo checks to validate required directories.
- 2026-06-05: Renamed the initial Git branch to `main` for GitHub readiness and saved the Phase 00 review artifact in `docs/review/phase-00-review.md`.
- 2026-06-05: Implemented Phase 01 foundation runtime with FastAPI `/health`, React/Vite shell, Celery worker shell, aiogram shell, Docker Compose, and runtime verification commands.
- 2026-06-05: Added the policy that commits and pushes require a direct user instruction in the current conversation turn.
- 2026-06-05: Added root npm scripts so the web shell starts from the repository root with `npm run dev` on `http://localhost:3000/`.
- 2026-06-05: Created `docs/execution-plans/detailed/02-service-request-intake-implementation.md` and implemented Phase 02 service request intake.
- 2026-06-05: Added `POST /service-requests`, request number generation, sqlite-backed local persistence, and a PostgreSQL migration for customer, machine, service request, and attachment metadata tables.
- 2026-06-05: Replaced the web runtime shell with a public CoffeeFix Pro intake form based on the Figma reference and wired it to the service request API contract.
- 2026-06-05: Rechecked Phase 02 after Docker setup, passed Compose config/build verification, passed `VITE_SERVICEOPS_API_BASE_URL` into the web Docker build, and restricted local Compose port bindings to `127.0.0.1`.

## Active Focus

Phase 03 planning is the active focus: create a detailed implementation plan for `docs/execution-plans/phases/03-client-status-and-notifications.md` before implementing the public status page and notification opt-in flow.

## Next Steps

1. Create a detailed implementation plan for Phase 03.
2. Review the Phase 03 plan before execution.
3. Execute Phase 03 only after the detailed plan exists.
4. Keep `python3 tools/repo-checks/check_docs.py`, API tests, worker tests, Telegram bot tests, and web checks passing after harness changes.

## Active Artifacts

- Plan index: `docs/execution-plans/index.md`
- Completed phase slice: `docs/execution-plans/phases/00-repository-harness.md`
- Detailed Phase 00 plan: `docs/execution-plans/detailed/00-repository-harness-implementation.md`
- Completed Phase 01 slice: `docs/execution-plans/phases/01-foundation-runtime.md`
- Detailed Phase 01 plan: `docs/execution-plans/detailed/01-foundation-runtime-implementation.md`
- Completed Phase 02 slice: `docs/execution-plans/phases/02-service-request-intake.md`
- Detailed Phase 02 plan: `docs/execution-plans/detailed/02-service-request-intake-implementation.md`
- Next phase slice: `docs/execution-plans/phases/03-client-status-and-notifications.md`
- Architecture map: `ARCHITECTURE.md`
- Domain map: `docs/domain-maps/index.md`
- Review protocol: `docs/review/subagent-review-protocol.md`
- Phase 00 review: `docs/review/phase-00-review.md`
- Phase 01 review: `docs/review/phase-01-review.md`
- Phase 02 review: `docs/review/phase-02-review.md`

## Recent Decisions

- The backend is a modular monolith with DDD/hexagonal boundaries.
- PostgreSQL with pgvector is the default SQL and RAG store.
- The Figma reference drives the public client UI, but exported code is treated as a reference, not production structure.
- Automation features are operational workflows with human confirmation, not decorative client-facing claims.
- `AGENTS.md` files act as maps and context entry points.
- Repo-specific workflow drafts are stored in `docs/agent-skills` until the project is ready to activate them.
- Before executing any phase, create a detailed implementation plan for that phase; current phase files are slice maps, not execution-ready implementation plans.
- Phase 01 local verification commands are `python3 tools/repo-checks/check_docs.py`, `cd apps/api && uv run --extra dev pytest`, `cd apps/worker && uv run --extra dev pytest`, `cd apps/telegram-bot && uv run --extra dev pytest`, `npm run web:test`, `npm run web:lint`, and `npm run web:build`.
- Phase 02 keeps attachment handling to metadata only; binary upload storage is deferred.
- Phase 02 uses sqlite-backed local persistence for deterministic development and tests while recording the PostgreSQL target schema in `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql`.
- Local Docker Compose publishes API, web, PostgreSQL, and Redis on `127.0.0.1` only; this is the intended safety posture for development.
