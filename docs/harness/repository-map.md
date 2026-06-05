# Repository Map

## Root

- `AGENTS.md`: entry map for contributors.
- `project_notes.md`: current status, latest changes, active focus, and next steps.
- `ARCHITECTURE.md`: system and domain architecture overview.
- `README.md`: human-readable project introduction.
- `package.json`: root developer scripts for local web checks and dev server.
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
- `docs/execution-plans/completed/`: completed phase plans.
- `docs/review/subagent-review-protocol.md`: review protocol for every slice.
- `docs/review/phase-02-review.md`: Phase 02 review artifact for service request intake.
- `docs/review/phase-03-review.md`: Phase 03 review artifact for client status and notifications.

## Workflow Skills

- `docs/agent-skills/skill-catalog.md`: skill list.
- `docs/agent-skills/<skill>/SKILL.md`: portable repo-specific workflow drafts.

## Code Areas

- `apps/api`: FastAPI backend with `/health`, service request intake, public status, answer submission, and Telegram opt-in contracts.
- `apps/api/src/serviceops_api/service_requests`: service request intake/status API, use cases, models, and repository.
- `apps/web`: React/Vite public intake form, request-number success state, and public status page.
- `apps/worker`: Celery worker shell.
- `apps/telegram-bot`: aiogram bot shell.
- `packages/shared-kernel`: shared domain primitives.
- `packages/observability`: logging and metrics helpers.
- `packages/test-harness`: test utilities.

## Runtime Harness

- `.env.example`: local environment template.
- `docker-compose.yml`: localhost-only local PostgreSQL, Redis, API, web on port 3000, worker, and optional Telegram bot profile.
- `apps/api/Dockerfile`: API container definition.
- `apps/web/Dockerfile`: web container definition.
- `apps/worker/Dockerfile`: worker container definition.
- `apps/telegram-bot/Dockerfile`: Telegram bot container definition.

## Repository Checks

- `tools/repo-checks/check_docs.py`: validates the documentation harness.
- `tools/repo-checks/README.md`: documents how to run repository checks.
