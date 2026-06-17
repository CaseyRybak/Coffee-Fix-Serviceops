# Project History

This file preserves historical phase context that used to make `project_notes.md` too long. Use `project_notes.md` for the current operating state and this file when older phase chronology or decisions matter.

## Phase Timeline

- 2026-06-05: Captured product vision, stack choices, harness-engineering approach, DDD/hexagonal direction, Figma reference assessment, and phased implementation strategy.
- 2026-06-05: Added the repository harness: `project_notes.md`, architecture docs, product docs, domain maps, execution plans, review protocol, `.gitignore`, `.gitkeep` placeholders, and repository checks.
- 2026-06-05: Completed Phase 01 foundation runtime with FastAPI `/health`, React/Vite shell, Celery worker shell, aiogram shell, Docker Compose, and root npm scripts.
- 2026-06-05: Completed Phase 02 service request intake with persisted request creation, request numbers, sqlite local persistence, PostgreSQL target schema, and the public intake form.
- 2026-06-05: Completed Phase 03 client status and notifications contract with public status snapshots, clarification answers, Telegram opt-in token/link generation, and status page UI.
- 2026-06-05: Added the PostgreSQL persistence slice so Docker Compose API runtime uses PostgreSQL via `SERVICEOPS_DATABASE_URL`.
- 2026-06-05 to 2026-06-06: Completed Phase 04 dispatcher MVP with protected-in-scope internal dispatcher routes, request list/detail/actions, manual assignment metadata, internal notes, and dispatcher workspace.
- 2026-06-06: Completed Phase 05 staff access with `/staff/login`, role vocabulary, bearer-token protection for internal APIs, staff login UI, and route guards.
- 2026-06-07: Completed Phase 06 knowledge-base RAG with document ingestion, chunking, deterministic embeddings, pgvector schema, retrieval with source metadata, worker embedding task boundary, and seed repair knowledge.
- 2026-06-07: Completed Phase 07 AI agent workflows with deterministic prompt assembly, source-backed dispatcher suggestions, suggestion persistence, protected AI routes, and dispatcher AI panel.
- 2026-06-07: Completed Phase 08 technician and inventory with technician assigned-visit workflow, diagnosis/result capture, parts catalog, stock counts, parts-used stock decrement, and technician/inventory workspaces.
- 2026-06-07: Inserted Phase 09 staff admin before deployment and completed persisted staff accounts, password hashes, admin-only lifecycle API, audit events, persisted login before development fallback, and `/admin` workspace.
- 2026-06-07: Completed Phase 10 deployment and operations with production Compose, expanded env docs, JSON logging, PostgreSQL migration command, backup/restore scripts, smoke-test script, n8n workflow records, operations runbooks, and local review fixes.
- 2026-06-07: Completed documentation audit after Phase 10, correcting current-stack descriptions, notification/deployment boundaries, public status endpoint docs, and production staff bootstrap caveats.
- 2026-06-10: Completed Phase 11 production launch readiness with first-admin bootstrap, launch smoke evidence template, persisted-staff smoke check, and runbook updates.
- 2026-06-10: Completed Phase 12 notification automation with backend-to-n8n webhook emission, delivery-result persistence, staff delivery visibility, Telegram opt-in token consumption, and workflow exports.
- 2026-06-10: Completed Phase 13 live AI provider and knowledge-base content with OpenAI-compatible AI/embedding adapters, curated repair knowledge seed content, RAG evaluation fixtures, and AI provider operations guidance.
- 2026-06-10: Completed documentation audit after Phase 13, correcting current product, architecture, notification domain, repository map, and review handoff docs.
- 2026-06-15: Completed Phase 14 operational hardening with safe structured logs across API, worker, and Telegram bot; staff-auth audit expansion; operational diagnostics; incident response; restore dry-run guidance; and launch evidence updates.
- 2026-06-15: Hardened AI/RAG prompt behavior with relevance filtering, knowledge-gap fallback instructions, electrical-shock safety triage, and regression tests for unknown topics.
- 2026-06-15: Completed Phase 15 scheduling depth with structured appointments, dispatcher create/reschedule/cancel APIs, technician schedule visibility, customer-safe appointment snapshots, and scheduling review fixes.
- 2026-06-15: Completed Phase 16 inventory reservations with request-linked reservations, stock movement audit records, low-stock visibility, part compatibility records, and technician reserved-parts consumption.
- 2026-06-15: Recorded first Aeza VPS/Dokploy test deployment evidence, including API/web/PostgreSQL/Redis health, migrations, first-admin bootstrap, n8n callback path, backup, restore drill, and worker Redis dependency fix.
- 2026-06-16: Hardened production paths after Phase 16 with atomic PostgreSQL request-number generation, appointment overlap exclusion and deadlock handling, row locks for inventory stock/reservation mutations, safer notification delivery rowcount logging, production Telegram bot default startup, no direct n8n port publication, and expired staff-session redirects in the web app.
- 2026-06-16: Completed documentation audit after Phase 16 and post-phase production hardening, updating current-state entry points, review artifacts, domain boundaries, and repository checks.
- 2026-06-16: Moved production notification automation from the earlier n8n Cloud path to the self-hosted VPS n8n service, imported and activated repository workflow exports, verified request-created delivery on `CFX-20260616-000008`, and documented the one-active-polling rule while local and production share one Telegram bot token.
- 2026-06-17: Captured the post-Phase-16 roadmap after internal and external review. The next sequence is public demo closure, portfolio packaging, frontend decomposition, owner dashboard/SLA, operational n8n automation, procurement lite, technician recommendations, and a bounded AI assistant with tools.
- 2026-06-17: Inserted Phase 17a after the real-domain demo check showed slow first hero image loading from large public hero PNG assets. This keeps demo performance optimization separate from Phase 17 launch/security work and before Phase 18 portfolio packaging.

