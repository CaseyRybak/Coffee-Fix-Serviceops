# Operational Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen production diagnosability, auditability, backup confidence, and incident response without changing customer-facing repair workflows.

**Architecture:** Keep operational hardening inside existing boundaries: shared JSON logging helpers stay in each runtime unless a small shared package removes duplication cleanly, service-request and notification use cases emit safe operational events, staff-management audit storage remains the durable audit source for staff-sensitive actions, and operations docs/scripts define recovery procedures. Logs and audit records must carry correlation fields, actor/action/target/outcome metadata, and no reusable secrets, raw AI prompts, provider bodies, passwords, tokens, or private customer contact values.

**Tech Stack:** FastAPI, Pydantic models, sqlite/PostgreSQL repositories, stdlib logging, pytest/httpx, Celery, aiogram, Docker Compose, shell backup/restore scripts, Dokploy service logs.

---

## File Structure

- Modify `apps/api/src/serviceops_api/observability.py`: add safe structured context support, redaction helpers, and stable operational field names.
- Modify `apps/api/tests/test_observability.py`: cover structured context fields, redaction, exception formatting, and formatter reuse.
- Modify `apps/worker/src/serviceops_worker/observability.py` and `apps/worker/tests/test_observability.py`: keep worker formatter behavior aligned with API logging.
- Modify `apps/telegram-bot/src/serviceops_telegram_bot/observability.py` and `apps/telegram-bot/tests/test_observability.py`: keep bot formatter behavior aligned with API logging.
- Modify `apps/api/src/serviceops_api/service_requests/use_cases.py`: log request intake, dispatcher status changes, assignment, clarification, customer answer, and internal-note write outcomes with request correlation fields.
- Modify `apps/api/src/serviceops_api/notifications/use_cases.py`: log notification event creation, n8n delivery result, callback result, and duplicate event suppression.
- Modify `apps/api/src/serviceops_api/ai_agents/use_cases.py`: log AI suggestion lifecycle outcomes without raw prompts, provider response bodies, or source chunk content.
- Modify `apps/worker/src/serviceops_worker/knowledge_base_tasks.py`: log embedding task start, success, failure, document id, provider mode, and duration without document body text.
- Modify `apps/telegram-bot/src/serviceops_telegram_bot/main.py` and `apps/telegram-bot/src/serviceops_telegram_bot/serviceops_client.py`: log opt-in token consumption outcomes without token values or chat ids.
- Modify `apps/api/src/serviceops_api/staff_auth.py`: add audit and log hooks for staff login success, login failure, token validation failure, and forbidden role checks.
- Modify `apps/api/src/serviceops_api/staff_management/repository.py`: ensure audit metadata can store `outcome`, `reason`, `request_number`, `role`, and `source` fields for sensitive staff actions.
- Modify `apps/api/tests/test_staff_auth.py` and `apps/api/tests/test_staff_management.py`: cover new staff-auth audit records and sensitive-field exclusion.
- Modify `apps/api/tests/test_notification_automation.py`, `apps/api/tests/test_dispatcher_requests.py`, and `apps/api/tests/test_ai_agent_suggestions.py`: cover logging/audit contracts in the workflows that are easiest to regress.
- Create `docs/operations/incident-response.md`: first-line incident checklist for API, web, PostgreSQL, Redis, worker, Telegram bot, n8n, notifications, and AI/RAG provider degradation.
- Modify `docs/operations/backup-restore.md`: add a production-safe restore dry-run procedure with evidence fields and abort conditions.
- Modify `docs/operations/smoke-tests.md`: reference restore-dry-run evidence and log-query checks.
- Modify `docs/operations/deployment-runbook.md`: link operational dashboard/log queries, incident checklist, and restore dry-run.
- Create `docs/operations/operational-diagnostics.md`: documented log queries and first-line dashboard checklist for tracing a request across intake, staff action, notification attempt, and status update.
- Modify `docs/operations/launch-smoke-evidence.md`: add backup dry-run and log trace evidence sections.
- Modify `tools/repo-checks/check_docs.py`: require new Phase 14 operational docs.
- Modify `docs/harness/repository-map.md`, `docs/execution-plans/index.md`, and `project_notes.md`: update current documentation pointers after Phase 14 implementation.
- Create `docs/review/phase-14-review.md` after local verification and independent review are available.

