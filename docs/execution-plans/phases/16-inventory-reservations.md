# Phase 16: Inventory Reservations

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Connect inventory basics to service execution through part reservations, stock movement history, and low-stock visibility.

## Context To Read

- `domains/inventory/AGENTS.md`
- `domains/technicians/AGENTS.md`
- `domains/service-requests/domain.md`
- `docs/execution-plans/phases/08-technician-and-inventory.md`
- `docs/execution-plans/phases/15-scheduling-depth.md`

## Deliverables

- Part reservation model tied to service requests or scheduled visits.
- Reservation create, adjust, release, and consume workflows.
- Stock movement history for reservation, release, consumption, and manual adjustment.
- Compatibility hints for machine model and part selection where existing data supports it.
- Low-stock visibility for inventory staff and dispatchers.
- Tests covering reservation consistency, stock movement records, authorization, and technician parts usage.

## Acceptance Criteria

- Staff can reserve parts for a request or visit without immediately consuming stock.
- Technician parts usage can consume reserved parts and record final stock movement.
- Releasing or changing a reservation restores available stock correctly.
- Inventory views distinguish on-hand, reserved, and available quantities.
- Low-stock indicators are visible without blocking normal service workflows.
- Public customer status snapshots do not expose inventory metadata.
- `project_notes.md` returns to backlog grooming or identifies the next approved phase after implementation.

## Subagent Review Gate

Review inventory consistency, stock movement auditability, reservation edge cases, role protection, and whether technician workflows remain simple enough for mobile use.
