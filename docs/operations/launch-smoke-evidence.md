# Launch Smoke Evidence

Use this record for the first public deployment and for later launch-like redeployments. Store the completed copy outside the repository if it contains environment-specific hostnames, account names, or operational notes that should not be public.

## Deployment Metadata

- Date:
- Operator:
- Environment:
- Git revision or image tag:
- Dokploy app:
- Web URL:
- API URL:
- n8n URL:

## Pre-Launch Checks

- Production environment values loaded from approved secret store:
- PostgreSQL and Redis have no public route:
- HTTPS is configured for web, API, and n8n:
- Persistent volumes configured for `postgres-data` and `n8n-data`:
- Backup directory exists and is covered by host-level retention:

## Migration Evidence

Command:

```bash
docker compose -f docker-compose.production.yml run --rm api python -m serviceops_api.operations.migrate
```

Result:

```text
record command output here
```

## First Admin Bootstrap Evidence

Command:

```bash
docker compose -f docker-compose.production.yml run --rm \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME="$SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME" \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME="$SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME" \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD="$SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD" \
  api python -m serviceops_api.operations.bootstrap_admin
```

Expected result:

```json
{"roles":["admin"],"status":"created","username":"admin@example.com"}
```

Recorded result:

```text
record command output here without password values
```

## Smoke Test Evidence

Command:

```bash
SERVICEOPS_PUBLIC_API_BASE_URL="https://api.example.com" \
SERVICEOPS_PUBLIC_WEB_BASE_URL="https://serviceops.example.com" \
SERVICEOPS_SMOKE_STAFF_USERNAME="$SERVICEOPS_SMOKE_STAFF_USERNAME" \
SERVICEOPS_SMOKE_STAFF_PASSWORD="$SERVICEOPS_SMOKE_STAFF_PASSWORD" \
N8N_TEST_WEBHOOK_URL="https://n8n.example.com/webhook/serviceops-smoke" \
tools/operations/smoke_test.sh
```

Result:

```text
record command output here without password values
```

## Service Checks

- API health returned healthy:
- Web root returned the web shell:
- Request intake created request number:
- Public status lookup by request number succeeded:
- Public status lookup by token succeeded:
- Staff login and dispatcher route succeeded:
- Worker logs reviewed:
- Telegram bot logs reviewed:
- n8n smoke webhook execution succeeded:
- Backup command or backup readiness check completed:

## Rollback Readiness

- Previous known-good image or Compose configuration identified:
- Latest verified backup identified:
- Maintenance or public-route disable procedure confirmed:
- Restore decision owner identified:

## Go/No-Go

- Decision:
- Decision maker:
- Notes:
