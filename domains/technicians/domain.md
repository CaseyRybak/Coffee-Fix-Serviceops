# Technicians Domain

## Responsibility

This domain represents repair technicians and their ability to work specific brands, machine types, and regions.

## First Use Cases

- Create technician profile.
- Store brand specializations.
- Store service regions.
- Provide candidates for manual assignment.

## Phase 04 Boundary

Phase 04 records manual assignment metadata from the dispatcher workflow on the service request: technician name, optional phone, optional region, and optional visit window. It does not create a full technician directory, availability calendar, mobile technician workflow, or automatic matching engine.

## Phase 08 Technician Workflow

Phase 08 adds a protected technician workspace for staff with the `technician` role. A technician can see service requests assigned to their staff username, open request detail, record a diagnosis checklist, record a repair result, and mark parts used during the visit.

Technician actions append service-request status events with actor `technician`. This slice still does not create full technician profiles, availability calendars, automatic matching, rescheduling rules, or mobile push notifications.
