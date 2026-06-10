# Phase 15: Scheduling Depth

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Turn assigned technician visits into a more practical scheduling workflow for dispatchers and technicians.

## Context To Read

- `domains/scheduling/AGENTS.md`
- `domains/technicians/AGENTS.md`
- `domains/service-requests/domain.md`
- `docs/execution-plans/phases/04-dispatcher-mvp.md`
- `docs/execution-plans/phases/08-technician-and-inventory.md`

## Deliverables

- Appointment window model and persistence.
- Dispatcher scheduling and rescheduling actions.
- Technician availability or capacity rules for basic assignment decisions.
- Staff-facing schedule list or calendar-oriented view.
- Technician-visible appointment timing and reschedule state.
- Request timeline entries for scheduling changes.
- Tests covering appointment creation, rescheduling, cancellation, role protection, and request status history.

## Acceptance Criteria

- Dispatcher can create, change, and cancel appointment windows for eligible service requests.
- Technician worklists reflect appointment timing and reschedule/cancel changes.
- The system prevents scheduling actions that conflict with request lifecycle rules.
- Scheduling changes are visible in internal request history and customer-safe status snapshots where appropriate.
- Role-protected scheduling APIs reject public and unauthorized staff access.
- `project_notes.md` identifies Phase 16 as the next active phase after implementation.

## Subagent Review Gate

Review scheduling lifecycle consistency, technician workflow fit, dispatcher ergonomics, authorization boundaries, and whether public status details stay customer-safe.
