# n8n Workflows

n8n automates delivery and operational routing around backend events. It does not own service-request state, staff identity, customer answers, inventory counts, or repair lifecycle transitions. Source-of-truth state remains in the ServiceOps API and PostgreSQL.

## Shared Webhook Rules

- ServiceOps sends approved notification events to n8n production webhook paths.
- Each inbound n8n webhook validates `X-ServiceOps-Webhook-Secret` against `SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET`.
- Each backend callback sends `X-ServiceOps-Callback-Secret` matching `SERVICEOPS_N8N_CALLBACK_SECRET`.
- n8n callbacks write delivery outcomes only; they must not mutate service-request lifecycle state.
- Backend event IDs are idempotency keys shaped as `<request_number>:<event_type>:<sequence>`.
- Payloads are public-safe and must not include internal notes, AI internals, staff-only data, audit data, technician phone numbers, inventory metadata, or shared secrets.

## Required Environment

Backend API:

```bash
SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET=<long random value>
SERVICEOPS_N8N_CALLBACK_SECRET=<different long random value>
SERVICEOPS_N8N_REQUEST_CREATED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/request-created
SERVICEOPS_N8N_STATUS_CHANGED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/status-changed
SERVICEOPS_N8N_CLARIFICATION_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/clarification-requested
SERVICEOPS_N8N_CUSTOMER_ANSWERED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/customer-answered
SERVICEOPS_TELEGRAM_BOT_USERNAME=<bot username without @>
SERVICEOPS_TELEGRAM_BOT_API_SECRET=<secret used by the bot when linking opt-in tokens>
```

The production Compose deployment should use the private Docker service URL above for API-to-n8n webhook calls. Use public HTTPS n8n webhook URLs only when n8n is intentionally hosted outside the production Compose network.

n8n runtime:

```bash
SERVICEOPS_API_BASE_URL=http://api:8000
SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET=<same inbound webhook value>
SERVICEOPS_N8N_CALLBACK_SECRET=<same callback value>
SERVICEOPS_TELEGRAM_BOT_TOKEN=<bot token>
SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID=<dispatcher operations chat id>
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
```

Telegram opt-in flow:

1. The public status page calls `POST /service-requests/{request_number}/telegram-opt-in`.
2. The API returns `https://t.me/<SERVICEOPS_TELEGRAM_BOT_USERNAME>?start=<token>`.
3. The Telegram bot handles `/start <token>`, calls `POST /notifications/telegram/opt-ins/{token}/link`, and stores `telegram_chat_id`.
4. Customer Telegram notifications use `payload.telegram_chat_id`. `payload.telegram_handle` is retained only as display/contact metadata.

## Live Workflow Records

Created through the n8n MCP API during Phase 12 and now imported into the self-hosted VPS n8n production runtime:

- `ServiceOps - Request Created Dispatcher Alert`: `fbEwkH56MkvmDnsD`
- `ServiceOps - Status Changed Customer Notification`: `0njpM50BqmqJeZE2`
- `ServiceOps - Clarification Customer Notification`: `bJWa9A1ALnypyE2V`
- `ServiceOps - Customer Answered Dispatcher Alert`: `PVYG8clWqn9opv1l`

Repository exports are stored in `docs/operations/n8n-workflows/`.

The earlier n8n Cloud workflows are no longer the production path. Keep them only as historical setup context or remove them after the self-hosted path has passed the full launch smoke.

## Production VPS Runtime

The VPS production API calls n8n over the Compose network through `http://n8n:5678`. n8n callback nodes call the API through `SERVICEOPS_API_BASE_URL=http://api:8000`, and delivery-result callbacks use `POST /notifications/n8n/delivery-results`.

The self-hosted n8n container should not publish `5678` directly to the internet. If the n8n UI must be reachable, route it through Dokploy/Traefik with HTTPS and access controls.

Production evidence from June 16, 2026:

- All four workflow exports listed above were imported, published, and active on the VPS n8n service.
- `CFX-20260616-000008` verified the request-created path end-to-end: API event emission, self-hosted n8n execution, Telegram delivery, and backend delivery-result callback with final status `sent`.
- Full dispatcher clarification smoke still needs production staff credentials; the local smoke covers the protected opt-in simulation plus clarification delivery path.

## Workflow: Request Created Dispatcher Alert

Trigger: `POST /webhook/serviceops/request-created`

Backend event: `service_request.created`

Input payload:

- `event_id`
- `event_type`
- `request_number`
- `payload.request_number`
- `payload.customer_name`
- `payload.customer_phone_masked`
- `payload.machine_brand`
- `payload.machine_model`
- `payload.urgency`
- `payload.public_status_url`

Steps:

1. Validate shared secret.
2. Format a dispatcher-safe Telegram message.
3. Send to `SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID`.
4. Call `POST /notifications/n8n/delivery-results` with `sent` or `failed`.

## Workflow: Status Changed Customer Notification

Trigger: `POST /webhook/serviceops/status-changed`

Backend event: `service_request.status_changed`

Input payload:

- `event_id`
- `event_type`
- `request_number`
- `payload.request_number`
- `payload.customer_name`
- `payload.telegram_handle`
- `payload.telegram_chat_id`
- `payload.new_status`
- `payload.public_status_url`

Steps:

