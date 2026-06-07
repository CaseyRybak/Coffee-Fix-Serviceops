# Phase 10 Deployment And Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare Coffee Fix ServiceOps for VPS/Dokploy deployment with production environment documentation, backups, basic observability, n8n workflow design, and smoke-test runbooks.

**Architecture:** Keep the application as the existing Dockerized modular monolith: API, web, worker, Telegram bot, PostgreSQL with pgvector, Redis, and n8n. Phase 10 should add deployable operations artifacts and lightweight runtime instrumentation without changing business workflows or exposing internal workspaces through public navigation.

**Tech Stack:** Docker Compose, Dokploy, PostgreSQL/pgvector, Redis, n8n, FastAPI, Celery, aiogram, React/Vite, pytest, node:test, shell scripts.

---

## Scope Decisions

- Phase 10 prepares deployment and operations artifacts; it does not deploy to a real VPS from the development machine.
- Dokploy is documented through Compose-based app definitions and runbook steps rather than a vendor-specific exported state file.
- Production public exposure should route only HTTP web/API services through Dokploy or its reverse proxy. PostgreSQL and Redis remain private Docker-network services.
- Local `docker-compose.yml` keeps its localhost-only safety posture.
- A new production Compose file can publish API/web/n8n ports for Dokploy routing, but database and Redis ports must not be exposed.
- Staff seed accounts are local-development only. Production setup must create persisted admin and staff users through the API/seed command after setting real secrets.
- Structured logging should be basic JSON logs with service, environment, level, logger, message, and timestamp. Metrics, tracing, alerting, log shipping, and uptime monitors remain follow-up operations work.
- n8n documentation should define request/status notification workflow contracts and operational behavior. Backend event emission to n8n can be documented as a manual/webhook smoke path in this slice unless the implementation explicitly adds outbound webhook calls with tests.
- No commits or pushes are part of this phase unless the user gives a direct instruction in the current conversation turn.

## File Responsibility Map

- Create: `docker-compose.production.yml` for Dokploy/VPS-oriented service definitions.
- Modify: `.env.example` to list production-safe variables, n8n variables, webhook placeholders, public URLs, backup settings, and secret guidance.
- Create: `apps/api/src/serviceops_api/observability.py` for API JSON logging setup.
- Modify: `apps/api/src/serviceops_api/main.py` to initialize API logging once during app creation.
- Create: `apps/api/tests/test_observability.py` for JSON logging format and app logging initialization.
- Create: `apps/worker/src/serviceops_worker/observability.py` for worker JSON logging setup.
- Modify: `apps/worker/src/serviceops_worker/celery_app.py` to initialize worker logging before Celery app creation.
- Create: `apps/worker/tests/test_observability.py` for worker logging setup.
- Create: `apps/telegram-bot/src/serviceops_telegram_bot/observability.py` for Telegram bot JSON logging setup.
- Modify: `apps/telegram-bot/src/serviceops_telegram_bot/main.py` to initialize bot logging before runtime behavior.
- Create: `apps/telegram-bot/tests/test_observability.py` for bot logging setup.
- Create: `apps/api/src/serviceops_api/operations/__init__.py` for operations package exports.
- Create: `apps/api/src/serviceops_api/operations/migrate.py` for a migration command that initializes PostgreSQL repositories with the configured database URL.
- Create: `apps/api/tests/test_operations_migrate.py` for migration command behavior and sqlite rejection.
- Create: `tools/operations/postgres_backup.sh` for a timestamped `pg_dump` backup command.
- Create: `tools/operations/postgres_restore.sh` for a documented `pg_restore` restore command.
- Create: `tools/operations/smoke_test.sh` for API, web, intake, status, worker, Telegram bot shell, and n8n webhook smoke checks.
- Create: `docs/operations/deployment-runbook.md` for the concrete Dokploy/VPS deployment procedure.
- Create: `docs/operations/backup-restore.md` for backup, restore, retention, and verification steps.
- Create: `docs/operations/smoke-tests.md` for manual and scripted smoke-test instructions.
- Create: `docs/operations/n8n-workflows.md` for request/status workflow design records.
- Modify: `docs/operations/deployment-runbook-outline.md` to point to the concrete runbook.
- Modify: `docs/harness/repository-map.md` to list Phase 10 operations artifacts.
- Modify: `tools/repo-checks/check_docs.py` to require the new Phase 10 plan and operations files.
- Modify: `docs/execution-plans/index.md` after implementation to mark Phase 10 completed and the next focus as backlog grooming or the next approved phase.
- Modify: `project_notes.md` after implementation to record Phase 10 completion, artifacts, verification, and next active focus.
- Create: `docs/review/phase-10-review.md` after verification and independent review.

