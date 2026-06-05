# Phase 07: Technician And Inventory

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Add technician mobile workflow and basic parts tracking.

## Context To Read

- `domains/technicians/AGENTS.md`
- `domains/scheduling/AGENTS.md`
- `domains/inventory/AGENTS.md`
- `domains/service-requests/domain.md`

## Deliverables

- Technician mobile request list.
- Technician request detail.
- Diagnosis checklist.
- Repair result capture.
- Parts catalog basics.
- Stock count basics.
- Parts used on request.
- Status updates from technician workflow.

## Acceptance Criteria

- Technician can see assigned visits.
- Technician can record diagnosis and result.
- Technician can mark parts used.
- Request status updates reflect technician actions.
- Tests cover technician actions and inventory stock changes.
- `project_notes.md` identifies Phase 08 as the next active phase.

## Subagent Review Gate

Review mobile workflow practicality, inventory consistency, and whether technician actions produce clear request history.
