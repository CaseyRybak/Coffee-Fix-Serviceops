# Phase 08: Deployment And Operations

> For agentic workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Prepare the system for VPS deployment with Dokploy, operational automation, backups, and basic observability.

## Context To Read

- `docs/architecture/tech-stack.md`
- `docs/architecture/harness-engineering.md`
- `domains/notifications/domain.md`

## Deliverables

- Production-oriented Docker Compose or Dokploy app definitions.
- Environment variable documentation.
- Database backup procedure.
- Basic structured logging.
- n8n workflow docs for request and status notifications.
- Deployment runbook.
- Smoke test checklist.

## Acceptance Criteria

- Deployment steps are documented and executable by a fresh agent.
- Required secrets are listed in `.env.example`.
- Backup and restore commands are documented.
- Smoke tests cover API health, public page, request intake, status page, worker, Telegram bot shell, and n8n webhook path.
- `project_notes.md` marks the next active focus as backlog grooming or the next approved phase.

## Subagent Review Gate

Review deployability, secret handling, operational clarity, and whether runbooks are specific enough for future agents.
