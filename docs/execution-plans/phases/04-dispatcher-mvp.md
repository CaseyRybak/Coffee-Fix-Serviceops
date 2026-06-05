# Phase 04: Dispatcher MVP

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Create the first internal dispatcher workflow for triage, status updates, clarification, and manual technician assignment.

Before implementation, use the detailed plan at `docs/execution-plans/detailed/04-dispatcher-mvp-implementation.md`.

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

## Scope Boundaries

- Dispatcher fields are internal. Public status responses must not expose internal notes, technician phone numbers, dispatcher-only assignment metadata, or raw database IDs.
- Phase 04 stores manual assignment metadata on the service request; it does not implement automatic matching, technician availability, mobile technician workflows, or appointment confirmation.
- Authentication is deferred. Dispatcher routes are acceptable for localhost MVP development only and require an access gate before public deployment.
- Status updates must use the existing service-request status vocabulary documented in `domains/service-requests/domain.md`.

## Acceptance Criteria

- Dispatcher can see incoming requests.
- Dispatcher can update status.
- Dispatcher can ask a clarification question visible on client status page.
- Dispatcher can assign a technician manually.
- Assignment and status changes create status events.
- Internal notes are visible in dispatcher detail and absent from public status snapshots.
- Visit window and assignment metadata are persisted in both sqlite test persistence and PostgreSQL Docker Compose persistence.
- Tests cover dispatcher use cases.
- `project_notes.md` identifies Phase 05 as the next active phase.

## Subagent Review Gate

Review operations fit, status lifecycle integrity, domain separation, and whether internal notes remain separate from customer-visible messages.
