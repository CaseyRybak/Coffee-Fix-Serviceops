# Phase 20: Owner Dashboard And SLA Foundation

> For implementation workers: create a detailed implementation plan before changing code, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Add the first owner-facing operational dashboard and SLA data foundation.

## Why This Phase Exists

The original platform direction included owner visibility, overdue work, daily reports, waiting-parts risk, technician workload, and operational insights. The current system has the underlying requests, scheduling, inventory, and technician actions, but it does not yet summarize them for the owner or compute SLA risk.

## Context To Read

- `docs/execution-plans/roadmap-after-phase-16.md`
- `domains/service-requests/domain.md`
- `domains/scheduling/domain.md`
- `domains/inventory/domain.md`
- `domains/technicians/domain.md`
- `domains/notifications/domain.md`
- `docs/product/vision.md`
- `docs/product/mvp-scope.md`
- `apps/api/src/serviceops_api/service_requests/`
- `apps/api/src/serviceops_api/scheduling/`
- `apps/api/src/serviceops_api/inventory/`
- `apps/api/src/serviceops_api/staff_auth.py`
- `apps/web/src/`

## Deliverables

- SLA model or derived SLA policy for service requests, including deadline, overdue state, and near-deadline state.
- Owner/admin dashboard API protected by staff roles.
- Dashboard metrics for new requests, in-progress requests, waiting-for-parts requests, completed requests, overdue requests, near-deadline requests, technician workload, top issue groups, and low-stock risk.
- Daily report API payload suitable for Phase 21 n8n owner reports.
- Owner/admin dashboard UI surface.
- Tests for SLA calculations, dashboard authorization, public/private data boundaries, and dashboard metrics.
- Documentation updates for SLA behavior and dashboard boundaries.

## Scope Boundaries

- This phase does not send notifications; Phase 21 automates reminders and owner reports.
- This phase does not implement procurement; it can show low-stock risk but should not create purchase requests.
- This phase does not implement AI owner recommendations. It may prepare structured data for later AI summaries.
- This phase does not implement billing or revenue metrics.
- Public status snapshots must not expose owner dashboard data, SLA diagnostics, staff workload, inventory quantities, or internal risk labels unless already customer-safe.

## Acceptance Criteria

- Owner/admin staff can view dashboard metrics through protected routes.
- Overdue and near-deadline requests are computed consistently from documented SLA rules.
- Waiting-for-parts and low-stock risks are visible internally.
- Daily report API is deterministic enough for n8n to consume later.
- Unauthorized users and public clients cannot access owner dashboard APIs.
- Tests cover key SLA edge cases and data safety boundaries.

## Subagent Review Gate

Review SLA rule clarity, data aggregation correctness, authorization, public/private separation, dashboard usefulness, and whether Phase 21 can build automation on the resulting API.
