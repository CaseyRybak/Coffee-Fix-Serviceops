# Phase 23 Lite Technician Recommendation Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small, deterministic technician profile and recommendation foundation without automatic assignment or a heavy technician-management subsystem.

**Completion note:** Phase 23 Lite was implemented and reviewed in `docs/review/phase-23-review.md`. The checkboxes below are preserved as the original execution plan rather than rewritten as a completion log.

**Architecture:** Technician profiles live as a thin domain table keyed by staff username. Admins maintain active flag, brand skills, and service regions; dispatchers request ranked recommendations for a service request and receive human-readable reasons and risks. Existing manual dispatcher assignment and structured scheduling remain the only mutation paths for assigning visits.

**Tech Stack:** FastAPI, Pydantic, sqlite/PostgreSQL repositories with SQL migrations, React/Vite/TypeScript, Vitest/Testing Library.

---

## File Structure

- Create `apps/api/src/serviceops_api/migrations/0014_technician_profiles.sql`: PostgreSQL table for technician profiles.
- Create `apps/api/src/serviceops_api/technicians/repository.py`: sqlite/PostgreSQL profile persistence, including migration initialization.
- Modify `apps/api/src/serviceops_api/technicians/models.py`: profile payloads, snapshots, recommendation DTOs.
- Modify `apps/api/src/serviceops_api/technicians/use_cases.py`: profile lifecycle use cases and deterministic recommendation ranking.
- Modify `apps/api/src/serviceops_api/technicians/api.py`: admin profile routes and dispatcher recommendation route.
- Modify `apps/api/src/serviceops_api/main.py`: wire technician profile repository and routes.
- Modify `apps/api/src/serviceops_api/service_requests/repository.py`: expose request recommendation context and scheduling/workload signals.
- Test `apps/api/tests/test_technician_profiles.py`: profile lifecycle, authorization, recommendations, conflicts, and public boundary.
- Modify `domains/technicians/domain.md`, `domains/service-requests/domain.md`, and phase docs to record the Lite boundary.
- Modify `apps/web/src/shared/api.ts` and `apps/web/src/shared/types.ts`: frontend path builders and DTOs.
- Modify `apps/web/src/features/admin/AdminPage.tsx`: compact technician-profile editor for staff with technician role.
- Modify `apps/web/src/features/dispatcher/DispatcherPage.tsx`: recommendation panel in dispatcher detail.
- Modify `apps/web/src/App.test.tsx`: UI coverage for profile editing and recommendation display.

## Tasks

### Task 1: Backend RED Tests

**Files:**
- Create: `apps/api/tests/test_technician_profiles.py`

- [ ] Add tests that create admin, dispatcher, and technician staff accounts in an injected sqlite staff repository.
- [ ] Verify `GET /admin/technician-profiles` and `POST /admin/technician-profiles/{username}` require admin role.
- [ ] Verify admin can upsert a profile for a staff account with the technician role.
- [ ] Verify upsert rejects usernames that do not exist or do not have the technician role.
- [ ] Verify dispatcher recommendations rank an active technician with matching brand and region above mismatches.
- [ ] Verify inactive profiles remain visible as risk-bearing non-top recommendations, not hidden magic.
- [ ] Verify optional `starts_at` and `ends_at` query parameters add a scheduling conflict risk when the technician already has an overlapping active appointment.
- [ ] Verify public status snapshots do not expose profile skills, regions, workload, or recommendation reasons.

Run:

```bash
cd apps/api && uv run --extra dev pytest tests/test_technician_profiles.py -q
```

Expected before implementation: failures for missing routes/models.

### Task 2: Backend Profile Persistence

**Files:**
- Create: `apps/api/src/serviceops_api/migrations/0014_technician_profiles.sql`
- Create: `apps/api/src/serviceops_api/technicians/repository.py`
- Modify: `apps/api/src/serviceops_api/main.py`

- [ ] Add a `technician_profiles` table keyed by `staff_username`, with `active`, `skill_brands`, `service_regions`, `notes`, and timestamps.
- [ ] Implement sqlite persistence with JSON-encoded arrays and idempotent schema creation.
- [ ] Implement PostgreSQL persistence with jsonb arrays and migration initialization.
- [ ] Add repository factory selection from `SERVICEOPS_DATABASE_URL`.
- [ ] Inject an in-memory profile repository when tests inject other repositories.

Run:

```bash
cd apps/api && uv run --extra dev pytest tests/test_technician_profiles.py -q
```

Expected after Task 2 only: persistence methods exist, route/use-case failures remain.

### Task 3: Backend Profile API

