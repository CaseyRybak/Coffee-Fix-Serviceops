# Phase 21: Operational n8n Automation

> For implementation workers: create a detailed implementation plan before changing code or n8n workflow exports, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Extend n8n from notification delivery into operational automation for SLA risk, owner reporting, and low-stock alerts.

## Why This Phase Exists

Current n8n workflows handle request-created, status-changed, clarification-requested, and customer-answered notification paths. The original platform direction also called for SLA reminders, red alerts, daily owner reports, and low-stock alerts. These should come after Phase 20 so n8n can consume backend-owned dashboard and SLA APIs rather than recomputing business state.

## Context To Read

- `docs/execution-plans/roadmap-after-phase-16.md`
- `docs/operations/n8n-workflows.md`
- `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`
- `docs/operations/deployment-runbook.md`
- `docs/operations/smoke-tests.md`
- `docs/operations/operational-diagnostics.md`
- `domains/notifications/domain.md`
- `domains/service-requests/domain.md`
- `domains/inventory/domain.md`
- Phase 20 detailed plan and implementation artifacts when available.

## Deliverables

- Backend endpoints or scheduled-safe APIs needed by n8n for SLA reminders, red alerts, owner daily reports, and low-stock alerts.
- n8n workflow exports for SLA reminder, red alert, daily owner report, and low-stock alert.
- Delivery-result persistence or operational evidence for the new automation paths.
- Idempotency or duplicate-notification safeguards for recurring reminders.
- Telegram owner/staff alert message contracts with sanitized payloads.
- Smoke tests or local workflow simulation guidance for each workflow.
- Updated n8n workflow documentation and production environment guidance.

## Scope Boundaries

- n8n must not own service-request status, SLA state, inventory counts, staff identity, or purchase-request state.
- This phase does not implement procurement approval; that belongs to Phase 22 unless a low-stock alert only links to an existing inventory view.
- This phase does not add AI-generated owner summaries unless Phase 20 already provides a safe deterministic report payload and the live AI guidance is followed.
- Notification payloads must not expose internal notes, raw AI prompts, provider payloads, customer phone numbers, Telegram chat ids, secrets, staff audit details, or inventory internals beyond the intended staff alert.

## Acceptance Criteria

- SLA reminder workflow can identify near-deadline work and notify the intended staff channel without duplicate spam.
- Red alert workflow can identify overdue work and notify the intended owner/staff channel.
- Daily owner report workflow can send a concise operational summary from backend-owned data.
- Low-stock workflow can notify inventory/owner stakeholders from backend-owned inventory data.
- Workflow exports are committed and documented with import/publish instructions.
- Delivery attempts or smoke evidence can be inspected without exposing secrets.

## Subagent Review Gate

Review backend/n8n state ownership, recurring workflow idempotency, payload privacy, workflow importability, smoke evidence, and whether the automation remains diagnosable from repository docs.
