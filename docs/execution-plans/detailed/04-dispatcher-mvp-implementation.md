# Dispatcher MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first internal dispatcher workflow for listing requests, reviewing request details, changing status, asking clarification questions, and recording manual technician assignment intent.

**Architecture:** Extend the existing service-request slice first because it already owns lifecycle status, clarification questions, public status snapshots, and status events. Add a small internal dispatcher API contract over application use cases and repository ports, then add a dispatcher route in the React app that consumes those contracts. Keep technician and scheduling data deliberately lightweight in this phase: manual assignment stores dispatcher-selected technician metadata and visit-window text on the request, while full technician profiles, availability, and appointments remain later domain slices.

**Tech Stack:** Python, FastAPI, Pydantic, sqlite3, psycopg, PostgreSQL migration SQL, pytest, React, Vite, TypeScript, Node test runner through `tsx`.

---

## Scope Decisions

- Phase 04 is an internal MVP workflow, not a full back-office product.
- Dispatcher endpoints are API contracts under `/dispatcher/...`; public `/service-requests/.../status` responses must not expose internal notes, technician phone numbers, raw database IDs, or dispatcher-only fields.
- Authentication is still outside this slice. The local Docker Compose safety posture is localhost-only; deployment must add an access gate before exposing dispatcher routes on a public host.
- Technician assignment is manual and descriptive in this slice. Store selected technician name plus optional phone, region, and visit window. Do not implement automatic matching, technician availability, mobile technician workflows, or appointment confirmation.
- Status changes are limited to the statuses already defined in `RequestStatus`: `new`, `needs_clarification`, `awaiting_assignment`, `technician_assigned`, `visit_scheduled`, `diagnostics`, `waiting_for_parts`, `repair_in_progress`, `completed`, `closed`, `warranty_case`, and `cancelled`.
- Every dispatcher status change, clarification question, and assignment action must create a status event so the public timeline stays coherent.

## File Responsibility Map

- `apps/api/src/serviceops_api/service_requests/models.py`: dispatcher request/response DTOs, status-update payload, clarification payload, assignment payload, and internal-note payload.
- `apps/api/src/serviceops_api/service_requests/use_cases.py`: dispatcher use cases over the existing repository protocol.
- `apps/api/src/serviceops_api/service_requests/api.py`: internal dispatcher routes mounted beside the existing public service-request routes.
- `apps/api/src/serviceops_api/service_requests/repository.py`: sqlite and PostgreSQL persistence for dispatcher list/detail projections, status updates, assignment metadata, visit window, and internal notes.
- `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql`: additive PostgreSQL columns/tables required by dispatcher metadata.
- `apps/api/tests/test_dispatcher_requests.py`: API behavior tests for dispatcher list, detail, status transition, clarification creation, assignment, and public-data safety.
- `apps/web/src/App.tsx`: dispatcher route, typed API helpers, list/detail state, and action handlers.
- `apps/web/src/App.test.tsx`: renderer and helper tests for dispatcher UI contracts.
- `apps/web/src/styles.css`: dispatcher layout, request list, detail panel, action controls, and responsive states.
- `domains/service-requests/domain.md`: Phase 04 dispatcher lifecycle notes.
- `domains/technicians/domain.md`: manual assignment boundary for this phase.
- `domains/scheduling/domain.md`: visit-window boundary for this phase.
- `project_notes.md`, `docs/execution-plans/index.md`, `docs/harness/repository-map.md`, and `tools/repo-checks/check_docs.py`: harness updates after implementation and review.
- `docs/review/phase-04-review.md`: durable review artifact after local verification.

## Task 1: Dispatcher API Contract And Failing Tests

**Files:**
- Modify: `apps/api/src/serviceops_api/service_requests/models.py`
- Create: `apps/api/tests/test_dispatcher_requests.py`

- [ ] **Step 1: Add dispatcher DTO skeletons**

Add Pydantic models for:
- `DispatcherRequestListItem`
- `DispatcherRequestDetail`
- `DispatcherStatusUpdatePayload`
- `DispatcherClarificationPayload`
- `DispatcherAssignmentPayload`
- `DispatcherInternalNotePayload`
- `DispatcherActionResponse`

Use explicit field constraints. `internal_notes` and assignment metadata belong only to dispatcher responses.

- [ ] **Step 2: Write failing API tests for list and detail**

