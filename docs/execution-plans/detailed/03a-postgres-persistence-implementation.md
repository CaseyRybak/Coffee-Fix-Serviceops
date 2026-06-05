# PostgreSQL Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist service requests, status history, clarification answers, and Telegram opt-in records in PostgreSQL when the app runs through Docker Compose.

**Architecture:** Keep the existing sqlite repository for fast injected tests and local fallback, but add a PostgreSQL repository that implements the same service-request store interface. `create_app()` should use an injected repository in tests, otherwise build the repository from settings: PostgreSQL for `postgresql://` or `postgresql+psycopg://` URLs, sqlite for `sqlite://` URLs or explicit fallback paths. PostgreSQL initialization applies the existing migration SQL so Docker Compose starts with the required tables.

**Tech Stack:** FastAPI, Pydantic settings, sqlite3, psycopg, PostgreSQL 16 via Docker Compose, pytest, Docker Compose.

---

## Execution Status

- Completed: repository selection tests and factory.
- Completed: psycopg dependency and PostgreSQL service-request repository.
- Completed: idempotent migration application during PostgreSQL repository initialization.
- Completed: documentation and repository harness updates.
- Completed: Docker Compose PostgreSQL persistence was verified from the user's WSL terminal: a newly created request appeared in `service_requests` via `psql`.

## Task 1: Repository Selection

**Files:**
- Modify: `apps/api/src/serviceops_api/config.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Create: `apps/api/tests/test_repository_selection.py`

- [x] **Step 1: Write failing tests**

Add tests that prove repository factory behavior:
- injected repositories are still used unchanged by `create_app()`;
- `postgresql+psycopg://...` settings create a PostgreSQL repository;
- `sqlite:///:memory:` settings create a sqlite repository.

- [x] **Step 2: Implement repository factory**

Add `create_service_request_repository(settings)` and wire `create_app()` through it when no repository is injected.

## Task 2: PostgreSQL Repository

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/uv.lock`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql`

- [x] **Step 1: Add psycopg dependency**

Add `psycopg[binary]` to API runtime dependencies.

- [x] **Step 2: Implement PostgreSQL repository**

Implement the same public methods as `ServiceRequestRepository` using psycopg and PostgreSQL placeholders. Reuse the migration SQL during initialization.

- [x] **Step 3: Preserve sqlite tests**

Existing API tests should continue to inject `ServiceRequestRepository.in_memory()` and pass without Docker.

## Task 3: Docker Compose Verification

**Files:**
- Modify: `project_notes.md`
- Modify: `docs/harness/repository-map.md`
- Modify: `tools/repo-checks/check_docs.py`

- [x] **Step 1: Update docs**

Record that Docker Compose API persistence now uses PostgreSQL, while unit tests keep sqlite in-memory repositories.

- [ ] **Step 2: Verify locally**

Run:

```bash
python3 tools/repo-checks/check_docs.py
cd apps/api && uv run --extra dev pytest
cd apps/worker && uv run --extra dev pytest
cd apps/telegram-bot && uv run --extra dev pytest
npm run web:test
npm run web:lint
npm run web:build
docker compose config
docker compose up -d postgres
docker compose run --rm api python -c "from serviceops_api.main import create_app; create_app(); print('api repository initialized')"
docker compose down
```

Expected: all commands exit 0. The compose run should initialize PostgreSQL tables from the migration.

Current local status: all non-Docker verification commands pass. Live Docker Compose persistence was verified from the user's WSL terminal by creating request `CFX-20260605-000001` and reading it from PostgreSQL with `psql`.
