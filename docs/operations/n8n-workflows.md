# n8n Workflows

n8n automates delivery and operational routing around backend events. It does not own service-request state, staff identity, customer answers, inventory counts, or repair lifecycle transitions. Source-of-truth state remains in the ServiceOps API and PostgreSQL.

## Shared Webhook Rules

- Each webhook receives a shared secret header matching `SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET`.
- Webhook inputs should include `event_id`, `event_type`, `occurred_at`, `request_number`, and a public-safe payload.
- n8n retries delivery tasks where the downstream channel supports retry.
- Backend callback is used only for delivery outcome records in a future slice; it must not mutate repair status.

## New Request Dispatcher Alert

Trigger: ServiceOps sends a `service_request.created` webhook after request intake.

Input fields:

- `event_id`
- `request_number`
- `customer_name`
- `customer_phone_masked`
- `machine_brand`
- `machine_model`
- `urgency`
- `status_url`

Steps:

1. Validate shared secret.
2. Format a dispatcher alert message.
3. Send to the dispatcher operations channel.
4. Record n8n execution status.

Output: dispatcher receives a new-request alert with a link to the dispatcher workspace.

Retry behavior: retry channel delivery up to the n8n workflow retry limit, then surface the failed execution in n8n.

Backend callback: none in Phase 10.

## Status Changed Customer Notification

Trigger: ServiceOps sends a `service_request.status_changed` webhook after a dispatcher or technician status event.

Input fields:

- `event_id`
- `request_number`
- `public_token`
- `customer_name`
- `telegram_handle`
- `new_status`
- `public_status_url`

Steps:

1. Validate shared secret.
2. Choose customer-safe message text based on `new_status`.
3. Send Telegram notification when the customer opted in.
4. Fall back to the configured manual follow-up channel when Telegram is unavailable.
5. Record n8n execution status.

Output: customer receives a public-safe status notification with the status link.

Retry behavior: retry Telegram delivery for transient channel failures; do not retry invalid opt-in data without operator review.

Backend callback: future delivery-result callback only.

## Awaiting Clarification Reminder

Trigger: scheduled n8n workflow runs every business morning.

Input fields:

- API base URL
- staff service token or future operations token
- maximum age for unanswered clarification questions

Steps:

1. Query a future ServiceOps operations endpoint for requests awaiting clarification.
2. Filter requests older than the configured reminder age.
3. Send customer reminder through the opted-in channel.
4. Send dispatcher summary for requests without customer contact.

Output: customers receive reminders; dispatchers receive an exception list.

Retry behavior: retry individual message delivery; do not re-run the full batch automatically after partial success without idempotency keys.

Backend callback: future delivery-result callback only.

## Daily Operations Summary

Trigger: scheduled n8n workflow runs once per business day.

Input fields:

- API base URL
- staff service token or future operations token
- reporting date

Steps:

1. Query future reporting endpoints for open requests, awaiting customer replies, assigned technician visits, and low-stock parts.
2. Format a daily summary.
3. Send to the operations channel.
4. Keep the execution result in n8n history.

Output: operations team receives one daily summary.

Retry behavior: retry operations-channel delivery once; failed summaries remain visible in n8n executions.

Backend callback: none.