## Task 1: Production Compose And Environment Contract

**Files:**
- Create: `docker-compose.production.yml`
- Modify: `.env.example`
- Modify: `tools/repo-checks/check_docs.py`

- [ ] **Step 1: Add failing docs-harness expectations**

Extend `tools/repo-checks/check_docs.py` so `REQUIRED_FILES` includes:

```python
"docs/execution-plans/detailed/10-deployment-and-operations-implementation.md",
"docker-compose.production.yml",
"docs/operations/deployment-runbook.md",
"docs/operations/backup-restore.md",
"docs/operations/smoke-tests.md",
"docs/operations/n8n-workflows.md",
"tools/operations/postgres_backup.sh",
"tools/operations/postgres_restore.sh",
"tools/operations/smoke_test.sh",
```

Add `require_text` checks for:

```python
require_text("docker-compose.production.yml", "n8n:")
require_text("docker-compose.production.yml", "pgvector/pgvector:pg16")
require_text("docker-compose.production.yml", "SERVICEOPS_STAFF_AUTH_SECRET")
require_text(".env.example", "SERVICEOPS_PUBLIC_API_BASE_URL")
require_text(".env.example", "N8N_WEBHOOK_URL")
require_text(".env.example", "SERVICEOPS_BACKUP_DIR")
```

Run: `python3 tools/repo-checks/check_docs.py`

Expected: fails because the production Compose and operations files do not exist yet.

- [ ] **Step 2: Create production Compose file**

Create `docker-compose.production.yml` with services:

- `api`: builds `./apps/api`, sets `SERVICEOPS_ENVIRONMENT=production`, PostgreSQL URL, Redis URL, CORS origins, staff auth secret, AI/RAG settings, and healthcheck against `http://127.0.0.1:8000/health`.
- `web`: builds `./apps/web` with `VITE_SERVICEOPS_API_BASE_URL=${SERVICEOPS_PUBLIC_API_BASE_URL}`, exposes port `80`, and depends on healthy API.
- `worker`: builds `./apps/worker`, uses Redis broker/backend and PostgreSQL URL, and depends on Redis and PostgreSQL health.
- `telegram-bot`: builds `./apps/telegram-bot`, uses `SERVICEOPS_TELEGRAM_BOT_TOKEN`, and runs under the `integrations` profile.
- `postgres`: uses `pgvector/pgvector:pg16`, stores data in a named volume, has `pg_isready` healthcheck, and does not publish a host port.
- `redis`: uses `redis:7-alpine`, has `redis-cli ping` healthcheck, and does not publish a host port.
- `n8n`: uses a pinned `n8nio/n8n` image, depends on PostgreSQL and Redis health, stores data in a named volume, exposes port `5678`, and receives the documented n8n environment variables.

Do not change the existing local `docker-compose.yml` port bindings.

- [ ] **Step 3: Expand environment template**

Update `.env.example` into grouped sections for local defaults and production-required values. Include these variables with placeholder guidance:

