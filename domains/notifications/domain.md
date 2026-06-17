# Notifications Domain

## Responsibility

This domain handles Telegram, n8n webhooks, and later other delivery channels.

## First Use Cases

- Link Telegram chat to request.
- Send request-created notification.
- Send status-changed notification.
- Receive customer answer to clarification question.

## Phase 03 Telegram Opt-In Contract

Phase 03 defined the first backend contract for Telegram notification opt-in.

- `POST /service-requests/{request_number}/telegram-opt-in` accepts an optional Telegram handle.
- The API returns the request number, saved Telegram handle, one-time token, and a bot deep link shaped as `https://t.me/coffeefix_service_bot?start=<token>`.
- The token links a Telegram chat to a service request after the bot receives `/start <token>`.
- The Telegram bot consumes the token through `POST /notifications/telegram/opt-ins/{token}/link` and persists `telegram_chat_id` for later notification delivery.

Customer clarification answers are recorded through the service-request API because the question belongs to the repair lifecycle. Notifications subscribe to those events for n8n delivery and dispatcher/customer alerts.

## Phase 10 Operations Boundary

Phase 10 documented n8n workflow designs and deployment wiring. Phase 12 made notification automation operational by emitting backend webhooks to n8n, persisting delivery attempts/results, and exposing delivery status to staff workflows.

Current production-relevant artifacts are:

- n8n deployment in `docker-compose.production.yml`.
- Workflow records and exports in `docs/operations/n8n-workflows.md` and `docs/operations/n8n-workflows/`.
- Notification delivery persistence in the API.
- Telegram opt-in token consumption in `apps/telegram-bot`.
- Smoke-test hooks for configured n8n webhook checks.

Source-of-truth service-request state remains in the ServiceOps API and PostgreSQL. n8n can automate delivery and operational routing, but it must not own lifecycle status, staff identity, customer answers, inventory counts, or repair decisions.

## Phase 20 Daily Report Payload Boundary

Phase 20 exposes owner daily report data through the protected ServiceOps API only. The payload summarizes owner dashboard metrics, SLA risks, and low-stock risk so Phase 21 can build n8n owner reports and reminders from an API source of truth.

Phase 20 does not send owner reports, SLA reminders, red alerts, or low-stock alerts. n8n automation remains responsible only after Phase 21, and it must continue to treat ServiceOps API data as read-only operational input rather than owning request lifecycle, staff identity, inventory quantities, or repair decisions.
