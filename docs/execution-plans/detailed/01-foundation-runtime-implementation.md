# Foundation Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the runnable Phase 01 foundation for API, web, worker, Telegram bot, PostgreSQL, Redis, and local verification.

**Architecture:** This phase creates runtime shells only. The API exposes health status and keeps application/domain boundaries ready for later phases; the web app is a React/Vite shell without request-intake behavior; worker and bot shells validate configuration without adding domain workflows.

**Tech Stack:** Python, FastAPI, Pydantic settings, pytest, httpx, Celery, aiogram, React, Vite, TypeScript, Node test runner through `tsx`, Docker Compose, PostgreSQL, Redis.

---

## Execution Status

- Completed: created backend runtime shell and tests.
- Completed: created worker and Telegram bot shells.
- Completed: created React/Vite web shell and build/test/lint commands.
- Completed: created Docker Compose and environment example.
- Completed: updated repository checks, project notes, repository map, and Phase 01 review artifact.
- Verification gap: Docker CLI is not installed in the current environment, so `docker compose config` and `docker compose up` must be verified on a machine with Docker.

## Task 1: API Health Runtime

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/Dockerfile`
- Create: `apps/api/src/serviceops_api/__init__.py`
- Create: `apps/api/src/serviceops_api/config.py`
- Create: `apps/api/src/serviceops_api/health.py`
- Create: `apps/api/src/serviceops_api/main.py`
- Create: `apps/api/tests/test_health.py`
- Delete: `apps/api/.gitkeep`

- [x] **Step 1: Write health endpoint tests**

Create `apps/api/tests/test_health.py` with tests for `GET /health` returning service name, environment, and healthy dependency placeholders.

- [x] **Step 2: Run backend tests and verify red**

Run `cd apps/api && python3 -m pytest`.

Expected before implementation: import failure because `serviceops_api` does not exist.

- [x] **Step 3: Implement FastAPI app**

Create config, health payload, and app factory modules. Keep dependency status local and deterministic for Phase 01.

- [x] **Step 4: Run backend tests and verify green**

Run `cd apps/api && python3 -m pytest`.

Expected after implementation: all API tests pass.

## Task 2: Worker And Telegram Bot Shells

**Files:**
- Create: `apps/worker/pyproject.toml`
- Create: `apps/worker/Dockerfile`
- Create: `apps/worker/src/serviceops_worker/__init__.py`
- Create: `apps/worker/src/serviceops_worker/celery_app.py`
- Create: `apps/worker/tests/test_celery_app.py`
- Delete: `apps/worker/.gitkeep`
- Create: `apps/telegram-bot/pyproject.toml`
- Create: `apps/telegram-bot/Dockerfile`
- Create: `apps/telegram-bot/src/serviceops_telegram_bot/__init__.py`
- Create: `apps/telegram-bot/src/serviceops_telegram_bot/config.py`
- Create: `apps/telegram-bot/src/serviceops_telegram_bot/main.py`
- Create: `apps/telegram-bot/tests/test_config.py`
- Delete: `apps/telegram-bot/.gitkeep`

- [x] **Step 1: Write shell tests**

Create tests that verify the Celery app name, Redis broker default, Telegram token validation, and bot disabled behavior.

- [x] **Step 2: Run tests and verify red**

Run `cd apps/worker && python3 -m pytest` and `cd apps/telegram-bot && python3 -m pytest`.

Expected before implementation: import failures for missing packages.

- [x] **Step 3: Implement shells**

Create importable worker and Telegram bot modules. The bot shell must not start polling without `TELEGRAM_BOT_TOKEN`.

- [x] **Step 4: Run tests and verify green**

Run worker and bot pytest commands again.

Expected after implementation: all shell tests pass.

## Task 3: React/Vite Web Shell

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/index.html`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/tsconfig.node.json`
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/App.test.tsx`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/src/styles.css`
- Create: `apps/web/src/vite-env.d.ts`
- Delete: `apps/web/.gitkeep`

- [x] **Step 1: Write shell tests**

Create Node test runner tests through `tsx` that verify the product shell renders service operations copy and does not expose public AI messaging.

- [x] **Step 2: Run frontend tests and verify red**

Run `cd apps/web && npm test`.

Expected before implementation: missing source files or failing render test.

- [x] **Step 3: Implement React shell**

Create a compact ServiceOps runtime shell with status, queue, and operations panels. Keep content public-service oriented and avoid AI claims.

- [x] **Step 4: Run frontend tests and build**

Run `cd apps/web && npm test`, `cd apps/web && npm run lint`, and `cd apps/web && npm run build`.

Expected after implementation: tests and build pass.

## Task 4: Compose And Environment

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Modify: `.gitignore`

- [x] **Step 1: Create local environment file**

Add `.env.example` with API, web, worker, bot, PostgreSQL, Redis, and Telegram placeholders.

- [x] **Step 2: Create Docker Compose services**

Add `api`, `web`, `worker`, `telegram-bot`, `postgres`, and `redis` services. Use health checks for API, PostgreSQL, and Redis.

- [x] **Step 3: Verify Compose config**

Run `docker compose config`.

Expected: Compose renders without configuration errors. Actual in this environment: `docker: command not found`; this must be verified on a machine with Docker installed.

## Task 5: Harness Updates And Review

**Files:**
- Modify: `tools/repo-checks/check_docs.py`
- Modify: `docs/harness/repository-map.md`
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-01-review.md`

- [x] **Step 1: Extend repository checks**

Require Phase 01 runtime files, `.env.example`, `docker-compose.yml`, and `docs/review/phase-01-review.md` after Phase 01 is complete.

- [x] **Step 2: Update project notes and maps**

Set active focus to Phase 02 planning and add Phase 01 artifacts to active artifacts.

- [x] **Step 3: Run full local verification**

Run:

```bash
python3 tools/repo-checks/check_docs.py
cd apps/api && python3 -m pytest
cd apps/worker && python3 -m pytest
cd apps/telegram-bot && python3 -m pytest
cd apps/web && npm test
cd apps/web && npm run lint
cd apps/web && npm run build
docker compose config
```

Expected: all commands exit 0. Actual in this environment: all non-Docker commands exit 0; `docker compose config` cannot run because Docker CLI is not installed.

- [x] **Step 4: Request Phase 01 review**

Run the review protocol from `docs/review/subagent-review-protocol.md` with the Phase 01 slice, detailed plan, changed-file list, and verification output.

- [x] **Step 5: Resolve blocking review findings**

Apply any required fixes, re-run affected verification, and update `docs/review/phase-01-review.md`.
