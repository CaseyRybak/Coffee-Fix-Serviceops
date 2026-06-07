# Repository Map

## Root

- `AGENTS.md`: entry map for contributors.
- `project_notes.md`: current status, latest changes, active focus, and next steps.
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
- `docs/execution-plans/detailed/03a-postgres-persistence-implementation.md`: PostgreSQL persistence technical slice between Phase 03 and Phase 04.
- `docs/execution-plans/detailed/04-dispatcher-mvp-implementation.md`: completed detailed plan for the dispatcher MVP.
- `docs/execution-plans/detailed/05-staff-access-and-roles-implementation.md`: completed detailed plan for staff login and role protection.
- `docs/execution-plans/detailed/06-knowledge-base-rag-implementation.md`: completed detailed plan for knowledge-base RAG.
- `docs/execution-plans/detailed/07-ai-agent-workflows-implementation.md`: completed detailed plan for AI-assisted dispatcher workflows.
- `docs/execution-plans/detailed/08-technician-and-inventory-implementation.md`: completed detailed plan for technician mobile flow and basic parts tracking.
- `docs/execution-plans/detailed/09-staff-admin-and-user-management-implementation.md`: completed detailed plan for persisted staff accounts and admin user management.
- `docs/execution-plans/detailed/10-deployment-and-operations-implementation.md`: completed detailed plan for Dokploy deployment, backups, observability, n8n workflows, and smoke tests.
- `docs/execution-plans/completed/`: completed phase plans.
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

## Workflow Skills

- `docs/agent-skills/skill-catalog.md`: skill list.
- `docs/agent-skills/<skill>/SKILL.md`: portable repo-specific workflow drafts.

## Operations Docs

- `docs/operations/deployment-runbook.md`: concrete Dokploy/VPS deployment runbook.
- `docs/operations/backup-restore.md`: PostgreSQL backup, restore, checksum, retention, and restore-drill procedure.
- `docs/operations/smoke-tests.md`: manual and scripted deployment smoke-test checklist.
- `docs/operations/n8n-workflows.md`: n8n workflow design records for request and status notifications.
- `tools/operations/`: operational shell scripts and regression checks for backup, restore, and smoke checks.

## Code Areas

- `apps/api`: FastAPI backend with `/health`, service request intake, public status, answer submission, Telegram opt-in contracts, dispatcher routes, technician routes, inventory routes, staff admin routes, knowledge-base RAG routes, AI suggestion routes, sqlite test persistence, and PostgreSQL Compose persistence.
- `apps/api/src/serviceops_api/ai_agents`: AI suggestion models, prompt assembly, deterministic provider, sqlite/PostgreSQL repositories, dispatcher use cases, and protected routes.
- `apps/api/src/serviceops_api/service_requests`: service request intake/status/dispatcher API, use cases, models, sqlite repository, PostgreSQL repository, and repository factory.
- `apps/api/src/serviceops_api/technicians`: technician assigned-visit models, protected routes, and workflow use cases for diagnosis, repair result, and parts used.
- `apps/api/src/serviceops_api/inventory`: parts catalog models, sqlite/PostgreSQL repositories, inventory use cases, protected inventory routes, and stock decrement behavior.
- `apps/api/src/serviceops_api/staff_management`: persisted staff account models, sqlite/PostgreSQL repositories, admin account lifecycle use cases, local persisted staff seed command, audit records, and protected admin routes.
- `apps/api/src/serviceops_api/knowledge_base`: knowledge document models, chunking, deterministic embeddings, sqlite/PostgreSQL repositories, ingestion and retrieval use cases, API routes, and seed repair documents.
- `apps/web`: React/Vite public intake form, request-number success state, public status page, dispatcher workspace, dispatcher AI suggestion panel, technician workspace, inventory workspace, and admin staff-management workspace.
- `apps/worker`: Celery worker shell and knowledge-base embedding task boundary.
- `apps/telegram-bot`: aiogram bot shell.
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