Create tests that:
- create two service requests through `POST /service-requests`;
- call `GET /dispatcher/service-requests`;
- assert newest-first ordering, request number, status, customer name, phone, machine brand/model, urgency, address, created timestamp, and latest timeline title;
- call `GET /dispatcher/service-requests/{request_number}`;
- assert full intake detail, timeline, latest clarification, assignment fields, visit window, and internal notes.

Run: `cd apps/api && uv run --extra dev pytest tests/test_dispatcher_requests.py -v`

Expected: failures because dispatcher routes and models do not exist.

- [ ] **Step 3: Write failing API tests for dispatcher actions**

Add tests for:
- `POST /dispatcher/service-requests/{request_number}/status` updating status and appending a dispatcher event;
- `POST /dispatcher/service-requests/{request_number}/clarifications` creating a public clarification question, moving status to `needs_clarification`, and showing the question on the public status page;
- `POST /dispatcher/service-requests/{request_number}/assignment` storing technician metadata, visit window, setting status to `technician_assigned` or `visit_scheduled`, and appending a dispatcher event;
- `POST /dispatcher/service-requests/{request_number}/internal-notes` saving notes that are visible in dispatcher detail but absent from public status responses.

Run: `cd apps/api && uv run --extra dev pytest tests/test_dispatcher_requests.py -v`

Expected: route-not-found failures.

## Task 2: Dispatcher Use Cases And Repository Port