## Historical Decisions

- The backend is a modular monolith with DDD/hexagonal boundaries.
- PostgreSQL with pgvector is the default SQL and RAG store.
- The Figma reference drives the public client UI, but exported code is reference material, not production structure.
- Automation features are operational workflows with human confirmation, not decorative client-facing claims.
- `AGENTS.md` files act as maps and context entry points.
- Repo-specific workflow drafts are stored in `docs/agent-skills` until the project is ready to activate them.
- Before executing any phase, create a detailed implementation plan; phase files are slice maps, not execution-ready implementation plans.
- Local Docker Compose publishes API, web, PostgreSQL, and Redis on `127.0.0.1` only.
- Docker Compose API persistence uses PostgreSQL through `SERVICEOPS_DATABASE_URL`; direct Python defaults to sqlite for lightweight local imports and tests.
- Public status snapshots must not expose internal notes, AI suggestions, source chunks, prompt inputs, provider metadata, staff accounts, password reset data, audit events, technician internal notes, parts-used notes, stock counts, part IDs, or inventory metadata.
- Dispatcher APIs require a `dispatcher` staff bearer token.
- Technician APIs require the `technician` role and expose only requests assigned to that staff username.
- Inventory APIs require the `inventory` role.
- Admin account lifecycle actions require the `admin` role, create staff audit records, and block deactivating or removing the last active admin.
- Local-development staff users are separated from production account management.
- Production deployment uses `docker-compose.production.yml`; local Compose remains localhost-only.
- PostgreSQL and Redis must remain private Docker-network services in production.
- API, worker, and Telegram bot services emit structured JSON logs to stdout for Dokploy log collection.
- n8n can automate delivery and operational routing but must not own service-request state, staff identity, customer answers, inventory counts, or repair lifecycle transitions.
- Production backups use PostgreSQL custom-format dumps with checksum files, and restore drills should run against a non-production database.
- AI and embedding providers default to deterministic local/test mode; OpenAI-compatible live providers are enabled only through secret-backed environment variables.
- PostgreSQL production paths use database-level concurrency guards where practical: request-number sequencing, appointment overlap exclusion, and row locks for stock/reservation mutations.
- Post-Phase-16 roadmap entries are slice maps, not detailed implementation plans. Detailed plans remain just-in-time artifacts created from current code and docs before each phase starts.
- Phase 17a is intentionally placed after Phase 17 because it depends on a stable public route for real first-load checks, and before Phase 18 so portfolio screenshots and walkthroughs use the optimized demo.

## Deferred Work Ledger

- Binary attachment storage.
- Full client accounts.
- Full technician profiles, durable availability calendar, automatic matching, route optimization, and customer self-scheduling.
- Warehouses, suppliers, purchase orders, barcode scanning, billing totals, and warranty stock handling.
- Provider latency/error dashboards and external log shipping.
- Public-launch readiness after VPS test deployment: domains, HTTPS, closure of temporary direct test ports, Dokploy admin access restriction, disposable staff-route smoke, and repeat smoke checks after real database transfer.
