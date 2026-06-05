# Phase 02: Service Request Intake

> For agentic workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Implement the first end-to-end repair request flow from public form to persisted service request.

## Context To Read

- `domains/service-requests/AGENTS.md`
- `domains/service-requests/domain.md`
- `domains/customers/AGENTS.md`
- `domains/machines/AGENTS.md`
- `docs/product/figma-reference-review.md`

## Deliverables

- Service request domain model.
- Customer and machine intake models.
- API endpoint for creating a repair request.
- Request number generation.
- Database migration.
- Public form based on `reference/figma`, simplified for MVP.
- Success state showing request number.

## Acceptance Criteria

- A user can submit name, phone, optional Telegram, client type, brand, problem, address/district, urgency, and optional attachment metadata.
- API persists request, customer, and machine intake data.
- Response includes public request number.
- Tests cover successful intake and validation failures.
- `project_notes.md` identifies Phase 03 as the next active phase.

## Subagent Review Gate

Review domain boundaries, API schema clarity, persistence mapping, form fidelity to Figma reference, and validation behavior.
