# Project Notes

## Current Status

The repository currently contains a Figma-exported React/Vite reference in `reference/figma`, a documentation harness for repository-guided development, the Phase 01 runtime foundation, the Phase 02 service request intake flow, the Phase 03 public status and notification opt-in flow, a PostgreSQL persistence slice for Docker Compose, the Phase 04 dispatcher MVP, the Phase 05 staff access layer, the Phase 06 knowledge-base RAG slice, the Phase 07 AI agent workflow slice, the Phase 08 technician and inventory slice, the Phase 09 staff admin and user management slice, and the Phase 10 deployment and operations slice. The API can create persisted service requests, expose public status snapshots, record clarification answers, create Telegram opt-in links, support protected internal dispatcher list/detail/actions, authenticate persisted staff accounts with development seed fallback, manage staff accounts through admin-only APIs, record staff-management audit events, ingest repair knowledge documents, chunk/embed them, retrieve source-backed chunks, generate dispatcher-reviewed AI suggestions, accept diagnostic-question suggestions as normal clarification questions, expose assigned technician visits, record technician diagnosis/results, manage a basic parts catalog, track stock counts, record parts used on requests, emit structured JSON logs, and run PostgreSQL migration initialization through an operations command. Docker Compose API runs against PostgreSQL with pgvector, production-oriented Compose covers Dokploy/VPS services including n8n, and injected tests keep sqlite in-memory persistence.

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
- 2026-06-05: Created `docs/execution-plans/detailed/03-client-status-and-notifications-implementation.md` and implemented Phase 03 client status and notification opt-in.
- 2026-06-05: Added public status retrieval by request number or token, status events, clarification questions, customer answer submission, Telegram opt-in token/link contract, and PostgreSQL target schema updates.
- 2026-06-05: Added the web status page with timeline, clarification answer form, Telegram opt-in action, and real success-state links.
- 2026-06-05: Added `docs/execution-plans/detailed/03a-postgres-persistence-implementation.md` and connected Docker Compose API persistence to PostgreSQL.
- 2026-06-05: Added a PostgreSQL service-request repository, repository selection from `SERVICEOPS_DATABASE_URL`, idempotent migration application, and psycopg runtime dependency.
- 2026-06-05: Audited documentation readiness for Phase 04 and added `docs/execution-plans/detailed/04-dispatcher-mvp-implementation.md` with dispatcher API, persistence, web, testing, and review scope.
- 2026-06-05: Implemented Phase 04 dispatcher MVP with internal dispatcher API routes, sqlite/PostgreSQL dispatcher persistence, manual assignment metadata, dispatcher-only internal notes, and a React dispatcher workspace.
- 2026-06-06: Re-audited Phase 04 readiness and added a lightweight dispatcher-only technician candidate list to close the slice-map "technician list" gap without expanding into full technician profiles or availability.
- 2026-06-06: Created `docs/execution-plans/detailed/05-staff-access-and-roles-implementation.md` and implemented Phase 05 staff access and roles.
- 2026-06-06: Added `/staff/login`, local-development staff token issuing, dispatcher/admin/technician/inventory role vocabulary, backend dispatcher API role protection, a frontend `/staff/login` page, and a `/dispatcher` route guard.
- 2026-06-07: Created `docs/execution-plans/detailed/06-knowledge-base-rag-implementation.md` and marked it ready for review before executing Phase 06.
- 2026-06-07: Implemented Phase 06 knowledge-base RAG with text document ingestion, deterministic chunking, source-backed retrieval, sqlite and PostgreSQL pgvector repositories, a worker embedding task boundary, and an E61 overheating seed repair document.
- 2026-06-07: Created `docs/execution-plans/detailed/07-ai-agent-workflows-implementation.md` and marked it ready for review before executing Phase 07.
- 2026-06-07: Implemented Phase 07 AI agent workflows with deterministic prompt assembly, source-backed dispatcher suggestions, sqlite/PostgreSQL AI suggestion persistence, protected dispatcher AI routes, and a dispatcher AI suggestion panel.
- 2026-06-07: Created `docs/execution-plans/detailed/08-technician-and-inventory-implementation.md` and marked it ready for review before executing Phase 08.
- 2026-06-07: Implemented Phase 08 technician and inventory with protected technician visit workflow, diagnosis/result capture, parts catalog, stock counts, parts-used stock decrement, technician status events, and technician/inventory web workspaces.
- 2026-06-07: Inserted Phase 09 Staff Admin and User Management before deployment, moved deployment and operations to Phase 10, and created `docs/execution-plans/detailed/09-staff-admin-and-user-management-implementation.md`.
- 2026-06-07: Implemented Phase 09 staff admin and user management with persisted staff accounts, password hashes, admin-only account lifecycle API, audit events, persisted login before development seed fallback, and an `/admin` workspace.
- 2026-06-07: Added a local-only persisted staff seed command for dispatcher, technician, and inventory development accounts.
- 2026-06-07: Created `docs/execution-plans/detailed/10-deployment-and-operations-implementation.md` to prepare the Dokploy deployment, operations, backup, structured logging, n8n workflow, and smoke-test slice.
- 2026-06-07: Implemented Phase 10 deployment and operations with production Compose, expanded environment documentation, JSON logging setup, PostgreSQL migration command, backup/restore scripts, smoke-test script, n8n workflow records, and concrete operations runbooks.
- 2026-06-07: Completed Phase 10 local review, fixed smoke-test status endpoints, clarified private-network PostgreSQL backup guidance, and moved active focus to backlog grooming or the next approved slice.

