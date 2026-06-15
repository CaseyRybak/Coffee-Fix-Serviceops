# Repository Map

## Root

- `AGENTS.md`: entry map for contributors.
- `project_notes.md`: compact current operating dashboard, active focus, next steps, entry points, verification commands, and current decisions.
- `docs/harness/project-history.md`: archived phase chronology, historical decisions, and deferred work ledger.
- `ARCHITECTURE.md`: system and domain architecture overview.
- `README.md`: human-readable project introduction.
- `package.json`: root developer scripts for local web checks and dev server.
- `docker-compose.production.yml`: production-oriented Compose definition for Dokploy/VPS deployment.
- `reference/figma`: exported Figma/Vite reference for the public UI.

## Product Docs

- `docs/product/vision.md`: product purpose and users.
- `docs/product/mvp-scope.md`: MVP and deferred scope.
- `docs/product/figma-reference-review.md`: how to use the Figma reference.

## Architecture Docs

- `docs/architecture/harness-engineering.md`: repository-guided development approach.
- `docs/architecture/domain-architecture.md`: DDD and hexagonal structure.
- `docs/architecture/tech-stack.md`: selected technologies.

## Domain Docs

- `docs/domain-maps/index.md`: domain overview and links.
- `domains/<domain>/AGENTS.md`: local domain map.
- `domains/<domain>/domain.md`: domain responsibility and first use cases.

## Plans And Review

- `docs/execution-plans/index.md`: phase list.
- `docs/execution-plans/phases/`: phase slice maps.
- `docs/execution-plans/detailed/`: just-in-time detailed implementation plans.
- `docs/execution-plans/detailed/README.md`: current-versus-historical detailed plan guidance.
- `docs/execution-plans/completed/README.md`: reserved archive convention for completed plans.
- `docs/execution-plans/detailed/03a-postgres-persistence-implementation.md`: PostgreSQL persistence technical slice between Phase 03 and Phase 04.
- `docs/execution-plans/detailed/04-dispatcher-mvp-implementation.md`: completed detailed plan for the dispatcher MVP.
- `docs/execution-plans/detailed/05-staff-access-and-roles-implementation.md`: completed detailed plan for staff login and role protection.
- `docs/execution-plans/detailed/06-knowledge-base-rag-implementation.md`: completed detailed plan for knowledge-base RAG.
- `docs/execution-plans/detailed/07-ai-agent-workflows-implementation.md`: completed detailed plan for AI-assisted dispatcher workflows.
- `docs/execution-plans/detailed/08-technician-and-inventory-implementation.md`: completed detailed plan for technician mobile flow and basic parts tracking.
- `docs/execution-plans/detailed/09-staff-admin-and-user-management-implementation.md`: completed detailed plan for persisted staff accounts and admin user management.
- `docs/execution-plans/detailed/10-deployment-and-operations-implementation.md`: completed detailed plan for Dokploy deployment, backups, observability, n8n workflows, and smoke tests.
- `docs/execution-plans/detailed/11-production-launch-readiness-implementation.md`: completed detailed plan for first-admin bootstrap and launch smoke evidence.
- `docs/execution-plans/detailed/12-notification-automation-implementation.md`: completed detailed plan for backend-to-n8n events, delivery persistence, workflow exports, and staff delivery visibility.
- `docs/execution-plans/detailed/13-live-ai-provider-and-knowledge-base-content-implementation.md`: completed detailed plan for OpenAI-compatible providers, curated repair knowledge, and RAG evaluation.
- `docs/execution-plans/detailed/14-operational-hardening-implementation.md`: completed detailed plan for observability, audit expansion, restore dry-runs, incident response, and diagnostics.
- `docs/execution-plans/completed/`: reserved archive directory for completed phase plans if the project later moves them out of `detailed/`.
- `docs/review/subagent-review-protocol.md`: review protocol for every slice.
- `docs/review/phase-02-review.md`: Phase 02 review artifact for service request intake.
- `docs/review/phase-03-review.md`: Phase 03 review artifact for client status and notifications.
- `docs/review/phase-04-review.md`: Phase 04 review artifact for dispatcher MVP.
- `docs/review/phase-05-review.md`: Phase 05 review artifact for staff access and roles.
- `docs/review/phase-06-review.md`: Phase 06 review artifact for knowledge-base RAG.
- `docs/review/phase-07-review.md`: Phase 07 review artifact for AI agent workflows.
- `docs/review/phase-08-review.md`: Phase 08 review artifact for technician workflow and inventory basics.
- `docs/review/phase-09-review.md`: Phase 09 review artifact for staff admin and user management.
- `docs/review/phase-10-review.md`: Phase 10 review artifact for deployment and operations.
- `docs/review/phase-11-review.md`: Phase 11 review artifact for production launch readiness.
- `docs/review/phase-12-review.md`: Phase 12 review artifact for notification automation.
- `docs/review/phase-13-review.md`: Phase 13 review artifact for live provider adapters and curated knowledge-base content.
- `docs/review/phase-14-review.md`: Phase 14 review artifact for operational hardening.
- `docs/review/documentation-audit-2026-06-07.md`: documentation consistency and quality audit after Phase 10.
- `docs/review/documentation-audit-2026-06-10.md`: documentation consistency and quality audit after Phase 13.
- `docs/review/documentation-audit-2026-06-15.md`: documentation readiness audit before Phase 14 implementation.
- `docs/review/documentation-audit-2026-06-15-current-state.md`: current-state documentation audit after Phase 14 and AI/RAG fallback hardening.

