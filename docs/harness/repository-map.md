# Repository Map

## Root

- `AGENTS.md`: entry map for agents.
- `project_notes.md`: current status, latest changes, active focus, and next steps.
- `ARCHITECTURE.md`: system and domain architecture overview.
- `README.md`: human-readable project introduction.
- `reference/figma`: exported Figma/Vite reference for the public UI.

## Product Docs

- `docs/product/vision.md`: product purpose and users.
- `docs/product/mvp-scope.md`: MVP and deferred scope.
- `docs/product/figma-reference-review.md`: how to use the Figma reference.

## Architecture Docs

- `docs/architecture/harness-engineering.md`: agent-first repository approach.
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

## Agent Skills

- `docs/agent-skills/skill-catalog.md`: skill list.
- `docs/agent-skills/<skill>/SKILL.md`: portable repo-specific skills.

## Future Code Areas

- `apps/api`: FastAPI backend with `/health`.
- `apps/web`: React/Vite frontend shell.
- `apps/worker`: Celery worker shell.
- `apps/telegram-bot`: aiogram bot shell.
- `packages/shared-kernel`: shared domain primitives.
- `packages/observability`: logging and metrics helpers.
- `packages/test-harness`: test utilities.

## Runtime Harness

- `.env.example`: local environment template.
- `docker-compose.yml`: local PostgreSQL, Redis, API, web, worker, and optional Telegram bot profile.
- `apps/api/Dockerfile`: API container definition.
- `apps/web/Dockerfile`: web container definition.
- `apps/worker/Dockerfile`: worker container definition.
- `apps/telegram-bot/Dockerfile`: Telegram bot container definition.

## Repository Checks

- `tools/repo-checks/check_docs.py`: validates the documentation harness.
- `tools/repo-checks/README.md`: documents how to run repository checks.
