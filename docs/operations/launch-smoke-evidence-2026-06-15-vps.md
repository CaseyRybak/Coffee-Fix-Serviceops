# Launch Smoke Evidence: Aeza VPS Test Deployment

This record captures the first real Coffee Fix ServiceOps VPS/Dokploy test deployment on June 15, 2026. It is sanitized and must not contain passwords, API keys, Telegram tokens, webhook secrets, raw provider payloads, customer phone numbers, or Telegram chat ids.

## Deployment Metadata

- Date: 2026-06-15
- Operator: Codex with project owner
- Environment: Aeza VPS test production environment
- VPS: Ubuntu 24.04, IP `138.124.91.212`, root SSH key access
- Initial deployed Git revision: `4b65f18` on branch `production`
- Latest verified application-code revision after worker fix: `f59989c` on branch `production`
- Latest observed Dokploy checkout during post-evidence redeploy: `e2c0f75` on branch `production`
- Dokploy app: `coffee-fix-serviceops`
- Web URL: `http://138.124.91.212:3001`
- API URL: `http://138.124.91.212:8000`
- Dokploy URL: `http://138.124.91.212:3000`
- n8n runtime used for notifications: n8n Cloud at `caseyrybak.app.n8n.cloud`

## Server Setup Evidence

- Docker installed and verified with `docker run hello-world`.
- Docker version observed: `29.5.3`.
- Docker Compose version observed: `v5.1.4`.
- Dokploy installed and first admin account created.
- Dokploy projects created separately:
  - `Coffee-Fix-Serviceops`
  - `Hermes`
- `Coffee-Fix-Serviceops` compose service uses repository `CaseyRybak/Coffee-Fix-Serviceops`, branch `production`, compose path `./docker-compose.production.yml`.
- PostgreSQL and Redis remain private containers with no UFW public rules.
- UFW public rules during test deployment:
  - `OpenSSH`
  - `3000/tcp` for Dokploy
  - `3001/tcp` for test web access
  - `8000/tcp` for test API access
- Ports `80/443` are not opened for public routing in this test state.

## Environment And Integration Notes

- Dokploy environment values were configured with live Telegram, AI, embedding, and n8n webhook URLs.
- n8n Cloud environment variables are unavailable on the current n8n plan, so live cloud workflows were updated directly through the n8n MCP API with the same generated webhook and callback secrets configured in Dokploy.
- Repository workflow exports were not modified; local/self-hosted n8n can still use the repository `$env`-based workflow exports.
- n8n Cloud workflows updated and republished:
  - `ServiceOps - Request Created Dispatcher Alert`
  - `ServiceOps - Status Changed Customer Notification`
  - `ServiceOps - Clarification Customer Notification`
  - `ServiceOps - Customer Answered Dispatcher Alert`
- n8n delivery-result callback URL now targets `http://138.124.91.212:8000/notifications/n8n/delivery-results`.
- The temporary n8n MCP API key used during setup was exposed in chat and should be rotated before any public launch.

## Migration Evidence

Command:

```bash
docker exec coffeefixserviceops-coffeefixserviceops-up3whl-api-1 \
  python -m serviceops_api.operations.migrate
```

Result:

```json
{"database": "postgres", "status": "ok"}
```

The Python runtime emitted a `runpy` warning about the module already being in `sys.modules`; the command still completed successfully with PostgreSQL status `ok`.

## First Admin Bootstrap Evidence

Production first-admin bootstrap was run through the API container after migrations.

Recorded result:

```json
{"roles":["admin"],"status":"created","username":"admin@coffeefix.local"}
```

The admin password was provided interactively by the operator and is not recorded here.

## Smoke Test Evidence

Command:

```bash
SERVICEOPS_PUBLIC_API_BASE_URL="http://138.124.91.212:8000" \
SERVICEOPS_PUBLIC_WEB_BASE_URL="http://138.124.91.212:3001" \
bash tools/operations/smoke_test.sh
```

Result:

```text
checking API health: http://138.124.91.212:8000/health
checking web root: http://138.124.91.212:3001/
creating smoke service request
checking status by request number: CFX-20260615-000002
checking status by public token
SERVICEOPS_SMOKE_STAFF_USERNAME/PASSWORD not configured; skipping staff route smoke check.
N8N_TEST_WEBHOOK_URL is not configured; manually verify the n8n webhook path.
manual follow-up: inspect worker logs and Telegram bot profile logs in Dokploy or Docker Compose.
smoke checks passed for request CFX-20260615-000002
```

## Service Checks

- API health returned healthy:

```json
{"service":"serviceops-api","status":"healthy","environment":"production","dependencies":{"postgres":"configured","redis":"configured","storage":"postgres"}}
```

- Web root returned `HTTP/1.1 200 OK`.
- Request intake created request `CFX-20260615-000002`.
- Public status lookup by request number succeeded.
- Public status lookup by token succeeded.
- Staff login and dispatcher route automated smoke was not run because no disposable staff smoke credentials were provided to the script.
- Production admin and dispatcher accounts were created manually through the application flow.
- Worker runtime review was completed after a Redis client dependency fix; see "Worker Fix And Redeploy Evidence".
- Telegram bot container is not running in the current compose profile; customer Telegram opt-in bot verification remains a follow-up before public launch.
- n8n Cloud webhook execution for a real API-created request succeeded.

