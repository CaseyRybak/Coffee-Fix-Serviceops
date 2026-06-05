---
name: telegram-serviceops-flows
description: Use when adding Telegram bot flows for request linking, status notifications, customer clarification answers, dispatcher alerts, or technician notifications.
---

# Telegram ServiceOps Flows

## Context To Open

- `domains/notifications/AGENTS.md`
- `domains/notifications/domain.md`
- `domains/service-requests/domain.md`
- Phase 03 or Phase 08 plan.

## Pattern

Telegram is a notification and lightweight interaction channel. The backend remains the source of truth. Bot handlers should call backend use cases or API contracts rather than owning repair state.

## Flow Types

- Link chat to request.
- Send request created notification.
- Send status changed notification.
- Show current status.
- Capture answer to clarification question.

## Message Style

Use practical service language: request number, current status, next action, and contact option. Keep operational facts separate from AI-generated drafts unless a human has approved the message.
