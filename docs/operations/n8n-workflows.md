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
SERVICEOPS_N8N_REQUEST_CREATED_WEBHOOK_URL=https://<n8n-host>/webhook/serviceops/request-created
SERVICEOPS_N8N_STATUS_CHANGED_WEBHOOK_URL=https://<n8n-host>/webhook/serviceops/status-changed
SERVICEOPS_N8N_CLARIFICATION_WEBHOOK_URL=https://<n8n-host>/webhook/serviceops/clarification-requested
SERVICEOPS_N8N_CUSTOMER_ANSWERED_WEBHOOK_URL=https://<n8n-host>/webhook/serviceops/customer-answered
SERVICEOPS_TELEGRAM_BOT_USERNAME=<bot username without @>
SERVICEOPS_TELEGRAM_BOT_API_SECRET=<secret used by the bot when linking opt-in tokens>
```

n8n runtime:

```bash
SERVICEOPS_API_BASE_URL=https://<api-host>
SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET=<same inbound webhook value>
SERVICEOPS_N8N_CALLBACK_SECRET=<same callback value>
SERVICEOPS_TELEGRAM_BOT_TOKEN=<bot token>
SERVICEOPS_DISPATCHER_TELEGRAM_CHAT_ID=<dispatcher operations chat id>
```

Telegram opt-in flow:

1. The public status page calls `POST /service-requests/{request_number}/telegram-opt-in`.
2. The API returns `https://t.me/<SERVICEOPS_TELEGRAM_BOT_USERNAME>?start=<token>`.
3. The Telegram bot handles `/start <token>`, calls `POST /notifications/telegram/opt-ins/{token}/link`, and stores `telegram_chat_id`.
4. Customer Telegram notifications use `payload.telegram_chat_id`. `payload.telegram_handle` is retained only as display/contact metadata.

## Live Workflow Records

Created through the n8n MCP API during Phase 12:

- `ServiceOps - Request Created Dispatcher Alert`: `fbEwkH56MkvmDnsD`
- `ServiceOps - Status Changed Customer Notification`: `0njpM50BqmqJeZE2`
- `ServiceOps - Clarification Customer Notification`: `bJWa9A1ALnypyE2V`
- `ServiceOps - Customer Answered Dispatcher Alert`: `PVYG8clWqn9opv1l`

Repository exports are stored in `docs/operations/n8n-workflows/`.

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

The live n8n instance already contains the Phase 12 workflows listed above. To restore them in another n8n instance, import the JSON exports from `docs/operations/n8n-workflows/`, configure the environment variables, activate the workflows, then set backend webhook URL variables to the production paths.
