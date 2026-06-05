# Notifications Domain

## Responsibility

This domain handles Telegram, n8n webhooks, and later other delivery channels.

## First Use Cases

- Link Telegram chat to request.
- Send request-created notification.
- Send status-changed notification.
- Receive customer answer to clarification question.

## Phase 03 Telegram Opt-In Contract

Phase 03 defines the first backend contract for Telegram notification opt-in without sending messages yet.

- `POST /service-requests/{request_number}/telegram-opt-in` accepts an optional Telegram handle.
- The API returns the request number, saved Telegram handle, one-time token, and a bot deep link shaped as `https://t.me/coffeefix_service_bot?start=<token>`.
- The token links a future Telegram chat to a service request after the bot receives `/start <token>`.
- Actual bot-side token consumption and outbound status notifications remain deferred to a later notification/Telegram slice.

Customer clarification answers are recorded through the service-request API because the question belongs to the repair lifecycle. Notifications can later subscribe to those events for Telegram or n8n delivery.