**Files:**
- Modify: `apps/api/src/serviceops_api/service_requests/use_cases.py`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql`

- [ ] **Step 1: Extend the repository protocol**

Add protocol methods for dispatcher list/detail and mutations:
- `list_dispatcher_requests()`
- `get_dispatcher_request(request_number)`
- `update_status(request_number, status, title, description, actor)`
- `ask_clarification(request_number, question)`
- `assign_technician(request_number, technician_name, technician_phone, technician_region, visit_window)`
- `save_internal_note(request_number, note, actor)`

- [ ] **Step 2: Add additive persistence fields**

Add nullable dispatcher metadata to both sqlite initialization and PostgreSQL migration SQL:
- `service_requests.assigned_technician_name`
- `service_requests.assigned_technician_phone`
- `service_requests.assigned_technician_region`
- `service_requests.visit_window`
- `internal_notes` table with `service_request_id`, `note`, `actor`, and `created_at`.

Keep these fields out of `get_public_status_by_request_number()` and `get_public_status_by_token()`.

- [ ] **Step 3: Implement sqlite repository behavior first**

Implement the new protocol methods in `ServiceRequestRepository`. Reuse existing status event insertion patterns and `ask_clarification()` behavior. For assignment:
- set status to `visit_scheduled` when `visit_window` is present;
- set status to `technician_assigned` when no visit window is present;
- append a status event with actor `dispatcher`.

Run: `cd apps/api && uv run --extra dev pytest tests/test_dispatcher_requests.py -v`

Expected: sqlite-backed dispatcher tests move from route failures to use-case or API wiring failures until Task 3 is complete.

- [ ] **Step 4: Implement PostgreSQL repository parity**

Mirror sqlite behavior in `PostgresServiceRequestRepository` with psycopg placeholders, returned IDs, and timestamp formatting consistent with existing public status methods.

Run: `cd apps/api && uv run --extra dev pytest tests/test_repository_selection.py tests/test_service_request_status.py tests/test_dispatcher_requests.py -v`

Expected: all selected API tests pass without Docker because tests inject sqlite; repository selection remains intact.

## Task 3: Dispatcher API Routes

**Files:**
- Modify: `apps/api/src/serviceops_api/service_requests/use_cases.py`
- Modify: `apps/api/src/serviceops_api/service_requests/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`

- [ ] **Step 1: Add dispatcher use cases**

Create use-case classes:
- `ListDispatcherRequests`
- `GetDispatcherRequest`
- `UpdateDispatcherStatus`
- `AskDispatcherClarification`
- `AssignDispatcherTechnician`
- `SaveDispatcherInternalNote`

Each use case should return Pydantic response models instead of raw repository dictionaries.

- [ ] **Step 2: Mount dispatcher routes**

Add routes:
- `GET /dispatcher/service-requests`
- `GET /dispatcher/service-requests/{request_number}`
- `POST /dispatcher/service-requests/{request_number}/status`
- `POST /dispatcher/service-requests/{request_number}/clarifications`
- `POST /dispatcher/service-requests/{request_number}/assignment`
- `POST /dispatcher/service-requests/{request_number}/internal-notes`

Map missing request numbers to `404`. Let invalid status values fail with `422` through Pydantic validation.

- [ ] **Step 3: Verify API behavior**

Run: `cd apps/api && uv run --extra dev pytest tests/test_dispatcher_requests.py tests/test_service_request_status.py tests/test_service_request_intake.py -v`

Expected: dispatcher tests pass and existing public status/intake behavior remains unchanged.

## Task 4: Dispatcher Web Experience

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Write failing web tests**

Add tests that render a dispatcher page with mocked initial data and assert:
- request list cards show request number, customer name, brand/model, urgency, and status label;
- detail panel shows client contact, problem, address, timeline, clarification state, assignment state, visit window, and internal notes;
- helper functions build dispatcher API paths for list/detail/status/clarification/assignment/internal notes;
- public status components do not render dispatcher-only fields.

Run: `cd apps/web && npm test`

Expected: failures because dispatcher helpers and UI do not exist.

- [ ] **Step 2: Add typed dispatcher API helpers**

Add TypeScript types for list items, detail snapshots, action payloads, and action responses. Add helpers for dispatcher API paths and payload trimming. Preserve existing public intake and status helpers.

- [ ] **Step 3: Add dispatcher route and UI**

Render dispatcher UI when `window.location.pathname` starts with `/dispatcher`. Build a work-focused layout:
- left request list with status and urgency filters;
- right detail view for the selected request;
- action controls for status update, clarification question, assignment metadata, visit window, and internal notes;
- clear loading, empty, and error states.

- [ ] **Step 4: Wire dispatcher actions**

Fetch list/detail from the dispatcher API and refresh detail after each successful action. Keep form state local and reset only the form that was submitted.

- [ ] **Step 5: Verify web behavior**

Run:

```bash
cd apps/web && npm test
cd apps/web && npm run lint
cd apps/web && npm run build
```

Expected: web tests, lint, and build pass.

## Task 5: Documentation, Harness, And Review

**Files:**
- Modify: `domains/service-requests/domain.md`
- Modify: `domains/technicians/domain.md`
- Modify: `domains/scheduling/domain.md`
- Modify: `docs/execution-plans/index.md`
- Modify: `docs/harness/repository-map.md`
- Modify: `project_notes.md`
- Modify: `tools/repo-checks/check_docs.py`
- Create: `docs/review/phase-04-review.md`

- [ ] **Step 1: Update domain documentation**

Document dispatcher-only fields, public/private data separation, manual assignment semantics, and visit-window scope.

- [ ] **Step 2: Update repository harness**

Require `docs/execution-plans/detailed/04-dispatcher-mvp-implementation.md`, `apps/api/tests/test_dispatcher_requests.py`, and `docs/review/phase-04-review.md` in `tools/repo-checks/check_docs.py` after the implementation and review artifacts exist.

- [ ] **Step 3: Update project status**

After implementation and review, mark Phase 04 complete, set Phase 05 as the active phase, and record Phase 04 artifacts in `project_notes.md` and `docs/execution-plans/index.md`.

- [ ] **Step 4: Run full verification**

Run:

```bash
python3 tools/repo-checks/check_docs.py
cd apps/api && uv run --extra dev pytest
cd apps/worker && uv run --extra dev pytest
cd apps/telegram-bot && uv run --extra dev pytest
npm run web:test
npm run web:lint
npm run web:build
docker compose config
```

Expected: all commands exit 0. If Docker is unavailable, record the skipped Docker command and reason in the review artifact.

- [ ] **Step 5: Record Phase 04 review**

Apply `docs/review/subagent-review-protocol.md` to the Phase 04 slice, detailed plan, changed-file list, verification output, and public/private data boundary. Store findings and final recommendation in `docs/review/phase-04-review.md`.

## Self-Review

- Spec coverage: the plan covers the Phase 04 deliverables: dispatcher request list, detail card, status actions, clarification creation, manual assignment, visit window, internal notes, tests, project notes, and review gate.
- Placeholder scan: no placeholder markers are present.
- Type consistency: API routes, payload names, status values, and repository method names are consistent across tasks.
- Scope check: authentication, automatic assignment, technician mobile workflows, real scheduling, and outbound notifications stay deferred.
