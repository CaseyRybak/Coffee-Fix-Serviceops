# Phase 22 Procurement Lite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not create commits unless the user explicitly asks for commits in the current conversation turn.

**Goal:** Add a lightweight internal procurement workflow that turns low-stock inventory signals into supplier-backed purchase requests, approvals, ordering, and stock receiving.

**Architecture:** Keep procurement inside the inventory domain as a bounded internal workflow. Add suppliers, purchase requests, and purchase request items to the existing inventory repository/API surface, reuse stock movement audit records for receiving, and protect all write paths with staff RBAC. The public service-request/status contract remains unchanged; n8n and AI do not own purchase decisions.

**Tech Stack:** FastAPI, Pydantic, sqlite/PostgreSQL repositories, hand-written SQL migrations, React/Vite, Vitest, pytest, repository docs checks.

**Completion Note:** Implemented in the Phase 22 working tree. Verification and subagent audit outcomes are recorded in `docs/review/phase-22-review.md`.

---

### Task 1: Procurement Domain Models And Repository

**Files:**
- Modify: `apps/api/src/serviceops_api/inventory/models.py`
- Modify: `apps/api/src/serviceops_api/inventory/repository.py`
- Create: `apps/api/src/serviceops_api/migrations/0013_procurement_lite.sql`
- Test: `apps/api/tests/test_inventory_procurement.py`

- [ ] Write failing pytest coverage for supplier creation/listing and purchase request creation with line items.
- [ ] Write failing pytest coverage for valid purchase statuses: `draft`, `pending_approval`, `approved`, `ordered`, `received`, and `cancelled`.
- [ ] Write failing pytest coverage that draft item edits are allowed only while the request is `draft`.
- [ ] Implement Pydantic payload/record models for suppliers, purchase requests, purchase request items, status action payloads, and low-stock draft creation.
- [ ] Extend the `InventoryStore` protocol with procurement methods.
- [ ] Add sqlite tables during repository initialization.
- [ ] Add PostgreSQL migration `0013_procurement_lite.sql`.
- [ ] Add sqlite and PostgreSQL repository methods for supplier CRUD-lite, purchase request create/list/detail, draft item replacement, and state transitions.
- [ ] Re-run `cd apps/api && uv run --extra dev pytest tests/test_inventory_procurement.py -q`.

### Task 2: Procurement State Machine, Receiving, And Low-Stock Drafts

**Files:**
- Modify: `apps/api/src/serviceops_api/inventory/use_cases.py`
- Modify: `apps/api/src/serviceops_api/inventory/repository.py`
- Test: `apps/api/tests/test_inventory_procurement.py`

- [ ] Write failing pytest coverage for state transitions:
  - `draft -> pending_approval`
  - `pending_approval -> approved`
  - `approved -> ordered`
  - `draft|pending_approval|approved|ordered -> cancelled`
  - `ordered -> received`
- [ ] Write failing pytest coverage that invalid transitions return a domain error and do not mutate state.
- [ ] Write failing pytest coverage that receiving increments `quantity_on_hand` and creates auditable `stock_movements` rows with `movement_type = procurement_receipt`.
- [ ] Write failing pytest coverage that cancelled requests never change stock.
- [ ] Write failing pytest coverage that low-stock draft creation includes only low-stock parts and chooses a simple reorder quantity from threshold/available gap.
- [ ] Add a `procurement_receipt` stock movement type.
- [ ] Add use case classes for creating/listing suppliers, purchase requests, draft item edits, status submission/approval/ordering/cancellation, receiving, and low-stock draft creation.
- [ ] Keep procurement notes/internal data out of public service request snapshots by not touching public DTOs.
- [ ] Re-run focused procurement and inventory tests.

### Task 3: Protected Procurement API

**Files:**
- Modify: `apps/api/src/serviceops_api/inventory/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Test: `apps/api/tests/test_inventory_procurement.py`

- [ ] Write failing API tests for:
  - inventory staff can create suppliers and draft purchase requests.
  - inventory staff can submit, mark ordered, receive, cancel, and create low-stock drafts.
  - admin can approve purchase requests.
  - dispatcher/technician/public requests are rejected for procurement writes.
  - public status snapshots do not contain supplier, purchase request, price, stock, or procurement fields.
- [ ] Register procurement routes under `/inventory/procurement/*`.
- [ ] Use inventory-role dependency for supplier/draft/order/receive/cancel workflows.
- [ ] Use admin-role dependency for approval.
- [ ] Use admin-or-inventory read dependency for procurement list/detail reads.
- [ ] Map duplicate/not-found/invalid-transition/stock errors to explicit HTTP statuses.
- [ ] Re-run focused API tests.

### Task 4: Staff-Facing Procurement UI

**Files:**
- Modify: `apps/web/src/shared/api.ts`
- Modify: `apps/web/src/shared/types.ts`
- Modify: `apps/web/src/features/inventory/InventoryPage.tsx`
- Modify: `apps/web/src/styles.css`
- Test: `apps/web/src/App.test.tsx`

- [ ] Add failing Vitest coverage for procurement path builders, inventory page procurement loading, low-stock draft action, supplier form, purchase request list rendering, and admin-only approval affordance.
- [ ] Add shared TypeScript types for suppliers, purchase requests, purchase items, and status payloads.
- [ ] Add shared API path builders for `/inventory/procurement/suppliers`, `/purchase-requests`, low-stock draft, draft items, submit, approve, mark-ordered, receive, and cancel.
- [ ] Extend `InventoryPage` with a compact procurement section matching the existing operational workspace style.
- [ ] Add forms for supplier creation, draft purchase request creation, draft line editing, and low-stock draft creation.
- [ ] Add status action buttons gated by session role:
  - inventory: submit, mark ordered, receive, cancel.
  - admin: approve.
- [ ] Keep text compact and operational; do not expose procurement in public navigation.
- [ ] Re-run focused web tests.

### Task 5: Documentation, Review Artifact, And Project Dashboard

**Files:**
- Modify: `domains/inventory/domain.md`
- Modify: `domains/service-requests/domain.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-22-review.md`

- [ ] Document Phase 22 procurement boundaries, statuses, receiving stock movement behavior, role rules, and low-stock draft behavior.
- [ ] Reaffirm that public status snapshots do not expose suppliers, purchase requests, prices, stock levels, movement history, or procurement notes.
- [ ] Update `project_notes.md` after implementation and verification to mark Phase 22 complete and move active focus toward Phase 23.
- [ ] Create `docs/review/phase-22-review.md` after independent review is available, including reviewer role, files reviewed, verification commands, findings, and final recommendation.

### Task 6: Verification And Independent Audit

**Files:**
- No production files unless verification or reviewers require fixes.

- [ ] Run `cd apps/api && uv run --extra dev pytest tests/test_inventory_procurement.py tests/test_inventory_parts.py`.
- [ ] Run `cd apps/api && uv run --extra dev pytest`.
- [ ] Run `npm run web:test`.
- [ ] Run `npm run web:lint`.
- [ ] Run `npm run web:build`.
- [ ] Run `python3 tools/repo-checks/check_docs.py`.
- [ ] Run subagent audit for plan compliance, procurement state transitions, inventory consistency, authorization, public/private separation, stock movement auditability, frontend behavior, and documentation.
- [ ] Fix blocking or important audit findings.
- [ ] Re-run focused verification after fixes.
