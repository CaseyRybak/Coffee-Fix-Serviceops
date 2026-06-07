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