```text
SERVICEOPS_ENVIRONMENT=local
SERVICEOPS_PUBLIC_WEB_BASE_URL=http://localhost:3000
SERVICEOPS_PUBLIC_API_BASE_URL=http://localhost:8000
SERVICEOPS_CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
SERVICEOPS_STAFF_AUTH_SECRET=local-dev-staff-auth-secret-change-me
SERVICEOPS_DATABASE_URL=postgresql+psycopg://serviceops:serviceops@postgres:5432/serviceops
SERVICEOPS_REDIS_URL=redis://redis:6379/0
SERVICEOPS_REDIS_BROKER_URL=redis://redis:6379/0
SERVICEOPS_REDIS_RESULT_BACKEND=redis://redis:6379/1
SERVICEOPS_TELEGRAM_BOT_TOKEN=
N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_WEBHOOK_URL=http://localhost:5678/
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=serviceops-admin
N8N_BASIC_AUTH_PASSWORD=change-me
SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET=change-me
SERVICEOPS_BACKUP_DIR=./backups
SERVICEOPS_BACKUP_RETENTION_DAYS=14
```

Keep existing local variables needed by Compose and tests.

- [ ] **Step 4: Verify Compose config**

Run: `docker compose -f docker-compose.production.yml config`

Expected: exits successfully and the rendered config contains `api`, `web`, `worker`, `telegram-bot`, `postgres`, `redis`, and `n8n`.

Run: `python3 tools/repo-checks/check_docs.py`

Expected: still fails until the remaining operations files are added in later tasks.

## Task 2: Structured Logging

**Files:**
- Create: `apps/api/src/serviceops_api/observability.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Create: `apps/api/tests/test_observability.py`
- Create: `apps/worker/src/serviceops_worker/observability.py`
- Modify: `apps/worker/src/serviceops_worker/celery_app.py`
- Create: `apps/worker/tests/test_observability.py`
- Create: `apps/telegram-bot/src/serviceops_telegram_bot/observability.py`
- Modify: `apps/telegram-bot/src/serviceops_telegram_bot/main.py`
- Create: `apps/telegram-bot/tests/test_observability.py`

- [ ] **Step 1: Write failing API logging tests**

Create `apps/api/tests/test_observability.py` with tests that:

- instantiate `JsonLogFormatter(service_name="serviceops-api", environment="test")`;
- format a `logging.LogRecord`;
- parse the output with `json.loads`;
- assert keys `timestamp`, `level`, `logger`, `message`, `service`, and `environment`;
- monkeypatch `serviceops_api.main.configure_logging` and assert `create_app()` calls it.

Run: `cd apps/api && uv run --extra dev pytest tests/test_observability.py -q`

Expected: fails because `serviceops_api.observability` does not exist.

- [ ] **Step 2: Implement API logging**

Create `apps/api/src/serviceops_api/observability.py` with:

- `JsonLogFormatter(logging.Formatter)` that emits one JSON object per log line;
- `configure_logging(service_name: str, environment: str) -> None` that configures the root logger with the formatter on stdout;
- idempotent setup so repeated `create_app()` calls in tests do not add duplicate handlers.

Modify `apps/api/src/serviceops_api/main.py` to call:

```python
configure_logging(settings.service_name, settings.environment)
```

after `settings = get_settings()`.

- [ ] **Step 3: Add worker logging tests and implementation**

Create `apps/worker/tests/test_observability.py` with the same formatter assertions for `service_name="serviceops-worker"`. Also assert `create_celery_app()` calls `configure_logging`.

Create `apps/worker/src/serviceops_worker/observability.py` with the same JSON formatter shape. Modify `apps/worker/src/serviceops_worker/celery_app.py` to call:

```python
configure_logging(
    service_name=os.getenv("SERVICEOPS_SERVICE_NAME", "serviceops-worker"),
    environment=os.getenv("SERVICEOPS_ENVIRONMENT", "local"),
)
```

before creating the Celery app.

- [ ] **Step 4: Add Telegram bot logging tests and implementation**

Create `apps/telegram-bot/tests/test_observability.py` with the same formatter assertions for `service_name="serviceops-telegram-bot"`. Also assert `run_bot()` configures logging when the token is empty and exits without polling.

Create `apps/telegram-bot/src/serviceops_telegram_bot/observability.py` with the same JSON formatter shape. Modify `apps/telegram-bot/src/serviceops_telegram_bot/main.py` to call:

```python
configure_logging(
    service_name="serviceops-telegram-bot",
    environment=resolved_settings.environment,
)
```

before checking whether the token is configured.

- [ ] **Step 5: Verify logging tests**

Run:

```bash
cd apps/api && uv run --extra dev pytest tests/test_observability.py -q
cd apps/worker && uv run --extra dev pytest tests/test_observability.py -q
cd apps/telegram-bot && uv run --extra dev pytest tests/test_observability.py -q
```

Expected: all pass and log formatting is deterministic JSON.

## Task 3: Migration Command And Backup Scripts

**Files:**
- Create: `apps/api/src/serviceops_api/operations/__init__.py`
- Create: `apps/api/src/serviceops_api/operations/migrate.py`
- Create: `apps/api/tests/test_operations_migrate.py`
- Create: `tools/operations/postgres_backup.sh`
- Create: `tools/operations/postgres_restore.sh`

- [ ] **Step 1: Write failing migration command tests**

Create `apps/api/tests/test_operations_migrate.py` with tests that:

- monkeypatch `SERVICEOPS_DATABASE_URL` to `sqlite:///:memory:` and assert `run_migrations()` raises `RuntimeError("Production migrations require PostgreSQL")`;
- monkeypatch repository factory functions and assert a PostgreSQL URL initializes service-request, knowledge-base, AI suggestion, inventory, and staff repositories with `initialize=True`.

