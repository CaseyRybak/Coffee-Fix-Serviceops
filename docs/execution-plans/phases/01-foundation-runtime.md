# Phase 01: Foundation Runtime

> For agentic workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Create the runnable application foundation: FastAPI, React/Vite, PostgreSQL, Redis, worker shell, Telegram bot shell, and Docker Compose.

## Context To Read

- `ARCHITECTURE.md`
- `docs/architecture/tech-stack.md`
- `docs/architecture/domain-architecture.md`
- `docs/product/mvp-scope.md`

## Deliverables

- `apps/api` FastAPI app with `/health`.
- `apps/web` React/Vite app with a simple shell.
- `apps/worker` Celery worker shell.
- `apps/telegram-bot` aiogram shell.
- PostgreSQL and Redis services in Docker Compose.
- Environment example file.
- Basic pytest and frontend test/lint commands.

## Acceptance Criteria

- `docker compose up` starts the core local environment.
- API healthcheck returns healthy status.
- Backend tests run.
- Frontend build runs.
- `project_notes.md` identifies Phase 02 as the next active phase.

## Subagent Review Gate

Review runtime commands, environment clarity, Docker Compose legibility, and whether application shells match the architecture map.
