# Phase 12: Notification Automation

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Move notification automation beyond design records by emitting backend events to n8n and persisting delivery outcomes.

## Context To Read

- `domains/notifications/AGENTS.md`
- `domains/notifications/domain.md`
- `domains/service-requests/domain.md`
- `docs/operations/deployment-runbook.md`
- `docs/execution-plans/phases/03-client-status-and-notifications.md`
- `docs/execution-plans/phases/10-deployment-and-operations.md`

## Deliverables

- Backend-to-n8n webhook emission for approved notification events.
- Delivery-result persistence for successful, failed, and retried notification attempts.
- Notification delivery status visibility for staff-facing workflows where operationally useful.
- Idempotency or deduplication contract for webhook delivery.
- Environment documentation for n8n webhook URLs and shared secrets.
- Tests covering event emission, delivery-result persistence, retry/error handling, and customer-safe status exposure.

## Acceptance Criteria

- Customer notification events are emitted only for approved lifecycle changes and clarification flows.
- Notification payloads do not expose internal notes, AI internals, staff-only data, audit data, or inventory metadata.
- Delivery attempts are persisted with enough context to diagnose failures without storing sensitive secrets.
- n8n webhook secrets are required in production-oriented configuration and documented in `.env.example`.
- Staff can see whether a notification was delivered, failed, or queued where that affects service operations.
- `project_notes.md` identifies Phase 13 as the next active phase after implementation.

## Subagent Review Gate

Review notification privacy, webhook security, retry behavior, delivery-state consistency, and whether customer-facing messages remain aligned with public status snapshot rules.
