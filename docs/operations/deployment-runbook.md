# Deployment Runbook

## Preconditions

- VPS has Docker, Docker Compose, and Dokploy installed.
- DNS records point the web, API, and n8n hostnames to the VPS.
- HTTPS is configured in Dokploy or the reverse proxy before public exposure.
- The repository `main` branch is available to Dokploy.
- Production `.env` values are set from `.env.example` with real secrets.
- A persistent backup directory exists on the host and is covered by host-level retention.
- A production-safe first-admin bootstrap command is run before public launch. The current local seed command is intentionally blocked in production.

## Services

- API: FastAPI app from `apps/api`.
- Web: static React/Vite app served by nginx from `apps/web`.
- Worker: Celery worker from `apps/worker`.
- Telegram bot: aiogram polling process from `apps/telegram-bot`.
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
SERVICEOPS_AI_PROVIDER=deterministic
SERVICEOPS_EMBEDDING_PROVIDER=deterministic
SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET=<long random value>
SERVICEOPS_N8N_CALLBACK_SECRET=<different long random value>
SERVICEOPS_N8N_REQUEST_CREATED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/request-created
SERVICEOPS_N8N_STATUS_CHANGED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/status-changed
SERVICEOPS_N8N_CLARIFICATION_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/clarification-requested
SERVICEOPS_N8N_CUSTOMER_ANSWERED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/customer-answered
SERVICEOPS_API_BASE_URL=http://api:8000
SERVICEOPS_TELEGRAM_BOT_TOKEN=<bot token>
SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID=<dispatcher operations chat id>
N8N_HOST=n8n.serviceops.example.com
N8N_PROTOCOL=https
N8N_WEBHOOK_URL=https://n8n.serviceops.example.com/
N8N_BASIC_AUTH_USER=<admin user>
N8N_BASIC_AUTH_PASSWORD=<strong password>
N8N_ENCRYPTION_KEY=<long random value>
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
SERVICEOPS_BACKUP_DIR=/var/backups/serviceops
```

The production API and n8n services should call each other through private Compose service names. `N8N_WEBHOOK_URL` controls generated public n8n URLs for the UI/runtime, but the ServiceOps backend webhook targets should remain `http://n8n:5678/...` when n8n runs in the same Compose app.

For live AI, set the OpenAI-compatible values from `docs/operations/ai-providers.md` in Dokploy. Do not commit provider API keys to `.env.example`, screenshots, smoke evidence, or workflow exports.

Do not use local development staff credentials, default passwords, or local URLs in production.

## Dokploy Setup

1. Create a new Dokploy Compose app from the repository `main` branch and `docker-compose.production.yml`.
2. Add production environment variables in the Dokploy app settings.
3. Configure persistent volumes for `postgres-data` and `n8n-data`.
4. Route the web domain to service `web` port `80`.
5. Route the API domain to service `api` port `8000`.
6. Do not publish `5678` directly. Self-hosted n8n runs in the production Compose app; route the n8n domain through Dokploy/Traefik to service `n8n` port `5678` only if the UI must be reachable.
7. Keep PostgreSQL and Redis without public routes.
8. Deploy the Compose app.

## Public Port Posture

Expected production posture:

- Public web/API traffic should go through `80`/`443` after domains and HTTPS are configured.
- n8n should not expose `5678` directly; API-to-n8n webhook calls use `http://n8n:5678` inside Docker.
- PostgreSQL `5432` and Redis `6379` stay private.
- Temporary direct IP test ports such as web `3001` and API `8000` must be closed after reverse-proxy routing is ready.
- Dokploy `3000` is an administrative surface and should be restricted to trusted IP/VPN access before public launch.

On the current single-node Dokploy host, Docker Swarm may leave `2377` and `7946` listening locally because Dokploy initializes Swarm for its own internal services. They are not required to be publicly reachable for the ServiceOps Compose app. Keep firewall default-deny inbound and do not add public allow rules for `2377` or `7946`.

## Migration

Run migrations after PostgreSQL is healthy and before public traffic:

```bash
docker compose -f docker-compose.production.yml run --rm api python -m serviceops_api.operations.migrate
```

The command initializes the service request, knowledge base, AI suggestion, inventory, staff-management, and notification-delivery PostgreSQL schemas.

If live AI/RAG is enabled, ingest the curated repair knowledge after migrations and before dispatcher AI smoke tests:

```bash
docker compose -f docker-compose.production.yml run --rm api python -m serviceops_api.operations.seed_knowledge_base
```

The seed command uses the configured embedding provider and skips already-ingested seed documents by `source_uri`.

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
7. Telegram bot when a production token is configured.

Only one `telegram-bot` polling process may use a Telegram bot token. If local and production intentionally share one bot token, stop the local `telegram-bot` service while production polling is active; otherwise a local bot can consume a production `/start <token>` update and make customer opt-in fail.

## Healthchecks

```bash
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/health"
curl -fsS "$SERVICEOPS_PUBLIC_WEB_BASE_URL/"
docker compose -f docker-compose.production.yml logs --tail=100 worker
docker compose -f docker-compose.production.yml logs --tail=100 n8n
docker compose -f docker-compose.production.yml logs --tail=100 telegram-bot
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

Before public traffic, also complete the restore dry-run evidence in `docs/operations/backup-restore.md` and record request trace evidence with `docs/operations/operational-diagnostics.md`.

Self-hosted n8n production evidence from June 16, 2026 is recorded in `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`. That evidence verifies the request-created Telegram path on `CFX-20260616-000008`; a full dispatcher clarification smoke still requires disposable production staff credentials.

## AI Provider Go/No-Go

Before switching `SERVICEOPS_AI_PROVIDER` or `SERVICEOPS_EMBEDDING_PROVIDER` to `openai-compatible`, verify:

1. Provider API keys are present only in Dokploy or a secret store.
2. `docs/operations/ai-providers.md` has been followed for model, base URL, timeout, and retry values.
3. Deterministic RAG evaluation passes with the curated seed documents.
4. A dispatcher AI suggestion smoke test succeeds on a non-sensitive request.
5. Public status snapshots still exclude AI suggestions, provider payloads, and source metadata.

## Rollback

1. Disable public routing or put the Dokploy app into maintenance mode.
2. Redeploy the previous known-good Compose/image configuration.
3. Keep `postgres-data` and `n8n-data` volumes attached.
4. Restore the latest verified database backup only when the rollback requires data rollback.
5. Run smoke tests before restoring public routing.

Use `docs/operations/incident-response.md` to decide between rollback, containment, and restore-from-backup.

## Logs

API, worker, and Telegram bot logs are structured JSON on stdout. Dokploy service logs are the first operational log source for this slice.

Use `docs/operations/operational-diagnostics.md` for `jq` filters, request tracing, safe evidence redaction, and read-only PostgreSQL checks.
