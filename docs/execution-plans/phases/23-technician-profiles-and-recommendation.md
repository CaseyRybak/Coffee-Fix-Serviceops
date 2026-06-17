# Phase 23: Technician Profiles And Recommendation

> For implementation workers: create a detailed implementation plan before changing code, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Add richer technician profiles and explainable technician recommendation logic.

## Why This Phase Exists

Scheduling currently uses staff accounts and usernames as technician identifiers. The original platform direction called for technician skills, regions, availability, workload, and recommendation reasoning. This phase creates the domain foundation needed before AI can safely recommend technicians.

## Context To Read

- `docs/execution-plans/roadmap-after-phase-16.md`
- `domains/technicians/AGENTS.md`
- `domains/technicians/domain.md`
- `domains/scheduling/domain.md`
- `domains/service-requests/domain.md`
- `domains/inventory/domain.md`
- `apps/api/src/serviceops_api/technicians/`
- `apps/api/src/serviceops_api/scheduling/`
- `apps/api/src/serviceops_api/staff_management/`
- `apps/web/src/`

## Deliverables

- Technician profile model linked to a staff account.
- Technician skills/specializations, service regions, active flag, and optional workload metadata.
- Dispatcher-visible technician profile management or admin-visible profile editing, depending on detailed plan.
- Recommendation query that ranks technicians using documented rules such as skill match, region match, active workload, appointment availability, and part readiness.
- Recommendation explanation that shows why a technician was suggested and what risks remain.
- Dispatcher UI surface for viewing recommendations while preserving manual confirmation.
- Tests for ranking, explanation, authorization, scheduling conflicts, and profile lifecycle.
- Documentation updates for technician-profile and recommendation boundaries.

## Scope Boundaries

- This phase does not automatically assign technicians.
- This phase does not implement GPS, route optimization, maps, mobile push, rating algorithms, payroll, or complex durable availability calendars.
- AI may summarize recommendation reasoning later, but this phase should keep the recommendation engine explainable and deterministic.
- Public status snapshots must not expose technician profile internals, private phone numbers, workload diagnostics, or recommendation reasoning.

## Acceptance Criteria

- Admin or authorized staff can maintain technician profiles.
- Dispatcher can request recommended technicians for a service request.
- Recommendations include a clear explanation and risk notes.
- Manual dispatcher assignment remains the only way to confirm assignment.
- Recommendation logic respects existing scheduling capacity rules.
- Tests cover deterministic ordering and key mismatch cases such as wrong region, inactive technician, and scheduling conflict.

## Subagent Review Gate

Review recommendation explainability, deterministic behavior, staff identity links, scheduling integration, authorization, and whether the design avoids hidden automatic assignment.
