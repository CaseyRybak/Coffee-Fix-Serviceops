# Phase 20 Owner Dashboard And SLA Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add internal SLA calculations, owner/admin dashboard metrics, and a daily report payload for later n8n automation.

**Architecture:** Keep SLA as a derived domain policy from request urgency, status, and creation time. Expose dashboard data through a new protected API module that reads service requests and inventory snapshots without changing public status contracts. Add a compact admin-facing React dashboard using the Phase 19 workspace split.

**Tech Stack:** FastAPI, Pydantic, sqlite/PostgreSQL repositories, React/Vite, Vitest, pytest.

---

### Task 1: SLA Policy

**Files:**
- Create: `apps/api/src/serviceops_api/owner_dashboard/__init__.py`
- Create: `apps/api/src/serviceops_api/owner_dashboard/models.py`
- Create: `apps/api/src/serviceops_api/owner_dashboard/sla.py`
- Test: `apps/api/tests/test_owner_dashboard.py`

- [ ] Write failing pytest coverage for `today`, `one_two_days`, and `planned` request deadlines, near-deadline state, overdue state, and terminal statuses.
- [ ] Run `cd apps/api && uv run --extra dev pytest tests/test_owner_dashboard.py -q` and confirm the SLA imports fail.
- [ ] Implement `SlaSnapshot` and `calculate_sla_snapshot()` with documented thresholds:
  - `today`: due 8 hours after creation, near-deadline within 2 hours.
  - `one_two_days`: due 48 hours after creation, near-deadline within 8 hours.
  - `planned`: due 120 hours after creation, near-deadline within 24 hours.
  - `completed`, `closed`, `cancelled`, and `warranty_case` are inactive for SLA.
- [ ] Re-run the focused pytest command and confirm the SLA tests pass.

### Task 2: Dashboard Aggregation API

**Files:**
- Create: `apps/api/src/serviceops_api/owner_dashboard/api.py`
- Create: `apps/api/src/serviceops_api/owner_dashboard/use_cases.py`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Test: `apps/api/tests/test_owner_dashboard.py`

- [ ] Add failing tests for `GET /owner/dashboard` and `GET /owner/daily-report`: admin succeeds, public/no-token is rejected, technician-only is forbidden, and public status responses do not contain SLA/dashboard keys.
- [ ] Add failing tests for counts: new, in progress, waiting for parts, completed, overdue, near deadline, technician workload, top issue groups, and low-stock risk.
- [ ] Add a repository read method returning internal dashboard rows with request number, status, urgency, created timestamp, problem, brand/model, customer name, assignment, and latest event title.
- [ ] Add aggregation use cases that calculate SLA snapshots, summarize metrics, include risk request rows, and build a deterministic daily report payload.
- [ ] Register a protected router under `/owner`, using `require_staff_role("admin", authenticator)`.
- [ ] Re-run focused API tests.

### Task 3: Owner Dashboard Web Surface

**Files:**
- Create: `apps/web/src/features/owner/OwnerDashboardPage.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/features/staff-auth/StaffWorkspacePage.tsx`
- Modify: `apps/web/src/shared/api.ts`
- Modify: `apps/web/src/shared/types.ts`
- Modify: `apps/web/src/styles.css`
- Test: `apps/web/src/App.test.tsx`

- [ ] Add failing Vitest coverage for the `/owner` route, admin workspace card, protected redirect behavior, dashboard fetch path, and rendering of SLA/risk metrics.
- [ ] Add shared API path builders and TypeScript response types for owner dashboard and daily report.
- [ ] Implement `ProtectedOwnerDashboardPage` with admin-only session handling matching existing protected workspaces.
- [ ] Render dense operational metrics, SLA risk rows, technician workload, top issue groups, and low-stock risk without exposing this surface in public navigation.
- [ ] Add CSS using the existing staff workspace visual language, with compact dashboard panels and responsive grids.
- [ ] Re-run focused web tests.

### Task 4: Documentation And Review Readiness

**Files:**
- Modify: `domains/service-requests/domain.md`
- Modify: `domains/notifications/domain.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-20-review.md` after implementation review is available.

- [ ] Document SLA rules and the public/private dashboard boundary.
- [ ] Document that Phase 20 daily report data is API-only and Phase 21 owns n8n sending.
- [ ] Update `project_notes.md` status and next steps only after implementation and verification.
- [ ] Run verification:
  - `cd apps/api && uv run --extra dev pytest tests/test_owner_dashboard.py`
  - `npm run web:test`
  - `npm run web:lint`
  - `npm run web:build`
  - `python3 tools/repo-checks/check_docs.py`
- [ ] Request independent review using `docs/review/subagent-review-protocol.md`.
