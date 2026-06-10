# Notification Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make notification automation operational by emitting approved ServiceOps events to n8n, recording delivery outcomes, and providing production-ready n8n workflow exports.

**Architecture:** Add a bounded `notifications` package behind service-request use cases. Service requests remain the source of lifecycle state; notifications receive public-safe event payloads, deliver them to n8n through a webhook adapter, and persist delivery attempts/results without storing shared secrets. n8n workflows perform channel delivery and report outcome callbacks without mutating repair lifecycle state.

**Tech Stack:** FastAPI, Pydantic settings/models, sqlite/PostgreSQL repositories, httpx webhook client, pytest, n8n workflow JSON exports, Docker Compose production environment variables.

---

## File Structure

- Create `apps/api/src/serviceops_api/notifications/`: notification event models, use cases, repository, n8n client, and callback API.
- Create `apps/api/tests/test_notification_automation.py`: backend tests for event payload privacy, webhook emission, idempotency, persistence, callbacks, and staff visibility.
- Modify `apps/api/src/serviceops_api/service_requests/use_cases.py`: publish notification events after successful request creation, dispatcher status changes, clarification questions, and customer answers.
- Modify `apps/api/src/serviceops_api/service_requests/models.py`: add staff-visible notification delivery status to dispatcher detail.
- Modify `apps/api/src/serviceops_api/service_requests/repository.py`: expose public-safe notification event snapshots and include delivery status in dispatcher details.
- Modify `apps/api/src/serviceops_api/main.py`: wire notification repository, publisher, and callback router.
- Modify `apps/api/src/serviceops_api/config.py`: add n8n webhook URLs, callback secret, shared secret, timeout, and enablement settings.
- Create `apps/api/src/serviceops_api/migrations/0006_notification_delivery.sql`: PostgreSQL delivery-attempt persistence.
- Create `docs/operations/n8n-workflows/service-request-created-dispatcher-alert.json`: importable workflow export.
- Create `docs/operations/n8n-workflows/service-request-status-changed-customer-notification.json`: importable workflow export.
- Create `docs/operations/n8n-workflows/service-request-clarification-customer-notification.json`: importable workflow export.
- Modify `docs/operations/n8n-workflows.md`, `docs/operations/deployment-runbook.md`, `.env.example`, `tools/repo-checks/check_docs.py`, `docs/execution-plans/index.md`, `project_notes.md`.
- Create `docs/review/phase-12-review.md` after implementation verification and independent review.

## Task 1: Notification Domain And Persistence

- [ ] Write failing tests proving delivery attempts are created with deterministic event IDs, deduplicated by event ID, and never persist webhook secrets.
- [ ] Add notification models for `service_request.created`, `service_request.status_changed`, `service_request.clarification_requested`, and `service_request.customer_answered`.
- [ ] Add sqlite and PostgreSQL delivery persistence with statuses `queued`, `sent`, `failed`, and `retried`.
- [ ] Add callback persistence for n8n delivery outcomes, keyed by `event_id`.

## Task 2: Public-Safe Event Emission

- [ ] Write failing tests for request-created, status-changed, clarification, and customer-answer events.
- [ ] Build payloads from repository snapshots that include only customer-safe fields: request number, masked phone, machine summary, public status URL/token where needed, lifecycle status, clarification question/answer metadata as allowed.
- [ ] Exclude internal notes, staff identity details, AI suggestions, audit data, inventory metadata, technician phone, and shared secrets.
- [ ] Publish only after the source lifecycle operation succeeds.

## Task 3: n8n Webhook Adapter And Callback API

- [ ] Write failing tests for shared-secret headers, timeout/error handling, production configuration requirements, and callback authentication.
- [ ] Add an httpx-based n8n webhook client with event-specific URLs and `X-ServiceOps-Webhook-Secret`.
- [ ] Add `POST /notifications/n8n/delivery-results` protected by `X-ServiceOps-Callback-Secret`.
- [ ] Persist success, failure, and retry outcome records without mutating service-request lifecycle state.

## Task 4: Staff Delivery Visibility

- [ ] Write failing tests that dispatcher detail shows delivery state relevant to the request.
- [ ] Add latest delivery attempts to `DispatcherRequestDetail.notification_deliveries`.
- [ ] Keep public status responses unchanged except for existing customer-safe lifecycle data.

## Task 5: n8n Workflows

- [ ] Create importable workflow JSON for dispatcher new-request alert.
- [ ] Create importable workflow JSON for status-change customer notification.
- [ ] Create importable workflow JSON for clarification customer notification.
- [ ] If n8n MCP API tools are available in the session, create or update these workflows in the live n8n instance and record workflow IDs in `docs/operations/n8n-workflows.md`.
- [ ] If MCP tools are unavailable, keep JSON exports and document manual import steps as the operational artifact.

## Task 6: Operations Docs And Phase Handoff

- [ ] Document required env vars in `.env.example` and deployment runbook.
- [ ] Update `docs/operations/n8n-workflows.md` with payload contracts, callback body, retry behavior, and workflow import/activation steps.
- [ ] Update repo checks to require Phase 12 artifacts.
- [ ] After verification and review, update `project_notes.md` and `docs/execution-plans/index.md` so Phase 13 is the next active phase.

## Verification

- [ ] `python3 tools/repo-checks/check_docs.py`
- [ ] `cd apps/api && uv run --extra dev pytest tests/test_notification_automation.py -v`
- [ ] `cd apps/api && uv run --extra dev pytest`
- [ ] `docker compose -f docker-compose.production.yml --env-file .env.example config`
- [ ] `npm run web:test`
- [ ] `npm run web:lint`
- [ ] `npm run web:build`

## Self-Review

- Phase 12 scope includes working backend contracts and importable n8n workflows.
- n8n does not own repair lifecycle state and cannot mutate request status through delivery callbacks.
- Public-safe payload boundaries match the service-request public status rules.
- Workflow creation in a live n8n instance is contingent on an exposed MCP/API tool in the active agent environment.