Run: `cd apps/api && uv run --extra dev pytest tests/test_operations_migrate.py -q`

Expected: fails because `serviceops_api.operations.migrate` does not exist.

- [ ] **Step 2: Implement migration command**

Create `apps/api/src/serviceops_api/operations/migrate.py` with:

- `run_migrations(settings: Settings | None = None) -> dict[str, str]`;
- validation that `settings.database_url` starts with `postgresql://` or `postgresql+psycopg://`;
- calls to `create_service_request_repository(settings, initialize=True)`, `create_knowledge_base_repository(settings, initialize=True)`, `create_ai_suggestion_repository(settings, initialize=True)`, `create_inventory_repository(settings, initialize=True)`, and `create_staff_account_repository(settings, initialize=True)`;
- `main()` that prints JSON `{"status": "ok", "database": "postgres"}`.

Add `apps/api/src/serviceops_api/operations/__init__.py` exporting `run_migrations`.

- [ ] **Step 3: Add backup script**

Create executable `tools/operations/postgres_backup.sh` that:

- reads `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, and `SERVICEOPS_BACKUP_DIR`;
- creates the backup directory;
- writes a timestamped custom-format dump named `serviceops-YYYYmmdd-HHMMSS.dump`;
- writes a `.sha256` checksum file;
- prints the backup path.

Use `pg_dump --format=custom --no-owner --no-acl`.

- [ ] **Step 4: Add restore script**

Create executable `tools/operations/postgres_restore.sh` that:

- accepts one positional backup path;
- verifies the file exists;
- reads the same PostgreSQL environment variables;
- runs `pg_restore --clean --if-exists --no-owner --no-acl --dbname=...`;
- prints the restored backup path.

- [ ] **Step 5: Verify migration and scripts**

Run:

```bash
cd apps/api && uv run --extra dev pytest tests/test_operations_migrate.py -q
bash -n tools/operations/postgres_backup.sh
bash -n tools/operations/postgres_restore.sh
```

Expected: pytest passes and shell syntax checks pass.

## Task 4: Operations Documentation

**Files:**
- Create: `docs/operations/deployment-runbook.md`
- Create: `docs/operations/backup-restore.md`
- Create: `docs/operations/smoke-tests.md`
- Create: `docs/operations/n8n-workflows.md`
- Modify: `docs/operations/deployment-runbook-outline.md`
- Modify: `docs/harness/repository-map.md`

- [ ] **Step 1: Create concrete deployment runbook**

Create `docs/operations/deployment-runbook.md` with sections:

- Preconditions: VPS with Docker/Dokploy, DNS, HTTPS routing, repository access, production secrets, and backup directory.
- Services: API, web, worker, Telegram bot, PostgreSQL, Redis, and n8n.
- Secret setup: required `.env` values and instruction to replace local defaults before public exposure.
- Dokploy setup: create Compose app from `docker-compose.production.yml`, configure domains for web/API/n8n, configure persistent volumes.
- Migration command: `docker compose -f docker-compose.production.yml run --rm api python -m serviceops_api.operations.migrate`.
- Startup order: PostgreSQL, Redis, API, web, worker, n8n, then optional Telegram bot profile.
- Healthchecks: API `/health`, web root, n8n UI, worker logs, Telegram bot disabled/enabled log.
- Rollback: redeploy previous image/config, keep database backups, do not delete volumes during rollback.
- Production staff accounts: create persisted admin first, then dispatcher/technician/inventory users; do not rely on dev seed users.

- [ ] **Step 2: Create backup and restore documentation**

Create `docs/operations/backup-restore.md` with:

- backup frequency recommendation for MVP operations;
- command for host-side backup through Compose;
- command for direct container execution if `pg_dump` is available only in the PostgreSQL container;
- restore command using `tools/operations/postgres_restore.sh`;
- checksum verification with `sha256sum -c`;
- restore drill checklist on a non-production database;
- retention note using `SERVICEOPS_BACKUP_RETENTION_DAYS`.

- [ ] **Step 3: Create smoke-test documentation**

Create `docs/operations/smoke-tests.md` covering:

- `docker compose -f docker-compose.production.yml config`;
- API health request;
- web root request;
- public request intake POST;
- public status page/API lookup;
- staff login and protected dispatcher route check;
- worker startup and Celery inspect command;
- Telegram bot shell with empty token and optional enabled profile check;
- n8n webhook path check against a test workflow;
- backup command dry run or non-production backup.

- [ ] **Step 4: Create n8n workflow design records**

Create `docs/operations/n8n-workflows.md` with design records for:

- New request dispatcher alert.
- Status changed customer notification.
- Awaiting clarification reminder.
- Daily operations summary.

For each record include trigger, input fields, n8n steps, output, retry behavior, and whether there is a backend callback. State that n8n does not own service-request state.

- [ ] **Step 5: Update outline and repository map**

Update `docs/operations/deployment-runbook-outline.md` so it points to `docs/operations/deployment-runbook.md`, `docs/operations/backup-restore.md`, `docs/operations/smoke-tests.md`, and `docs/operations/n8n-workflows.md`.

Update `docs/harness/repository-map.md` to list:

- `docker-compose.production.yml`;
- `docs/operations/deployment-runbook.md`;
- `docs/operations/backup-restore.md`;
- `docs/operations/smoke-tests.md`;
- `docs/operations/n8n-workflows.md`;
- `tools/operations/`.

## Task 5: Scripted Smoke Checks

**Files:**
- Create: `tools/operations/smoke_test.sh`
- Modify: `docs/operations/smoke-tests.md`

- [ ] **Step 1: Create smoke script**

Create executable `tools/operations/smoke_test.sh` that:

- reads `SERVICEOPS_PUBLIC_API_BASE_URL`, `SERVICEOPS_PUBLIC_WEB_BASE_URL`, and optional `N8N_TEST_WEBHOOK_URL`;
- fails fast with clear messages;
- checks `GET /health`;
- checks the web root URL returns a successful HTTP status;
- posts a minimal service request to `/service-requests`;
- extracts `request_number` and `public_token` with Python from the JSON response;
- checks `GET /service-requests/{request_number}/status`;
- checks `GET /status/{public_token}`;
- prints manual follow-up checks for worker, Telegram bot, and n8n when a webhook URL is not configured;
- posts to `N8N_TEST_WEBHOOK_URL` when configured.

Keep the script dependency-light: `bash`, `curl`, and `python3`.

- [ ] **Step 2: Document script usage**

Update `docs/operations/smoke-tests.md` with:

```bash
SERVICEOPS_PUBLIC_API_BASE_URL=https://api.example.com \
SERVICEOPS_PUBLIC_WEB_BASE_URL=https://app.example.com \
N8N_TEST_WEBHOOK_URL=https://n8n.example.com/webhook/serviceops-smoke \
tools/operations/smoke_test.sh
```

- [ ] **Step 3: Verify script syntax**

Run: `bash -n tools/operations/smoke_test.sh`

Expected: exits successfully.

## Task 6: Phase Completion Docs And Verification

**Files:**
- Modify: `project_notes.md`
- Modify: `docs/execution-plans/index.md`
- Modify: `docs/harness/repository-map.md`
- Modify: `tools/repo-checks/check_docs.py`
- Create: `docs/review/phase-10-review.md`

- [ ] **Step 1: Update phase index**

Update `docs/execution-plans/index.md`:

- Active Phase becomes backlog grooming or the next user-approved phase.
- Completed detailed plans includes `detailed/10-deployment-and-operations-implementation.md`.
- Phase sequence keeps Phase 10 as completed in the narrative.

- [ ] **Step 2: Update project notes**

Update `project_notes.md`:

- Current Status includes Phase 10 deployment and operations artifacts.
- Latest Changes records the implementation date and major artifacts.
- Active Focus becomes backlog grooming or the next user-approved phase.
- Next Steps point to running deployment smoke checks against a real Dokploy environment and selecting the next approved slice.
- Active Artifacts includes the Phase 10 detailed plan and `docs/review/phase-10-review.md`.
- Recent Decisions records production exposure, backups, structured logging, and n8n ownership boundaries.

- [ ] **Step 3: Add review artifact shell**

Create `docs/review/phase-10-review.md` after implementation verification with:

- reviewer role;
- files reviewed;
- verification commands and outputs;
- blocking issues;
- non-blocking issues;
- suggested follow-up slice;
- final recommendation.

The review must follow `docs/review/subagent-review-protocol.md`.

- [ ] **Step 4: Run full local verification**

Run:

```bash
python3 tools/repo-checks/check_docs.py
cd apps/api && uv run --extra dev pytest
cd apps/worker && uv run --extra dev pytest
cd apps/telegram-bot && uv run --extra dev pytest
npm run web:test
npm run web:lint
npm run web:build
docker compose -f docker-compose.production.yml config
bash -n tools/operations/postgres_backup.sh
bash -n tools/operations/postgres_restore.sh
bash -n tools/operations/smoke_test.sh
```

Expected: all commands pass before requesting review.

- [ ] **Step 5: Request independent review**

Ask an independent reviewer or subagent to review:

- active phase slice: `docs/execution-plans/phases/10-deployment-and-operations.md`;
- this detailed plan;
- changed-file list or diff;
- verification output;
- deployability, secret handling, operational clarity, runbook specificity, and n8n state boundaries.

Store the result in `docs/review/phase-10-review.md` and resolve blocking issues before marking Phase 10 complete.

## Self-Review Notes

- Phase 10 deliverables are covered: production Compose/Dokploy definitions, environment documentation, backup/restore, structured logging, n8n workflows, deployment runbook, and smoke tests.
- Secret handling is explicit: local defaults remain for development, production runbook requires replacement before exposure.
- Public deployment boundaries are explicit: PostgreSQL and Redis stay private, staff workspaces remain unlinked from public navigation, and n8n does not own business state.
- The plan intentionally avoids commit and push steps because project policy requires a direct user instruction in the current conversation turn.