## Operational Field Contract

Use these field names consistently in structured logs and audit metadata:

- `request_number`: public request number such as `CFX-20260615-000001`.
- `event_id`: notification event id shaped as `<request_number>:<event_type>:<sequence>`.
- `event_type`: domain event such as `service_request.created`.
- `actor_username`: staff username for authenticated staff actions.
- `action`: stable action name such as `staff.login_succeeded`, `dispatcher.status_updated`, or `notification.delivery_recorded`.
- `target`: affected request number, staff username, event id, document id, or service name.
- `outcome`: `succeeded`, `failed`, `blocked`, `skipped`, or `retried`.
- `reason`: short operator-safe failure reason, never a password, token, provider body, raw prompt, or customer phone.
- `duration_ms`: integer elapsed time when practical.
- `provider`: `deterministic`, `openai-compatible`, `n8n`, `telegram`, or `postgres` when relevant.

Never place these values in logs or audit metadata:

- Passwords, password hashes, staff auth tokens, Telegram opt-in tokens, webhook shared secrets, callback secrets, provider API keys, raw provider request/response bodies, raw AI prompts, full internal note bodies, customer phone numbers, Telegram chat ids, or unrestricted source chunk text.

## Task 1: Structured Logging Contract And Redaction

- [ ] Add failing tests in `apps/api/tests/test_observability.py` for `JsonLogFormatter` with `extra={"serviceops_context": {...}}`.
- [ ] Assert the JSON payload includes `request_number`, `actor_username`, `action`, `target`, `outcome`, `reason`, `duration_ms`, and `provider` when supplied.
- [ ] Assert redaction replaces unsafe keys named `password`, `password_hash`, `access_token`, `token`, `telegram_chat_id`, `SERVICEOPS_STAFF_AUTH_SECRET`, `SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET`, `SERVICEOPS_N8N_CALLBACK_SECRET`, `SERVICEOPS_AI_API_KEY`, and `SERVICEOPS_EMBEDDING_API_KEY` with `[redacted]`.
- [ ] Implement a small helper in `apps/api/src/serviceops_api/observability.py`:

```python
SAFE_CONTEXT_KEYS = {
    "request_number",
    "event_id",
    "event_type",
    "actor_username",
    "action",
    "target",
    "outcome",
    "reason",
    "duration_ms",
    "provider",
}

SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "telegram_chat_id",
)
```

- [ ] Copy the same helper shape to worker and Telegram bot observability modules unless a small package import from `packages/observability` is introduced in the same task.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_observability.py -v`
  - `cd apps/worker && uv run --extra dev pytest tests/test_observability.py -v`
  - `cd apps/telegram-bot && uv run --extra dev pytest tests/test_observability.py -v`
- [ ] Expected: formatter tests pass and logs remain valid single-line JSON.

## Task 2: Request, Dispatcher, Notification, And AI Workflow Logs

- [ ] Add tests that use `caplog` around `CreateServiceRequest.execute()` and assert an intake success log includes `action=service_request.created`, `request_number`, and `outcome=succeeded`.
- [ ] Add dispatcher tests for `UpdateDispatcherStatus`, `AskDispatcherClarification`, `AssignDispatcherTechnician`, and `SaveDispatcherInternalNote` proving logs include `request_number`, `actor_username` when available, action, and outcome.
- [ ] Add notification tests proving `NotificationPublisher._publish()` logs queued, delivered, failed, and duplicate-suppressed outcomes with `event_id`, `event_type`, `request_number`, and `provider=n8n`.
- [ ] Add AI suggestion tests proving generation logs provider mode, request number, suggestion count, and outcome without prompt text, source content, provider response body, or customer contact values.
- [ ] Implement logging inside use cases after successful persistence or after caught provider/delivery outcomes. Do not log before persistence for events that may fail.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_service_request_intake.py tests/test_dispatcher_requests.py tests/test_notification_automation.py tests/test_ai_agent_suggestions.py -v`
- [ ] Expected: workflow log tests pass and existing public/private response boundaries stay unchanged.

