# Operational Diagnostics

Use this guide for first-line production diagnosis from Dokploy, Docker Compose logs, and read-only PostgreSQL checks.

## Safe Trace Fields

Structured logs use operator-safe fields:

- `request_number`: public request number.
- `event_id`: notification event id.
- `event_type`: domain event name.
- `actor_username`: staff username for authenticated actions.
- `action`: stable operation name.
- `target`: affected request, staff username, event id, document id, or service name.
- `outcome`: `succeeded`, `failed`, `blocked`, `skipped`, or `retried`.
- `reason`: short safe reason.
- `duration_ms`: elapsed runtime where useful.
- `provider`: `deterministic`, `openai-compatible`, `n8n`, `telegram`, or `postgres`.

Never copy passwords, hashes, bearer tokens, Telegram opt-in tokens, webhook secrets, API keys, raw AI prompts, provider bodies, customer phone numbers, Telegram chat ids, internal note bodies, or unrestricted source chunk text into tickets or launch evidence.

## Trace One Request

1. Start with the customer-safe `request_number`.
2. Search API logs for `service_request.created`.
3. Search API logs for `dispatcher.*` actions on the same `request_number`.
4. Search notification logs for `notification.event_queued`, `notification.delivery_recorded`, and `notification.callback_recorded`.
5. Search worker logs when the problem involves knowledge-base embeddings or AI/RAG preparation.
6. Search Telegram bot logs for `telegram.opt_in_linked` when customer notification linking is involved.
7. Confirm the public status endpoint still excludes internal notes, staff data, AI suggestions, audit data, and notification metadata.

## Docker And Dokploy Logs

```bash
docker compose -f docker-compose.production.yml logs --tail=500 api
docker compose -f docker-compose.production.yml logs --tail=500 worker
docker compose -f docker-compose.production.yml --profile integrations logs --tail=500 telegram-bot
docker compose -f docker-compose.production.yml logs --tail=500 n8n
```

In Dokploy, use each service log view first. Export only the lines needed for the incident, then redact hostnames, account names, and operational notes when required by the incident owner.

## jq Filters

Filter a saved API log file by request:

```bash
jq -c 'select(.request_number=="CFX-20260615-000001")' api.log
```

Filter one notification event:

```bash
jq -c 'select(.event_id=="CFX-20260615-000001:service_request.created:1")' api.log
```

Find failed outcomes:

```bash
jq -c 'select(.outcome=="failed") | {timestamp,service,logger,action,target,reason}' api.log
```

List staff actions for one actor:

```bash
jq -c 'select(.actor_username=="dispatcher@example.com") | {timestamp,action,target,outcome,reason}' api.log
```

## Read-Only PostgreSQL Checks

Use a read-only database user when available.

Notification delivery attempts:

```sql
SELECT event_id, event_type, request_number, status, provider_message_id, error, attempt_count, updated_at
FROM notification_delivery_attempts
WHERE request_number = 'CFX-20260615-000001'
ORDER BY id;
```

Staff audit events for a request or staff user:

```sql
SELECT actor_username, target_username, action, metadata, created_at
FROM staff_audit_events
WHERE actor_username = 'dispatcher@example.com'
   OR target_username = 'dispatcher@example.com'
ORDER BY id DESC
LIMIT 50;
```

Recent failed staff auth events:

```sql
SELECT actor_username, target_username, action, metadata, created_at
FROM staff_audit_events
WHERE action IN ('staff.login_failed', 'staff.token_rejected', 'staff.role_forbidden')
ORDER BY id DESC
LIMIT 50;
```

## Evidence Redaction

Before copying evidence into a ticket or launch note:

- Keep `request_number`, `event_id`, `action`, `outcome`, safe `reason`, and timestamps.
- Remove customer phone numbers, Telegram chat ids, bearer tokens, webhook secrets, API keys, raw prompts, provider request or response bodies, internal notes, and full source chunk text.
- Replace staff names or hostnames when the incident owner marks them sensitive.
- Prefer a short excerpt of relevant JSON log lines over full service logs.
