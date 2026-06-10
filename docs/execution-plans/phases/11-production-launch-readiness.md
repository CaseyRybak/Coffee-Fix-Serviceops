# Phase 11: Production Launch Readiness

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Close the remaining launch blockers before the first public production deployment.

## Context To Read

- `docs/architecture/tech-stack.md`
- `docs/architecture/harness-engineering.md`
- `docs/operations/deployment-runbook.md`
- `docs/execution-plans/phases/10-deployment-and-operations.md`
- `docs/review/phase-10-review.md`

## Deliverables

- Production-safe first-admin bootstrap command or controlled database runbook step.
- Documented first-launch checklist for Dokploy/VPS.
- Real-environment smoke-check procedure for web, API, worker, Telegram bot shell, PostgreSQL, Redis, and n8n.
- Verification notes template for recording launch smoke-test results.
- Clear rollback and restore decision points for first launch.
- Updated operations documentation for any launch-only manual steps.

## Acceptance Criteria

- Public launch no longer depends on local seed staff users.
- A fresh operator can create the first production admin without exposing reusable credentials in repository files or logs.
- Smoke checks can be run against a real Dokploy/VPS environment and produce auditable results.
- The runbook identifies required secrets, expected service health, and failure handling before DNS or public traffic is enabled.
- Tests or script checks cover any new bootstrap or smoke-test code.
- `project_notes.md` identifies Phase 12 as the next active phase after implementation.

## Subagent Review Gate

Review launch safety, secret handling, operational clarity, bootstrap repeatability, and whether the deployment evidence is specific enough to support a public go/no-go decision.
