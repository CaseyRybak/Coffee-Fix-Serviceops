---
name: n8n-automation-design
description: Use when designing n8n workflows for CoffeeFix Pro request events, notifications, reminders, webhooks, or external service automation.
---

# n8n Automation Design

## Context To Open

- `domains/notifications/AGENTS.md`
- `domains/notifications/domain.md`
- `docs/architecture/tech-stack.md`
- Relevant phase plan.

## Pattern

n8n automates around backend events. It does not own business state. Backend events trigger webhooks; n8n performs delivery, reminders, or external integration and reports outcomes when needed.

## Useful Workflows

- New request dispatcher alert.
- Status changed customer notification.
- Reminder for requests awaiting clarification.
- B2B email notification.
- Daily operations summary.

## Design Record

Document each workflow with trigger, inputs, steps, outputs, retry behavior, and backend callback if any.