**Files:**
- Modify: `apps/api/src/serviceops_api/technicians/models.py`
- Modify: `apps/api/src/serviceops_api/technicians/use_cases.py`
- Modify: `apps/api/src/serviceops_api/technicians/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`

- [ ] Add profile payload validation that trims strings, removes duplicates case-insensitively, and limits notes.
- [ ] Add list/upsert use cases that validate the linked staff account exists, is active/inactive independently, and has the technician role.
- [ ] Add admin routes:

```text
GET /admin/technician-profiles
POST /admin/technician-profiles/{username}
```

- [ ] Return staff display name and phone together with profile fields.
- [ ] Record a staff audit event `technician_profile.upserted` without raw notes.

Run:

```bash
cd apps/api && uv run --extra dev pytest tests/test_technician_profiles.py -q
```

Expected after Task 3: profile lifecycle and authorization tests pass; recommendation tests still fail.

### Task 4: Backend Recommendation Query

**Files:**
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/src/serviceops_api/technicians/models.py`
- Modify: `apps/api/src/serviceops_api/technicians/use_cases.py`
- Modify: `apps/api/src/serviceops_api/technicians/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`

- [ ] Add a service-request repository method that returns request number, machine brand/model, address, urgency, and status for recommendations.
- [ ] Add repository methods for active appointment count and optional overlap check by technician username.
- [ ] Rank only staff accounts with the `technician` role.
- [ ] Score matches with simple documented weights: active profile, brand match, region text match, no overlap, lower scheduled workload.
- [ ] Return explanation arrays: `reasons` for positive signals and `risks` for mismatches or missing data.
- [ ] Add dispatcher route:

```text
GET /dispatcher/service-requests/{request_number}/technician-recommendations?starts_at=...&ends_at=...
```

- [ ] Keep the route read-only; it must never call assignment or scheduling mutations.

Run:

```bash
cd apps/api && uv run --extra dev pytest tests/test_technician_profiles.py -q
```

Expected after Task 4: all backend Phase 23 Lite tests pass.

### Task 5: Frontend RED Tests

**Files:**
- Modify: `apps/web/src/App.test.tsx`

- [ ] Add a test that renders `AdminPage` with technician staff and profiles, edits brands/regions, and verifies the profile endpoint payload.
- [ ] Add a test that renders `DispatcherPage` with a selected request and recommendation response, then verifies reasons/risks are visible and selecting a recommendation fills manual assignment and appointment fields.

Run:

```bash
npm run web:test -- --run
```

Expected before frontend implementation: tests fail for missing UI text or missing path builders.

### Task 6: Frontend Implementation

**Files:**
- Modify: `apps/web/src/shared/api.ts`
- Modify: `apps/web/src/shared/types.ts`
- Modify: `apps/web/src/features/admin/AdminPage.tsx`
- Modify: `apps/web/src/features/dispatcher/DispatcherPage.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] Add API path builders and DTOs.
- [ ] Add a compact admin technician-profile panel that only appears for staff rows with the `technician` role.
- [ ] Add a dispatcher recommendation panel near assignment/scheduling controls.
- [ ] Use recommendations to prefill existing manual assignment and appointment fields; do not submit assignment automatically.
- [ ] Keep styling consistent with existing staff workspaces: dense, operational, no new landing-page patterns.

Run:

```bash
npm run web:test -- --run
npm run web:lint
```

Expected after Task 6: web tests and lint pass.

### Task 7: Documentation And Verification

**Files:**
- Modify: `project_notes.md`
- Modify: `domains/technicians/domain.md`
- Modify: `domains/service-requests/domain.md`
- Modify: `docs/execution-plans/phases/23-technician-profiles-and-recommendation.md`

- [ ] Document that Phase 23 was intentionally scoped to Lite.
- [ ] Document that public status snapshots remain free of technician-profile and recommendation internals.
- [ ] Document that AI and backend recommendation logic do not assign technicians.

Run:

```bash
python3 tools/repo-checks/check_docs.py
cd apps/api && uv run --extra dev pytest tests/test_technician_profiles.py tests/test_staff_management.py tests/test_dispatcher_requests.py tests/test_scheduling_workflow.py tests/test_service_request_status.py -q
npm run web:test -- --run
npm run web:lint
npm run web:build
```

Expected: all commands pass.

## Self-Review

- Scope is intentionally Lite: no GPS, route optimization, ratings, durable availability calendar, payroll, or automatic assignment.
- The plan keeps staff accounts as identity source and avoids duplicate login/profile ownership.
- The recommendation query is deterministic, explainable, and read-only.
- Public status boundaries are explicitly tested and documented.
- No commits are included in steps because repository policy requires direct user instruction before commit or push.
