# Phase 14: Operational Hardening

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Strengthen production operations with better observability, auditability, and recovery checks after the launch path is in place.

## Context To Read

- `docs/architecture/harness-engineering.md`
- `docs/architecture/tech-stack.md`
- `docs/operations/deployment-runbook.md`
- `docs/review/subagent-review-protocol.md`
- `docs/execution-plans/phases/10-deployment-and-operations.md`
- `docs/execution-plans/phases/11-production-launch-readiness.md`
- `docs/execution-plans/phases/13-live-ai-provider-and-knowledge-base-content.md`

## Deliverables

- Structured logging coverage for key request, staff, notification, and background-job workflows.
- Operational audit trail expansion for sensitive staff actions not already covered.
- Backup and restore dry-run procedure with evidence capture.
- Incident checklist for degraded API, web, database, worker, Telegram, and n8n paths.
- Basic operational dashboard or documented log queries for first-line diagnosis.
- Tests or static checks for new audit/logging contracts where practical.

## Acceptance Criteria

- Operators can trace a customer request from intake through staff action, notification attempt, and status update without exposing sensitive data.
- Sensitive staff actions produce durable audit records with actor, action, target, timestamp, and outcome.
- Backup and restore documentation includes a dry-run path that can be executed without harming production data.
- Incident docs identify what to check first, when to rollback, and when to restore from backup.
- Logging and audit changes do not expose passwords, tokens, webhook secrets, or internal AI prompt content.
- `project_notes.md` identifies Phase 15 as the next active phase after implementation.

## Subagent Review Gate

Review production diagnosability, audit completeness, secret redaction, restore realism, and whether incident steps are actionable under pressure.
