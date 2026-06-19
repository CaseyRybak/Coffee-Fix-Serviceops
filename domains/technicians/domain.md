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

Technician actions append service-request status events with actor `technician`. This slice did not create full technician profiles, availability calendars, automatic matching, technician-owned rescheduling controls, or mobile push notifications. Dispatcher-owned structured rescheduling arrives in the Phase 15 scheduling boundary below.

## Phase 15 Schedule Visibility

Phase 15 adds technician-visible structured appointment timing. The technician workspace can show assigned service requests and a schedule-oriented list for the authenticated technician.

Technician identity:

- Scheduling uses the staff username as the technician identifier.
- Existing assignment matching still uses `assigned_technician_name`, now populated with the technician identifier when a structured appointment is created.
- Dispatcher candidate selection reads active staff accounts with the `technician` role. Candidates expose staff display name, username, and phone. Phase 23 Lite adds profile-backed region and skill data for recommendation flows.

Capacity assumption:

- A technician can have only one active scheduled appointment in an overlapping time window.
- Cancelled or rescheduled historical appointments do not count against capacity.

Technician boundary:

- Technicians can see appointment timing and reschedule/cancel effects.
- Technicians cannot create, reschedule, or cancel appointments in Phase 15; those actions remain dispatcher-owned.

## Phase 16 Reserved Parts Consumption

Technician parts usage now cooperates with inventory reservations. When a technician records parts used for an assigned request, the inventory domain consumes any active reservation for the same request and part before using unreserved available stock.

Technician catalog access is read-only. The technician workspace can load the parts catalog, show available/reserved stock context, and let the technician select a catalog part by SKU/name before recording usage. Catalog creation, duplicate control, compatibility metadata, stock adjustment, and reservation creation/release remain inventory-owned.

## Phase 23 Lite Recommendation Foundation

Phase 23 was intentionally scoped to a lightweight profile and recommendation foundation for the portfolio MVP. A technician profile is linked to an existing staff account with the `technician` role and stores only:

- whether the technician participates in recommendations;
- brand skills;
- service regions;
- an optional internal note.

Dispatcher recommendations are deterministic and explainable. They rank technicians using active staff/profile state, brand match, region match, scheduled workload, and optional appointment-window conflict checks. Recommendations return reasons and risks for dispatcher review, but they never assign technicians or create appointments.

## Phase 24 Assistant Consumption Boundary

The staff assistant can consume backend-owned technician recommendations for authorized staff. Assistant answers may summarize recommendation reasons and risks, but they must not assign technicians, create appointments, override scheduling conflicts, or expose technician private notes.

Still deferred: GPS, route optimization, ratings, payroll, durable availability calendars, automatic assignment, and AI-owned technician assignment decisions.