## Workflow Skills

- `docs/agent-skills/skill-catalog.md`: skill list.
- `docs/agent-skills/<skill>/SKILL.md`: portable repo-specific workflow drafts.

## Operations Docs

- `docs/operations/deployment-runbook.md`: concrete Dokploy/VPS deployment runbook.
- `docs/operations/backup-restore.md`: PostgreSQL backup, restore, checksum, retention, and restore-drill procedure.
- `docs/operations/launch-smoke-evidence.md`: first-launch evidence template for production smoke checks and go/no-go decisions.
- `docs/operations/smoke-tests.md`: manual and scripted deployment smoke-test checklist.
- `docs/operations/operational-diagnostics.md`: structured-log fields, request tracing, log queries, read-only PostgreSQL checks, and evidence redaction rules.
- `docs/operations/incident-response.md`: first-line incident checklist for degraded API, web, PostgreSQL, Redis, worker, Telegram, n8n, notifications, AI/RAG, and restore decisions.
- `docs/operations/ai-providers.md`: deterministic and OpenAI-compatible AI/embedding provider operations guide, including RAG relevance filtering, knowledge-gap fallback, safety triage, and seed-update caveats.
- `docs/operations/n8n-workflows.md`: n8n workflow contracts, live workflow IDs, import guidance, and delivery-result callback shape.
- `tools/operations/`: operational shell scripts and regression checks for backup, restore, and smoke checks.

## Code Areas

- `apps/api`: FastAPI backend with `/health`, service request intake, public status, answer submission, Telegram opt-in/linking contracts, notification callbacks, dispatcher routes, technician routes, inventory routes, staff admin routes, knowledge-base RAG routes, AI suggestion routes, sqlite test persistence, and PostgreSQL Compose persistence.
- `apps/api/src/serviceops_api/ai_agents`: AI suggestion models, prompt assembly with RAG relevance filtering, deterministic and OpenAI-compatible providers, knowledge-gap fallback behavior, sqlite/PostgreSQL repositories, dispatcher use cases, and protected routes.
- `apps/api/src/serviceops_api/service_requests`: service request intake/status/dispatcher API, use cases, models, sqlite repository, PostgreSQL repository, and repository factory.
- `apps/api/src/serviceops_api/technicians`: technician assigned-visit models, protected routes, and workflow use cases for diagnosis, repair result, and parts used.
- `apps/api/src/serviceops_api/inventory`: parts catalog models, sqlite/PostgreSQL repositories, inventory use cases, protected inventory routes, and stock decrement behavior.
- `apps/api/src/serviceops_api/staff_management`: persisted staff account models, sqlite/PostgreSQL repositories, admin account lifecycle use cases, local persisted staff seed command, audit records, and protected admin routes.
- `apps/api/src/serviceops_api/operations`: migration and first-admin bootstrap commands for production operations.
- `apps/api/src/serviceops_api/knowledge_base`: knowledge document models, chunking, deterministic and OpenAI-compatible embeddings, sqlite/PostgreSQL repositories, ingestion and retrieval use cases, API routes, curated seed repair documents, and RAG evaluation fixtures.
- `apps/web`: React/Vite public intake form, request-number success state, public status page, dispatcher workspace, dispatcher AI suggestion panel, technician workspace, inventory workspace, and admin staff-management workspace.
- `apps/worker`: Celery worker shell and knowledge-base embedding task boundary with deterministic/live-compatible provider selection.
- `apps/telegram-bot`: aiogram bot for `/start <token>` Telegram opt-in linking.
- `packages/shared-kernel`: shared domain primitives.
- `packages/observability`: logging and metrics helpers.
- `packages/test-harness`: test utilities.

## Runtime Harness

- `.env.example`: local environment template.
- `docker-compose.yml`: localhost-only local PostgreSQL, Redis, API using PostgreSQL persistence, web on port 3000, worker, and optional Telegram bot profile.
- `docker-compose.production.yml`: production-oriented API, web, worker, Telegram bot, PostgreSQL, Redis, and n8n Compose definition.
- `apps/api/Dockerfile`: API container definition.
- `apps/web/Dockerfile`: web container definition.
- `apps/worker/Dockerfile`: worker container definition.
- `apps/telegram-bot/Dockerfile`: Telegram bot container definition.

## Repository Checks

- `tools/repo-checks/check_docs.py`: validates the documentation harness.
- `tools/repo-checks/README.md`: documents how to run repository checks.