## Task 3: Worker And Telegram Bot Operational Logs

- [ ] Add worker tests around knowledge-base embedding tasks proving logs include provider mode, document id or source URI, outcome, and duration.
- [ ] Add Telegram bot tests proving opt-in link success, expired/invalid token failure, and API client failure are logged with `outcome` and `reason` but without opt-in token, Telegram chat id, bot token, or full customer contact values.
- [ ] Implement logs in `apps/worker/src/serviceops_worker/knowledge_base_tasks.py`, `apps/telegram-bot/src/serviceops_telegram_bot/main.py`, and `apps/telegram-bot/src/serviceops_telegram_bot/serviceops_client.py`.
- [ ] Run:
  - `cd apps/worker && uv run --extra dev pytest -v`
  - `cd apps/telegram-bot && uv run --extra dev pytest -v`
- [ ] Expected: runtime-specific tests pass without network access.

## Task 4: Sensitive Staff Action Audit Expansion

- [ ] Extend `apps/api/tests/test_staff_auth.py` with persisted account login scenarios:
  - successful login records `staff.login_succeeded`;
  - wrong password records `staff.login_failed`;
  - inactive account records `staff.login_failed` with `reason=inactive`;
  - token verification after deactivation records `staff.token_rejected`.
- [ ] Extend admin tests proving forbidden role access records an audit event with actor, action, target route or role, timestamp, outcome, and operator-safe reason.
- [ ] Add an optional audit recorder dependency to `StaffAuthenticator` or `create_staff_auth_router()` using the existing staff-management repository protocol.
- [ ] Store sensitive-auth audit records through `record_audit_event(actor, target, action, metadata)`.
- [ ] Keep audit metadata free of passwords, hashes, bearer tokens, opt-in tokens, and shared secrets.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_staff_auth.py tests/test_staff_management.py -v`
- [ ] Expected: staff-management audit behavior still protects the last active admin and new auth audit records are durable.

## Task 5: Operational Diagnostics Documentation

- [ ] Create `docs/operations/operational-diagnostics.md` with:
  - fields required to trace one request from intake through dispatcher action, notification event, n8n callback, and public status update;
  - Dokploy/Docker log commands for `api`, `worker`, `telegram-bot`, and `n8n`;
  - `jq` examples for filtering by `request_number`, `event_id`, `action`, and `outcome`;
  - PostgreSQL read-only queries for notification delivery attempts and staff audit events;
  - redaction rules for evidence copied into tickets or launch notes.
- [ ] Update `docs/operations/deployment-runbook.md` and `docs/operations/smoke-tests.md` to link this diagnostics guide.
- [ ] Run:
  - `python3 tools/repo-checks/check_docs.py`
- [ ] Expected: documentation harness passes.

## Task 6: Restore Dry-Run Procedure And Evidence

- [ ] Expand `docs/operations/backup-restore.md` with a restore dry-run that never targets production data:
  - create a temporary PostgreSQL database or disposable Compose project;
  - verify checksum before restore;
  - restore the latest backup with `tools/operations/postgres_restore.sh`;
  - run migrations against the restored target;
  - run smoke checks against the restored stack;
  - record backup timestamp, checksum status, restore duration, migration result, smoke result, and operator.
- [ ] Add abort conditions:
  - target host or database name equals production;
  - checksum fails;
  - backup age is outside the approved recovery window;
  - restore command would use production `SERVICEOPS_DATABASE_URL`.
- [ ] Update `docs/operations/launch-smoke-evidence.md` with a restore dry-run evidence section.
- [ ] Run:
  - `bash -n tools/operations/postgres_backup.sh`
  - `bash -n tools/operations/postgres_restore.sh`
  - `python3 tools/operations/test_smoke_script_contract.py`
- [ ] Expected: scripts parse and the smoke script contract still passes.

## Task 7: Incident Checklist

- [ ] Create `docs/operations/incident-response.md` with sections for:
  - degraded API;
  - degraded web;
  - PostgreSQL unavailable or slow;
  - Redis or worker failure;
  - Telegram bot failure;
  - n8n webhook/callback failure;
  - AI or embedding provider degradation;
  - notification delivery backlog;
  - suspected secret exposure;
  - restore-from-backup decision.
- [ ] Each section must include first checks, customer impact, containment, rollback criteria, restore criteria, owner handoff, and evidence to capture.
- [ ] Link the checklist from `docs/operations/deployment-runbook.md`, `docs/operations/smoke-tests.md`, and `project_notes.md`.
- [ ] Run:
  - `python3 tools/repo-checks/check_docs.py`
- [ ] Expected: docs pass and operators have one incident entry point.

## Task 8: Repository Checks And Phase Handoff

- [ ] Update `tools/repo-checks/check_docs.py` to require:
  - `docs/execution-plans/detailed/14-operational-hardening-implementation.md`;
  - `docs/operations/operational-diagnostics.md`;
  - `docs/operations/incident-response.md`;
  - `docs/review/phase-14-review.md` only after the review artifact exists.
- [ ] After implementation and independent review, update `project_notes.md` current status to include completed Phase 14 operational hardening.
- [ ] After implementation and independent review, update `project_notes.md` active focus to Phase 15 scheduling depth.
- [ ] After implementation and independent review, update `docs/execution-plans/index.md` active phase to `phases/15-scheduling-depth.md`.
- [ ] Create `docs/review/phase-14-review.md` with reviewer role, files reviewed, verification commands, blocking issues, non-blocking issues, follow-up slice, documentation updates, and final recommendation.
- [ ] Run the full verification list below before requesting review.

## Verification

- [ ] `python3 tools/repo-checks/check_docs.py`
- [ ] `cd apps/api && uv run --extra dev pytest tests/test_observability.py tests/test_staff_auth.py tests/test_staff_management.py tests/test_service_request_intake.py tests/test_dispatcher_requests.py tests/test_notification_automation.py tests/test_ai_agent_suggestions.py -v`
- [ ] `cd apps/api && uv run --extra dev pytest`
- [ ] `cd apps/worker && uv run --extra dev pytest`
- [ ] `cd apps/telegram-bot && uv run --extra dev pytest`
- [ ] `npm run web:test`
- [ ] `npm run web:lint`
- [ ] `npm run web:build`
- [ ] `docker compose -f docker-compose.production.yml --env-file .env.example config`
- [ ] `bash -n tools/operations/postgres_backup.sh`
- [ ] `bash -n tools/operations/postgres_restore.sh`
- [ ] `bash -n tools/operations/smoke_test.sh`
- [ ] `python3 tools/operations/test_smoke_script_contract.py`
- [ ] Secret scan before review:
  - `rg -n "sk-|SERVICEOPS_[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|API_KEY)=.+[A-Za-z0-9_-]{16,}" . --glob '!apps/**/.venv/**' --glob '!node_modules/**' --glob '!reference/figma/node_modules/**'`
  - Expected: no real reusable secrets in tracked files.

## Subagent Review Gate

Ask the reviewer to inspect:

- Operators can trace a customer request from intake through staff action, notification event, delivery callback, and public status update using only safe structured logs and read-only queries.
- Audit records for sensitive staff auth/admin actions include actor, action, target, timestamp, outcome, and reason where available.
- Logs and audit metadata do not expose passwords, hashes, bearer tokens, Telegram opt-in tokens, webhook secrets, API keys, raw AI prompts, provider bodies, customer phone numbers, Telegram chat ids, internal note bodies, or unrestricted source chunk text.
- Restore dry-run instructions cannot be mistaken for a production destructive restore path.
- Incident steps are actionable under pressure and identify first checks, containment, rollback, restore criteria, owner handoff, and evidence capture.
- Phase 14 does not expand scheduling, inventory reservations, billing, or autonomous AI decisions beyond the active slice.

## Self-Review

- Phase 14 deliverables are covered by Tasks 1-8.
- The plan keeps operational hardening bounded to observability, auditability, recovery checks, incident procedures, diagnostics docs, verification, and handoff.
- Logging and audit changes use existing domain/application boundaries rather than introducing a new observability platform.
- The plan avoids changing public status response content except where smoke or docs verify existing privacy boundaries.
- The plan leaves Phase 15 scheduling depth and Phase 16 inventory reservations untouched.
