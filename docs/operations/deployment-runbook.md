# Deployment Runbook

## Preconditions

- VPS has Docker, Docker Compose, and Dokploy installed.
- DNS records point the web, API, and n8n hostnames to the VPS.
- HTTPS is configured in Dokploy or the reverse proxy before public exposure.
- The repository is available to Dokploy.
- Production `.env` values are set from `.env.example` with real secrets.
- A persistent backup directory exists on the host and is covered by host-level retention.
- A production-safe first-admin bootstrap command is run before public launch. The current local seed command is intentionally blocked in production.

## Services

- API: FastAPI app from `apps/api`.
- Web: static React/Vite app served by nginx from `apps/web`.
- Worker: Celery worker from `apps/worker`.
- Telegram bot: optional aiogram polling process from `apps/telegram-bot`.
- PostgreSQL: `pgvector/pgvector:pg16` with the `postgres-data` volume.
- Redis: private broker/cache service.
- n8n: operational automation UI and webhook runner with the `n8n-data` volume.

## Secret Setup

Set these values in Dokploy before exposing the app:

```bash
SERVICEOPS_ENVIRONMENT=production
SERVICEOPS_PUBLIC_WEB_BASE_URL=https://serviceops.example.com
SERVICEOPS_PUBLIC_API_BASE_URL=https://api.serviceops.example.com
SERVICEOPS_CORS_ALLOWED_ORIGINS=https://serviceops.example.com
POSTGRES_PASSWORD=<strong password>
SERVICEOPS_DATABASE_URL=postgresql+psycopg://serviceops:<strong password>@postgres:5432/serviceops
SERVICEOPS_STAFF_AUTH_SECRET=<long random value>
SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET=<long random value>
SERVICEOPS_N8N_CALLBACK_SECRET=<different long random value>
SERVICEOPS_N8N_REQUEST_CREATED_WEBHOOK_URL=https://n8n.serviceops.example.com/webhook/serviceops/request-created
SERVICEOPS_N8N_STATUS_CHANGED_WEBHOOK_URL=https://n8n.serviceops.example.com/webhook/serviceops/status-changed
SERVICEOPS_N8N_CLARIFICATION_WEBHOOK_URL=https://n8n.serviceops.example.com/webhook/serviceops/clarification-requested
SERVICEOPS_N8N_CUSTOMER_ANSWERED_WEBHOOK_URL=https://n8n.serviceops.example.com/webhook/serviceops/customer-answered
SERVICEOPS_API_BASE_URL=https://api.serviceops.example.com
SERVICEOPS_TELEGRAM_BOT_TOKEN=<bot token>
SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID=<dispatcher operations chat id>
N8N_HOST=n8n.serviceops.example.com
N8N_PROTOCOL=https
N8N_WEBHOOK_URL=https://n8n.serviceops.example.com/
N8N_BASIC_AUTH_USER=<admin user>
N8N_BASIC_AUTH_PASSWORD=<strong password>
N8N_ENCRYPTION_KEY=<long random value>
SERVICEOPS_BACKUP_DIR=/var/backups/serviceops
```

Do not use local development staff credentials, default passwords, or local URLs in production.

## Dokploy Setup

1. Create a new Dokploy Compose app from `docker-compose.production.yml`.
2. Add production environment variables in the Dokploy app settings.
3. Configure persistent volumes for `postgres-data` and `n8n-data`.
4. Route the web domain to service `web` port `80`.
5. Route the API domain to service `api` port `8000`.
6. Route the n8n domain to service `n8n` port `5678`.
7. Keep PostgreSQL and Redis without public routes.
8. Deploy the Compose app.

## Migration

Run migrations after PostgreSQL is healthy and before public traffic:

```bash
docker compose -f docker-compose.production.yml run --rm api python -m serviceops_api.operations.migrate
```

The command initializes the service request, knowledge base, AI suggestion, inventory, staff-management, and notification-delivery PostgreSQL schemas.

## First Admin Bootstrap

Create the first production admin after migrations and before public routing. Set these values from a secret store or secure shell session. Do not commit them to repository files, paste them into shared chat, or leave them in shell history.

```bash
export SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME="admin@example.com"
export SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME="ServiceOps Admin"
export SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD="<strong one-time password>"
```

Run the one-time bootstrap command:

```bash
docker compose -f docker-compose.production.yml run --rm \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME="$SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME" \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME="$SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME" \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD="$SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD" \
  api python -m serviceops_api.operations.bootstrap_admin
```

Expected output contains only non-secret fields:

```json
{"roles":["admin"],"status":"created","username":"admin@example.com"}
```

The command refuses to run when an active admin already exists. After the first admin exists, use the admin workspace to create dispatcher, technician, and inventory users. Rotate the bootstrap password through the admin workspace if the value was visible to more than the intended operator.

## Startup Order

1. PostgreSQL.
2. Redis.
3. API.
4. Web.
5. Worker.
6. n8n.
7. Telegram bot with the `integrations` profile when a production token is configured.

## Healthchecks

```bash
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/health"
curl -fsS "$SERVICEOPS_PUBLIC_WEB_BASE_URL/"
docker compose -f docker-compose.production.yml logs --tail=100 worker
docker compose -f docker-compose.production.yml logs --tail=100 n8n
docker compose -f docker-compose.production.yml --profile integrations logs --tail=100 telegram-bot
```

The Telegram bot is allowed to log that it is disabled when `SERVICEOPS_TELEGRAM_BOT_TOKEN` is empty.

## Production Staff Accounts

Production staff accounts are persisted and managed through the admin API/workspace after an admin exists.

The local seed command is intentionally limited to `local`, `development`, `dev`, and `test` environments and must not be used as a production account bootstrap. Do not expose the deployment publicly while relying on local-development seed users.

## First Launch Evidence

Complete `docs/operations/launch-smoke-evidence.md` during the first real Dokploy/VPS launch. Keep the completed evidence record in an operations-controlled location if it contains real hostnames, staff account names, or sensitive operational notes.

Minimum go/no-go evidence before enabling DNS or public traffic:

1. Migrations succeeded.
2. First admin bootstrap succeeded or an active production admin already exists from a previous approved launch.
3. API health and web root checks passed.
4. Request intake and public status smoke checks passed.
5. Persisted staff login and dispatcher route smoke checks passed.
6. Worker, Telegram bot, and n8n logs were reviewed.
7. Rollback target and latest verified backup were identified.

## Rollback

1. Disable public routing or put the Dokploy app into maintenance mode.
2. Redeploy the previous known-good Compose/image configuration.
3. Keep `postgres-data` and `n8n-data` volumes attached.
4. Restore the latest verified database backup only when the rollback requires data rollback.
5. Run smoke tests before restoring public routing.

## Logs

API, worker, and Telegram bot logs are structured JSON on stdout. Dokploy service logs are the first operational log source for this slice.
