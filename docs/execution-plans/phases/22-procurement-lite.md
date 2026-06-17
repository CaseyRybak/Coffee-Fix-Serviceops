# Phase 22: Procurement Lite

> For implementation workers: create a detailed implementation plan before changing code, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Add a small procurement workflow that connects low stock and reservations to supplier purchase requests.

## Why This Phase Exists

Inventory reservations and low-stock visibility are implemented, but the original ServiceOps direction included purchase requests and supplier workflows. This phase adds procurement depth without building a full ERP.

## Context To Read

- `docs/execution-plans/roadmap-after-phase-16.md`
- `domains/inventory/AGENTS.md`
- `domains/inventory/domain.md`
- `domains/service-requests/domain.md`
- `docs/execution-plans/phases/16-inventory-reservations.md`
- Phase 20 and Phase 21 artifacts when available.
- `apps/api/src/serviceops_api/inventory/`
- `apps/web/src/`

## Deliverables

- Supplier model and persistence.
- Purchase request model with statuses: `draft`, `pending_approval`, `approved`, `ordered`, `received`, and `cancelled`.
- Purchase request items tied to inventory parts and quantities.
- Inventory staff workflow for creating, editing draft items, submitting for approval, marking ordered, receiving, and cancelling purchase requests.
- Owner/admin or inventory approval rule, depending on the detailed plan.
- Receiving workflow that creates stock movement records and updates on-hand stock.
- Low-stock-to-purchase-draft action.
- Staff-facing procurement UI.
- Tests for state transitions, authorization, stock receiving, movement records, and low-stock draft creation.
- Domain and operations documentation updates.

## Scope Boundaries

- This phase does not implement vendor billing, payments, invoices, fiscal documents, warranty accounting, barcode scanning, or multi-warehouse procurement.
- This phase does not let AI create approved purchase requests. AI may later create drafts only through Phase 24 confirmation rules.
- Public clients must not see suppliers, purchase requests, prices, stock levels, or procurement notes.
- n8n purchase approval buttons are not required in this phase unless explicitly included in the detailed plan; Phase 21 already owns operational n8n automation.

## Acceptance Criteria

- Staff can create a purchase request draft from low-stock parts.
- Staff can move a purchase request through documented statuses.
- Receiving a purchase request updates inventory stock and records an auditable stock movement.
- Authorization prevents public or wrong-role access.
- Cancelled purchase requests do not change stock.
- Procurement data remains absent from public status snapshots.

## Subagent Review Gate

Review procurement state transitions, inventory consistency, authorization, public/private separation, stock movement auditability, and whether the workflow stays lightweight enough for the project scope.
