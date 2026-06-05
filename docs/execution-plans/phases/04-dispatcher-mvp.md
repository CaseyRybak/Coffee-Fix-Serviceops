# Phase 04: Dispatcher MVP

> For agentic workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Create the first internal dispatcher workflow for triage, status updates, clarification, and manual technician assignment.

## Context To Read

- `domains/service-requests/AGENTS.md`
- `domains/technicians/AGENTS.md`
- `domains/scheduling/AGENTS.md`
- `docs/product/mvp-scope.md`

## Deliverables

- Dispatcher request list.
- Request detail card.
- Status transition actions.
- Clarification question creation.
- Technician list and manual assignment.
- Visit window field.
- Internal notes field.

## Acceptance Criteria

- Dispatcher can see incoming requests.
- Dispatcher can update status.
- Dispatcher can ask a clarification question visible on client status page.
- Dispatcher can assign a technician manually.
- Assignment and status changes create status events.
- Tests cover dispatcher use cases.
- `project_notes.md` identifies Phase 05 as the next active phase.

## Subagent Review Gate

Review operations fit, status lifecycle integrity, domain separation, and whether internal notes remain separate from customer-visible messages.
