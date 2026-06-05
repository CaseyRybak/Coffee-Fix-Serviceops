---
name: dokploy-deployment
description: Use when preparing CoffeeFix Pro for VPS deployment, Docker Compose production config, Dokploy apps, environment variables, backups, or smoke tests.
---

# Dokploy Deployment

## Context To Open

- `docs/architecture/tech-stack.md`
- Phase 08 plan.
- `project_notes.md`

## Pattern

Deployment should be reproducible by a fresh contributor. Keep runtime services explicit: API, web, worker, telegram bot, PostgreSQL, Redis, and n8n.

## Deployment Docs Should Include

- Required environment variables.
- Service start order.
- Healthchecks.
- Migration command.
- Backup and restore commands.
- Smoke test checklist.
- Where logs are available.

## Smoke Test Areas

- API health.
- Public web page.
- Request intake.
- Status page.
- Worker startup.
- Telegram bot startup.
- n8n webhook path.