1. Validate shared secret.
2. Format a customer-safe status update.
3. Send Telegram message to the opted-in customer chat ID.
4. Call backend delivery-result callback.

## Workflow: Clarification Customer Notification

Trigger: `POST /webhook/serviceops/clarification-requested`

Backend event: `service_request.clarification_requested`

Input payload:

- `event_id`
- `event_type`
- `request_number`
- `payload.request_number`
- `payload.telegram_handle`
- `payload.telegram_chat_id`
- `payload.question_id`
- `payload.question`
- `payload.public_status_url`

Steps:

1. Validate shared secret.
2. Format a customer-safe clarification prompt.
3. Send Telegram message to the opted-in customer chat ID.
4. Call backend delivery-result callback.

## Workflow: Customer Answered Dispatcher Alert

Trigger: `POST /webhook/serviceops/customer-answered`

Backend event: `service_request.customer_answered`

Input payload:

- `event_id`
- `event_type`
- `request_number`
- `payload.request_number`
- `payload.question_id`
- `payload.status`
- `payload.public_status_url`

Steps:

1. Validate shared secret.
2. Format a dispatcher alert that the customer answered.
3. Send to `SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID`.
4. Call backend delivery-result callback.

## Backend Callback

Path: `POST /notifications/n8n/delivery-results`

Headers:

- `X-ServiceOps-Callback-Secret: <SERVICEOPS_N8N_CALLBACK_SECRET>`

Body:

```json
{
  "event_id": "CFX-20260610-000001:service_request.created:1",
  "status": "sent",
  "channel": "telegram",
  "provider_message_id": "123456",
  "error": "",
  "attempt_count": 1
}
```

Allowed statuses: `queued`, `sent`, `failed`, `retried`.

## Import Or Restore

The live VPS n8n instance already contains the Phase 12 workflows listed above. To restore them in another n8n instance, import the JSON exports from `docs/operations/n8n-workflows/`, configure the environment variables, activate the workflows, then set backend webhook URL variables to the target runtime paths.

## Local n8n Runtime

Local n8n runs as the `n8n` service in `docker-compose.yml` and is bound to `127.0.0.1:${N8N_PORT:-5678}`. It shares the local Postgres container with ServiceOps by using the `n8n_` table prefix and stores n8n files in the `n8n-data` Docker volume.

For local container-to-container calls, backend webhook URLs must use the Docker service name:

```bash
SERVICEOPS_N8N_REQUEST_CREATED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/request-created
SERVICEOPS_N8N_STATUS_CHANGED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/status-changed
SERVICEOPS_N8N_CLARIFICATION_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/clarification-requested
SERVICEOPS_N8N_CUSTOMER_ANSWERED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/customer-answered
```

The n8n callback target is environment-based inside the workflow exports:

```bash
SERVICEOPS_API_BASE_URL=http://api:8000
```

The project may use the same Telegram bot and staff chat in local and production while it remains a pet project. Keep those values only in ignored environment files or deployment secrets, never in workflow exports or committed docs.

Only one polling instance may use a Telegram bot token at a time. While production polling is active with the shared bot token, keep the local `telegram-bot` service stopped. Otherwise local polling can consume a production `/start <token>` message and make the opt-in link fail against the local API.

To import the repository exports into local n8n:

```bash
python3 - <<'PY'
import json
from pathlib import Path

src = Path("docs/operations/n8n-workflows")
dst = Path("/tmp/serviceops-n8n-import")
dst.mkdir(parents=True, exist_ok=True)
for old in dst.glob("*.json"):
    old.unlink()
for path in src.glob("*.json"):
    data = json.loads(path.read_text())
    workflow = data["workflow"]
    workflow["active"] = False
    workflow.pop("activeVersion", None)
    workflow.pop("triggerInfo", None)
    workflow.pop("scopes", None)
    workflow.pop("canExecute", None)
    (dst / path.name).write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n")
PY

docker compose up -d n8n
docker compose exec -T n8n mkdir -p /tmp/serviceops-n8n-import
docker compose cp /tmp/serviceops-n8n-import/. n8n:/tmp/serviceops-n8n-import
docker compose exec -T n8n n8n import:workflow --separate --input=/tmp/serviceops-n8n-import
docker compose exec -T n8n n8n publish:workflow --id=fbEwkH56MkvmDnsD
docker compose exec -T n8n n8n publish:workflow --id=0njpM50BqmqJeZE2
docker compose exec -T n8n n8n publish:workflow --id=bJWa9A1ALnypyE2V
docker compose exec -T n8n n8n publish:workflow --id=PVYG8clWqn9opv1l
docker compose restart n8n
```

Use a clean destination path when re-importing. If `docker compose cp` copies a directory into an existing directory, n8n can accidentally import stale JSON from the parent path.

Run the local notification smoke after `api` and `n8n` are up. Start `telegram-bot` locally only when production polling is intentionally stopped or when a separate development bot token is configured:

```bash
set -a
. ./.env
set +a
SERVICEOPS_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 python3 tools/operations/local_notification_smoke.py
```

The smoke creates a local request, links a Telegram opt-in through the protected bot endpoint, asks a dispatcher clarification, and waits until the clarification delivery callback becomes `sent`. It simulates the Telegram `/start <token>` link step because a local script cannot make a real Telegram user send `/start` automatically.
