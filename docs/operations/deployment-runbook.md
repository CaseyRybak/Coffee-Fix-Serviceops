# Deployment Runbook

## Preconditions

- VPS has Docker, Docker Compose, and Dokploy installed.
- DNS records point the web, API, and n8n hostnames to the VPS.
- HTTPS is configured in Dokploy or the reverse proxy before public exposure.
- The repository is available to Dokploy.
- Production `.env` values are set from `.env.example` with real secrets.
- A persistent backup directory exists on the host and is covered by host-level retention.

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

The command initializes the service request, knowledge base, AI suggestion, inventory, and staff-management PostgreSQL schemas.

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

Create the first persisted admin before public operations. Then use the admin workspace to create dispatcher, technician, and inventory users. Local-development seed users are fallback-only and must not be treated as production account management.

## Rollback

1. Disable public routing or put the Dokploy app into maintenance mode.
2. Redeploy the previous known-good Compose/image configuration.
3. Keep `postgres-data` and `n8n-data` volumes attached.
4. Restore the latest verified database backup only when the rollback requires data rollback.
5. Run smoke tests before restoring public routing.

## Logs

API, worker, and Telegram bot logs are structured JSON on stdout. Dokploy service logs are the first operational log source for this slice.
