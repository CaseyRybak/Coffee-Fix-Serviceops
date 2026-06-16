# Scheduling Domain

## Responsibility

This domain coordinates customer preferences and technician availability into a confirmed visit window.

## First Use Cases

- Store preferred visit time from intake.
- Create scheduled appointment.
- Update appointment window.
- Publish schedule change event.

## Phase 04 Boundary

Phase 04 stores a dispatcher-entered visit window as request metadata so the client timeline and dispatcher card can reflect the next operational step. Confirmed appointments, technician availability, rescheduling rules, and schedule-change events remain later scheduling-domain work.

## Phase 08 Boundary

Phase 08 reuses the dispatcher-entered visit window for technician assigned-visit lists. Scheduling still does not own a calendar engine, availability matching, confirmed appointment lifecycle, rescheduling workflow, or schedule-change notifications.

## Phase 15 Scheduling Depth

Phase 15 introduces structured appointment windows in addition to the legacy dispatcher `visit_window` text. Dispatchers can create, reschedule, and cancel appointments for eligible service requests through protected scheduling APIs and a staff schedule view.

Appointment lifecycle states:

- `scheduled`: the active confirmed appointment.
- `rescheduled`: a historical appointment superseded by a newer scheduled appointment.
- `cancelled`: an appointment cancelled by dispatch, with no active visit unless a later appointment is created.

Capacity rule:

- One technician can have only one active `scheduled` appointment for overlapping time windows.
- Cancelled and historical rescheduled rows do not block capacity.
- PostgreSQL enforces active appointment overlap with an exclusion constraint. Application checks still return early for normal conflicts, and PostgreSQL exclusion/unique/deadlock errors are mapped to dispatcher-safe scheduling conflicts.

Scheduling status rules:

- Creating appointments is allowed for `new`, `needs_clarification`, `awaiting_assignment`, `technician_assigned`, and `visit_scheduled`.
- Creating appointments is blocked once a visit is in diagnostics, repair, waiting-for-parts, completed, closed, warranty, or cancelled states.
- Rescheduling and cancellation are blocked for terminal request statuses.
- Rescheduling or cancelling after technician work has started may update the active appointment/window, but it must preserve the current service-request lifecycle status such as `diagnostics`, `waiting_for_parts`, or `repair_in_progress`.

Public/private boundary:

- Public status snapshots may show customer-safe appointment timing and schedule-change timeline events.
- Public status snapshots must not expose appointment ids, technician phone numbers, internal reasons, capacity diagnostics, staff audit data, AI data, or internal notes.

Still deferred:

- Automatic route optimization.
- Customer self-scheduling.
- Calendar engine integrations.
- Appointment-change notification automation beyond normal request status events.
