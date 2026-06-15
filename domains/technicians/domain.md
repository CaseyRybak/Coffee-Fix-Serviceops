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

## Phase 15 Schedule Visibility

Phase 15 adds technician-visible structured appointment timing. The technician workspace can show assigned service requests and a schedule-oriented list for the authenticated technician.

Technician identity:

- Scheduling uses the staff username as the technician identifier.
- Existing assignment matching still uses `assigned_technician_name`, now populated with the technician identifier when a structured appointment is created.

Capacity assumption:

- A technician can have only one active scheduled appointment in an overlapping time window.
- Cancelled or rescheduled historical appointments do not count against capacity.

Technician boundary:

- Technicians can see appointment timing and reschedule/cancel effects.
- Technicians cannot create, reschedule, or cancel appointments in Phase 15; those actions remain dispatcher-owned.

## Phase 16 Reserved Parts Consumption

Technician parts usage now cooperates with inventory reservations. When a technician records parts used for an assigned request, the inventory domain consumes any active reservation for the same request and part before using unreserved available stock.

Technician catalog access is read-only. The technician workspace can load the parts catalog, show available/reserved stock context, and let the technician select a catalog part by SKU/name before recording usage. Catalog creation, duplicate control, compatibility metadata, stock adjustment, and reservation creation/release remain inventory-owned.
