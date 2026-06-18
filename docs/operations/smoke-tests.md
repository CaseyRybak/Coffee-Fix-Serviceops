# Smoke Tests

## Compose Config

```bash
docker compose -f docker-compose.production.yml --env-file .env.example config --quiet
```

For a real environment, run the same command with the production env file or Dokploy-rendered environment. Keep `--quiet` enabled so substituted secrets are not printed during validation.

## Scripted Check

```bash
SERVICEOPS_PUBLIC_API_BASE_URL=https://api.example.com \
SERVICEOPS_PUBLIC_WEB_BASE_URL=https://app.example.com \
SERVICEOPS_SMOKE_STAFF_USERNAME=dispatcher@example.com \
SERVICEOPS_SMOKE_STAFF_PASSWORD='<password>' \
N8N_TEST_WEBHOOK_URL=https://n8n.example.com/webhook/serviceops-smoke \
tools/operations/smoke_test.sh
```

`SERVICEOPS_SMOKE_STAFF_USERNAME` and `SERVICEOPS_SMOKE_STAFF_PASSWORD` are optional but must be set together. When set, the script verifies persisted staff login and the dispatcher request list route. `N8N_TEST_WEBHOOK_URL` is optional. When omitted, the script prints manual n8n follow-up checks.

## Manual API Health

```bash
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/health"
```

Expected: JSON status with `status` equal to `healthy`.

## Manual Web Root

```bash
curl -fsS "$SERVICEOPS_PUBLIC_WEB_BASE_URL/"
```

Expected: successful HTTP response containing the web shell.

## Manual Request Intake

```bash
curl -fsS -X POST "$SERVICEOPS_PUBLIC_API_BASE_URL/service-requests" \
  -H "content-type: application/json" \
  -d '{
    "customer": {"name": "Smoke Test", "phone": "+15555550100"},
    "machine": {"brand": "La Marzocco", "model": "Linea Mini"},
    "problem_description": "Smoke test request",
    "urgency": "standard"
  }'
```

Expected: response includes `request_number` and `public_token`.

## Manual Status Lookup

```bash
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/service-requests/<request-number>/status"
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/status/<public-token>"
```

Expected: public-safe status snapshot. Internal notes, AI suggestions, staff accounts, and inventory metadata must not be present.

## Staff Login And Dispatcher Route

```bash
token="$(curl -fsS -X POST "$SERVICEOPS_PUBLIC_API_BASE_URL/staff/login" \
  -H "content-type: application/json" \
  -d '{"username":"dispatcher@example.com","password":"<password>"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"

curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/dispatcher/service-requests" \
  -H "authorization: Bearer $token"
```

Expected: dispatcher list response for a persisted dispatcher account.

The scripted smoke check uses `SERVICEOPS_SMOKE_STAFF_USERNAME` and `SERVICEOPS_SMOKE_STAFF_PASSWORD` instead of placing credentials in the command body. Do not record staff passwords in smoke evidence.

## Worker

```bash
docker compose -f docker-compose.production.yml logs --tail=100 worker
docker compose -f docker-compose.production.yml exec worker \
  celery -A serviceops_worker.celery_app:celery_app inspect ping
```

Expected: worker process is running and Celery responds when the container is healthy.

## AI And RAG

Run deterministic provider and curated knowledge checks before enabling live AI:

```bash
cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_seed.py -v
```

Expected: curated repair seed documents pass source checks and representative RAG evaluation queries retrieve the expected source URI in the top three results.

Optional live-provider smoke should use a non-sensitive request and production secrets from the deployment environment:

```bash
cd apps/api && uv run --extra dev pytest tests/test_live_ai_provider.py tests/test_live_embedding_provider.py -v
```

Expected: provider contract tests pass with fake transports. To test real provider credentials, use a controlled deployment environment and do not place live API keys in shell history, smoke evidence, or repository files.

## Telegram Bot

```bash
docker compose -f docker-compose.production.yml logs --tail=100 telegram-bot
```

Expected: disabled-token log when no token is configured, or polling startup with a production token.

## n8n Webhook Path

Create a temporary test workflow with a webhook path such as `/webhook/serviceops-smoke`, then run:

```bash
curl -fsS -X POST "$N8N_TEST_WEBHOOK_URL" \
  -H "content-type: application/json" \
  -d '{"source":"serviceops-smoke"}'
```

Expected: n8n receives the payload and the workflow execution succeeds.

## n8n Operational Automation Preview

After API and n8n secrets are configured, preview the Phase 21 operational payloads without creating duplicate-suppression records:

```bash
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/notifications/n8n/operations/sla-reminders?mark_sent=false" \
  -H "X-ServiceOps-Callback-Secret: $SERVICEOPS_N8N_CALLBACK_SECRET"
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/notifications/n8n/operations/red-alerts?mark_sent=false" \
  -H "X-ServiceOps-Callback-Secret: $SERVICEOPS_N8N_CALLBACK_SECRET"
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/notifications/n8n/operations/owner-daily-report?mark_sent=false" \
  -H "X-ServiceOps-Callback-Secret: $SERVICEOPS_N8N_CALLBACK_SECRET"
curl -fsS "$SERVICEOPS_PUBLIC_API_BASE_URL/notifications/n8n/operations/low-stock-alerts?mark_sent=false" \
  -H "X-ServiceOps-Callback-Secret: $SERVICEOPS_N8N_CALLBACK_SECRET"
```

Expected: each response contains `automation`, `generated_at`, `window_key`, `items`, and `suppressed_count`. Evidence may record item counts and sanitized `event_id` values, but must not record callback secrets, Telegram bot tokens, customer phone numbers, Telegram chat ids, raw internal notes, provider bodies, or staff audit details.

To test duplicate suppression in a disposable local environment, call one endpoint twice with the same explicit `window_key` and default `mark_sent=true`. Expected: first call returns matching `items`; second call returns an empty `items` list and `suppressed_count` equal to the suppressed item count.

## Backup Check

On a non-production database or during a controlled maintenance window:

```bash
tools/operations/postgres_backup.sh
```

Expected: a `.dump` file and `.sha256` file are created in `SERVICEOPS_BACKUP_DIR`.

## Restore Dry-Run Check

Use the production-safe restore dry-run in `docs/operations/backup-restore.md` before public launch and after backup script changes.

Expected: checksum verification passes, restore targets a disposable database, migrations pass against the restored target, smoke checks pass, and abort conditions are recorded.

## Log Query Check

Use `docs/operations/operational-diagnostics.md` to confirm one smoke request can be traced by `request_number` through:

- `service_request.created`;
- a staff action when staff smoke credentials are configured;
- `notification.event_queued`;
- `notification.delivery_recorded`;
- `notification.callback_recorded` when n8n callback smoke is enabled.

Expected: copied evidence contains safe operational fields only and excludes passwords, tokens, webhook secrets, API keys, customer phone numbers, Telegram chat ids, raw AI prompts, provider bodies, and internal notes.

## Evidence Capture

For first launch, record smoke results in `docs/operations/launch-smoke-evidence.md` or an operations-controlled copy of that template. Completed evidence should include command output, request number, service checks, rollback readiness, and final go/no-go decision without reusable passwords or webhook secrets.

For degraded-service follow-up, use `docs/operations/incident-response.md`.
