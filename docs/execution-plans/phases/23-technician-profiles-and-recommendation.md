# Phase 23: Technician Profiles And Recommendation Lite

> For implementation workers: create a detailed implementation plan before changing code, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Add a lightweight technician profile and explainable technician recommendation foundation without turning the MVP into a full workforce-management system.

## Why This Phase Exists

Scheduling currently uses staff accounts and usernames as technician identifiers. The original platform direction called for technician skills, regions, availability, workload, and recommendation reasoning. For the portfolio MVP, this phase is intentionally scoped down to the smallest useful foundation needed before AI can safely discuss technician choices.

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
- Technician brand skills, service regions, active flag, and optional internal note.
- Admin-visible lightweight profile editing for staff with the `technician` role.
- Recommendation query that ranks technicians using documented rules such as brand match, region match, active profile/staff state, active appointment workload, and optional requested-window conflict checks.
- Recommendation explanation that shows why a technician was suggested and what risks remain.
- Dispatcher UI surface for viewing recommendations while preserving manual confirmation.
- Tests for ranking, explanation, authorization, scheduling conflicts, and profile lifecycle.
- Documentation updates for technician-profile and recommendation boundaries.

## Scope Boundaries

- This phase does not automatically assign technicians.
- This phase does not implement GPS, route optimization, maps, mobile push, rating algorithms, payroll, or complex durable availability calendars.
- This Lite scope does not implement part-readiness scoring or a full availability calendar.
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