## Active Focus

Phase 10 deployment and operations is locally reviewed and ready to close. The active focus is backlog grooming or selecting the next user-approved implementation slice; create a detailed implementation plan before executing the next slice.

## Next Steps

1. Select the next approved implementation slice and create its detailed plan before execution.
2. Run deployment smoke checks against a real Dokploy/VPS environment before public launch.
3. Add backend-to-n8n webhook emission and delivery-result persistence when notification automation moves beyond design records.
4. Keep `python3 tools/repo-checks/check_docs.py`, API tests, worker tests, Telegram bot tests, web checks, production Compose config, and operations shell syntax checks passing after harness changes.

## Active Artifacts

- Plan index: `docs/execution-plans/index.md`
- Completed phase slice: `docs/execution-plans/phases/00-repository-harness.md`
- Detailed Phase 00 plan: `docs/execution-plans/detailed/00-repository-harness-implementation.md`
- Completed Phase 01 slice: `docs/execution-plans/phases/01-foundation-runtime.md`
- Detailed Phase 01 plan: `docs/execution-plans/detailed/01-foundation-runtime-implementation.md`
- Completed Phase 02 slice: `docs/execution-plans/phases/02-service-request-intake.md`
- Detailed Phase 02 plan: `docs/execution-plans/detailed/02-service-request-intake-implementation.md`
- Completed Phase 03 slice: `docs/execution-plans/phases/03-client-status-and-notifications.md`
- Detailed Phase 03 plan: `docs/execution-plans/detailed/03-client-status-and-notifications-implementation.md`
- Detailed PostgreSQL persistence plan: `docs/execution-plans/detailed/03a-postgres-persistence-implementation.md`
- Detailed Phase 04 plan: `docs/execution-plans/detailed/04-dispatcher-mvp-implementation.md`
- Completed Phase 04 slice: `docs/execution-plans/phases/04-dispatcher-mvp.md`
- Detailed Phase 05 plan: `docs/execution-plans/detailed/05-staff-access-and-roles-implementation.md`
- Completed Phase 05 slice: `docs/execution-plans/phases/05-staff-access-and-roles.md`
- Completed Phase 06 slice: `docs/execution-plans/phases/06-knowledge-base-rag.md`
- Detailed Phase 06 plan: `docs/execution-plans/detailed/06-knowledge-base-rag-implementation.md`
- Completed Phase 07 slice: `docs/execution-plans/phases/07-ai-agent-workflows.md`
- Detailed Phase 07 plan: `docs/execution-plans/detailed/07-ai-agent-workflows-implementation.md`
- Phase 07 review: `docs/review/phase-07-review.md`
- Completed Phase 08 slice: `docs/execution-plans/phases/08-technician-and-inventory.md`
- Detailed Phase 08 plan: `docs/execution-plans/detailed/08-technician-and-inventory-implementation.md`
- Phase 08 review: `docs/review/phase-08-review.md`
- Detailed Phase 09 plan: `docs/execution-plans/detailed/09-staff-admin-and-user-management-implementation.md`
- Phase 09 review: `docs/review/phase-09-review.md`
- Detailed Phase 10 plan: `docs/execution-plans/detailed/10-deployment-and-operations-implementation.md`
- Phase 10 review: `docs/review/phase-10-review.md`
- Architecture map: `ARCHITECTURE.md`
- Domain map: `docs/domain-maps/index.md`
- Review protocol: `docs/review/subagent-review-protocol.md`
- Phase 00 review: `docs/review/phase-00-review.md`
- Phase 01 review: `docs/review/phase-01-review.md`
- Phase 02 review: `docs/review/phase-02-review.md`
- Phase 03 review: `docs/review/phase-03-review.md`
- Phase 04 review: `docs/review/phase-04-review.md`
- Phase 05 review: `docs/review/phase-05-review.md`
- Phase 06 review: `docs/review/phase-06-review.md`

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
- Phase 02 introduced sqlite-backed local persistence for deterministic development and tests while recording the PostgreSQL target schema in `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql`.
- Local Docker Compose publishes API, web, PostgreSQL, and Redis on `127.0.0.1` only; this is the intended safety posture for development.
- Phase 03 supports public status lookup by request number for MVP convenience and by public token for direct status links.
- Phase 03 records customer clarification answers in the service-request lifecycle; dispatcher UI creation of questions is deferred to Phase 04.
- Phase 03 defines Telegram opt-in token/link generation but defers bot-side token consumption and outbound notification delivery.
- Docker Compose API persistence uses PostgreSQL via `SERVICEOPS_DATABASE_URL`; direct Python defaults to sqlite for lightweight local imports and tests.
- Phase 04 should keep dispatcher-only internal notes and assignment metadata out of public status snapshots.
- Phase 04 dispatcher routes are internal API contracts but still unauthenticated; an access gate is required before public deployment exposure.
- Phase 04 keeps technician assignment manual and descriptive on the request. Full technician profiles, availability, confirmed appointments, and mobile technician workflows remain deferred.
- Phase 05 uses local-development staff users and stateless bearer tokens for MVP access control; production user management, password reset, SSO, OAuth, audit logs, and granular permissions remain deferred.
- Dispatcher APIs require a staff bearer token with the `dispatcher` role; public intake, public status lookup, clarification answer, and Telegram opt-in flows remain unauthenticated.
- No public homepage navigation exposes staff login, dispatcher, admin, technician, or inventory workspace links.
- Phase 06 added knowledge-base documents, chunks, deterministic local embeddings, PostgreSQL pgvector schema, retrieval with source metadata, and a worker embedding task boundary while keeping AI workflow automation deferred to Phase 07.
- Phase 06 retrieval returns source chunks and metadata only; generated answers, diagnostic recommendations, dispatcher suggestions, and customer replies belong to Phase 07.
- Phase 07 AI suggestions are stored separately from service-request lifecycle actions until a dispatcher confirms them.
- Only accepted diagnostic-question suggestions create customer-visible clarification questions; likely causes, parts, and customer replies remain dispatcher-reviewed drafts.
- Phase 07 parts suggestions are inventory concepts only. Live catalog, stock, reservations, and technician parts workflows remain Phase 08 scope.
- Public status snapshots never expose AI suggestions, source chunks, prompt inputs, or provider metadata.
- Phase 08 technician actions require the `technician` staff role and only expose requests assigned to the staff username stored in dispatcher assignment metadata.
- Phase 08 inventory management requires the `inventory` staff role; parts-used actions decrement stock immediately and reject insufficient stock before service-request status changes.
- Public status snapshots can show customer-safe technician timeline events but not technician checklist summaries, repair-result internal details, parts-used notes, stock counts, part IDs, or inventory metadata.
- Phase 09 added persisted staff accounts and admin user management before production deployment; local-development staff users remain separated from production account management.
- Phase 09 authenticates persisted staff accounts before falling back to local development seed users.
- Local developers can persist the dispatcher, technician, and inventory seed users with `cd apps/api && uv run --extra dev python -m serviceops_api.staff_management.seed_local_staff`.
- Phase 09 admin account lifecycle actions require the `admin` role, create staff audit records, and block deactivating the last active admin account.
- Public status snapshots and public navigation still do not expose staff accounts, admin routes, password reset data, audit events, or internal workspaces.
- Production deployment uses `docker-compose.production.yml` for Dokploy/VPS while the local Compose file remains localhost-only.
- PostgreSQL and Redis must remain private Docker-network services in production; public routing is only for web, API, and n8n through Dokploy or the reverse proxy.
- API, worker, and Telegram bot services emit structured JSON logs to stdout for Dokploy log collection.
- n8n automates delivery and operational routing around backend events, but it does not own service-request state, staff identity, customer answers, inventory counts, or repair lifecycle transitions.
- Production backups use PostgreSQL custom-format dumps with checksum files, and restore drills should run against a non-production database.