## Worker Fix And Redeploy Evidence

Initial worker runtime check showed the worker container exited because Kombu's Redis transport could not find the Python `redis` client:

```text
AttributeError: 'NoneType' object has no attribute 'Redis'
```

Fix committed and pushed:

```text
f59989c fix: add redis client for worker broker
```

Local worker test evidence after the fix:

```bash
cd apps/worker && uv run --extra dev pytest
```

Result:

```text
15 passed
```

The Dokploy working copy on the VPS was updated to include `f59989c`, and the worker service was rebuilt and recreated from `docker-compose.production.yml`.

After the evidence documentation commit, the Dokploy checkout was observed at `e2c0f75` and `api`, `web`, and `worker` were rebuilt/recreated from the production compose file:

```text
BEFORE_COMMIT e2c0f75
AFTER_COMMIT e2c0f75
coffeefixserviceops-coffeefixserviceops-up3whl-api-1 Up 11 seconds (healthy)
coffeefixserviceops-coffeefixserviceops-up3whl-web-1 Up Less than a second
coffeefixserviceops-coffeefixserviceops-up3whl-worker-1 Up 11 seconds
```

Fresh deployed verification:

```text
API_HEALTH
{"service":"serviceops-api","status":"healthy","environment":"production","dependencies":{"postgres":"configured","redis":"configured","storage":"postgres"}}

WEB_STATUS 200

WORKER_STATUS
coffeefixserviceops-coffeefixserviceops-up3whl-worker-1 Up 4 minutes

REDIS_IMPORT
redis_transport_ok True
```

Worker log tail after redeploy:

```text
transport:   redis://redis:6379/0
results:     redis://redis:6379/1
serviceops_worker.knowledge_base_tasks.embed_knowledge_document
Connected to redis://redis:6379/0
celery@ef3c9b0871d0 ready.
```

The worker still runs as root inside the production container because this test deployment follows the current root-based VPS decision. Celery emits a standard warning for that runtime mode.

## n8n And Notification Evidence

- Synthetic n8n MCP execution for `ServiceOps - Request Created Dispatcher Alert`: execution `71`, final status `success`.
- Real API-created request `CFX-20260615-000001` triggered n8n Cloud execution `72`, final status `success`.
- PostgreSQL delivery-result evidence:

```text
CFX-20260615-000001 | service_request.created | sent | telegram | provider_message_id present
CFX-20260615-000002 | service_request.created | sent | telegram | provider_message_id present
```

- A prior `service_request.clarification_requested` attempt for `CFX-20260615-000001` is recorded as `failed` and should be retested after staff-workspace workflow checks.

## Backup Evidence

Backup command was run on the VPS through the production PostgreSQL container.

Backup file:

```text
/var/backups/serviceops/serviceops-20260615-205909.dump
```

Checksum result:

```text
/var/backups/serviceops/serviceops-20260615-205909.dump: OK
```

## Restore Dry-Run Evidence

- Backup file: `/var/backups/serviceops/serviceops-20260615-205909.dump`
- Checksum verification result: OK
- Disposable target host: temporary Docker container `serviceops-restore-drill-postgres`
- Disposable target database: `serviceops_restore_drill`
- Public routes for restore target: none
- Restore result: `pg_restore` completed into disposable target
- Migration result against restored target:

```json
{"database": "postgres", "status": "ok"}
```

- Restored service request row count: `2`
- Cleanup: temporary restore PostgreSQL container and Docker network removed

## Log Trace Evidence

- Smoke request number: `CFX-20260615-000002`
- `service_request.created` notification delivery result found in PostgreSQL.
- `notification.callback_recorded` path verified indirectly by `sent` delivery result from n8n callback.
- Full structured-log trace capture remains a follow-up before public launch.

## Rollback Readiness

- Previous known-good compose configuration before worker fix: branch `production`, commit `4b65f18`.
- Latest verified application-code fix after worker fix: branch `production`, commit `f59989c`.
- Latest observed Dokploy checkout after evidence redeploy: branch `production`, commit `e2c0f75`.
- Latest verified backup identified: `/var/backups/serviceops/serviceops-20260615-205909.dump`.
- Maintenance/public-route disable procedure: close UFW rules for `3001/tcp` and `8000/tcp`, and disable Dokploy routes when domains are later configured.
- Restore decision owner: project owner.

## Current Gaps Before Public Launch

- Domains and HTTPS are not configured; current deployment is IP-and-port based test access over HTTP.
- Staff route smoke should be rerun with disposable staff credentials through `tools/operations/smoke_test.sh`.
- Telegram bot opt-in runtime should be reviewed after deciding whether the optional Telegram bot profile is part of the launch.
- n8n MCP API key and any exposed setup secrets should be rotated before public launch.
- Real database transfer has not happened yet; smoke, backup, and n8n checks must be repeated after import.

## Go/No-Go

- Decision: No public launch yet.
- Reason: VPS test deployment and n8n integration passed, but the deployment is still HTTP over IP, uses temporary public test ports, has no domain/HTTPS, and real database transfer is not complete.
