# Phase 21 Operational n8n Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not create commits unless the user explicitly asks for commits in the current conversation turn.

**Goal:** Add scheduled-safe n8n automation for SLA reminders, red alerts, owner daily reports, and low-stock alerts while keeping ServiceOps API as the source of truth.

**Architecture:** Add a protected operational automation API under `/notifications/n8n/operations/*` that n8n can call with the existing callback secret. The API reads Phase 20 owner dashboard/daily-report data, filters it into purpose-specific alert payloads, and records idempotency keys in notification delivery persistence so recurring workflows do not spam duplicate alerts. n8n workflow exports remain delivery/routing artifacts only; they do not calculate SLA, inventory, staff identity, or lifecycle state.

**Tech Stack:** FastAPI, Pydantic, sqlite/PostgreSQL repositories, hand-written SQL migrations, n8n JSON workflow exports, pytest, repository docs checks.

---

### Task 1: Backend Operational Automation Contracts

**Files:**
- Modify: `apps/api/src/serviceops_api/config.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/src/serviceops_api/notifications/api.py`
- Modify: `apps/api/src/serviceops_api/notifications/models.py`
- Modify: `apps/api/src/serviceops_api/notifications/use_cases.py`
- Test: `apps/api/tests/test_operational_n8n_automation.py`

- [ ] Write failing tests for `GET /notifications/n8n/operations/sla-reminders`, `/red-alerts`, `/owner-daily-report`, and `/low-stock-alerts`.
- [ ] Verify anonymous requests and wrong secrets return `401`.
- [ ] Verify returned payloads use backend-owned Phase 20 data and exclude customer phone numbers, Telegram chat ids, raw notes, secrets, staff audit details, and public inventory internals beyond intended alert fields.
- [ ] Verify repeated calls with the same idempotency window suppress duplicate alert items, while `mark_sent=false` can be used as a dry-run/smoke preview.
- [ ] Implement Pydantic response models for operational alert envelopes and alert items.
- [ ] Use existing notification delivery attempts as operational idempotency/evidence rows keyed by deterministic `operational:*` event ids.
- [ ] Add a use case that builds four alert payloads from `GetOwnerDashboard` and `GetOwnerDailyReport`.
- [ ] Register protected operational routes using `X-ServiceOps-Callback-Secret`.
- [ ] Re-run the focused pytest file and confirm it passes.

### Task 2: n8n Workflow Exports

**Files:**
- Create: `docs/operations/n8n-workflows/sla-reminder-alert.json`
- Create: `docs/operations/n8n-workflows/red-alert.json`
- Create: `docs/operations/n8n-workflows/owner-daily-report.json`
- Create: `docs/operations/n8n-workflows/low-stock-alert.json`
- Test/Inspect: JSON parsing and key workflow node contracts.

- [ ] Add repository workflow exports with Schedule Trigger, HTTP request to the operational API, Code node message formatting, Telegram send, and backend delivery-result callback.
- [ ] Use environment expressions for `SERVICEOPS_API_BASE_URL`, `SERVICEOPS_N8N_CALLBACK_SECRET`, and `SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID`.
- [ ] Keep workflow exports free of secrets, real chat ids, customer phone numbers, Telegram chat ids, and production hostnames.
- [ ] Ensure each workflow sends a concise alert/report message and skips empty item lists.
- [ ] Validate all four JSON exports parse successfully.

### Task 3: Operations, Domain Docs, And Smoke Guidance

**Files:**
- Modify: `docs/operations/n8n-workflows.md`
- Modify: `docs/operations/deployment-runbook.md`
- Modify: `docs/operations/smoke-tests.md`
- Modify: `docs/operations/operational-diagnostics.md`
- Modify: `domains/notifications/domain.md`
- Modify: `domains/service-requests/domain.md`
- Modify: `domains/inventory/domain.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-21-review.md`

- [ ] Document the four new workflows, import/publish guidance, environment requirements, and private Compose-network URLs.
- [ ] Document local smoke previews with `mark_sent=false` and expected safe payload shape.
- [ ] Document read-only diagnostic SQL for operational idempotency/evidence rows.
- [ ] Update domain boundaries to clarify Phase 21 operational automation and non-ownership by n8n.
- [ ] Update `project_notes.md` after implementation and verification to move active focus toward Phase 22.
- [ ] Create the phase review artifact with scope, files reviewed, verification commands, and final subagent-review status.

### Task 4: Verification And Review

**Files:**
- No new production files unless fixes are required by failures or reviewers.

- [ ] Run `cd apps/api && uv run --extra dev pytest tests/test_operational_n8n_automation.py tests/test_notification_automation.py tests/test_owner_dashboard.py`.
- [ ] Run `python3 tools/repo-checks/check_docs.py`.
- [ ] Run JSON validation for `docs/operations/n8n-workflows/*.json`.
- [ ] Run subagent review for plan compliance, architecture/privacy/idempotency audit, and bug finding.
- [ ] Fix blocking or important review findings.
- [ ] Re-run focused verification after fixes.
