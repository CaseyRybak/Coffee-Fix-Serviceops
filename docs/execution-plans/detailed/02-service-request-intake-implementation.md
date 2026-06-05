# Service Request Intake Implementation Plan

> **For implementation workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first end-to-end repair request flow from the public form to a persisted service request with a public request number.

**Architecture:** The API keeps service-request, customer, and machine intake concerns behind an application use case and repository port. Persistence uses a small sqlite-backed repository for deterministic local tests and development, while a PostgreSQL migration records the target production schema. The web app becomes the MVP public repair intake surface based on the Figma reference, with a real submit flow and success state.

**Tech Stack:** Python, FastAPI, Pydantic, sqlite3, pytest, React, Vite, TypeScript, Node test runner through `tsx`, Docker Compose, PostgreSQL migration SQL.

---

## Execution Status

- Completed: API intake contract, validation, request-number generation, and persistence.
- Completed: public repair request form with submit and success state.
- Completed: domain documentation, project notes, repository checks, and Phase 02 review artifact.

## Task 1: API Intake Domain And Persistence

**Files:**
- Create: `apps/api/src/serviceops_api/service_requests/__init__.py`
- Create: `apps/api/src/serviceops_api/service_requests/models.py`
- Create: `apps/api/src/serviceops_api/service_requests/repository.py`
- Create: `apps/api/src/serviceops_api/service_requests/use_cases.py`
- Create: `apps/api/src/serviceops_api/service_requests/api.py`
- Create: `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql`
- Create: `apps/api/tests/test_service_request_intake.py`
- Modify: `apps/api/src/serviceops_api/config.py`
- Modify: `apps/api/src/serviceops_api/main.py`

- [x] **Step 1: Write failing API tests**

Create `apps/api/tests/test_service_request_intake.py` with tests that call `POST /service-requests` through the FastAPI ASGI app. Cover a successful request, persistence of customer and machine data, request number shape, and validation errors for missing required fields.

- [x] **Step 2: Run API test and verify red**

Run: `cd apps/api && uv run --extra dev pytest tests/test_service_request_intake.py -v`

Expected before implementation: import or route failure because the service-request modules and route do not exist.

- [x] **Step 3: Implement intake models and use case**

Add Pydantic request/response models, a `CreateServiceRequest` use case, and request-number generation that returns public numbers shaped like `CFX-YYYYMMDD-000001`.

- [x] **Step 4: Implement sqlite-backed repository**

Add repository initialization, inserts for `customers`, `machines`, `service_requests`, and `attachment_metadata`, and a test helper query surface used only through repository methods. Default local storage should be in-memory for tests when a repository is injected and file-backed under `.local/serviceops-api.sqlite3` for the app factory.

- [x] **Step 5: Register the FastAPI route**

Mount `POST /service-requests` in `create_app()`, return `201 Created`, and keep `/health` behavior unchanged.

- [x] **Step 6: Add target database migration**

Create `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql` with PostgreSQL tables and indexes for customers, machines, service requests, and attachment metadata.

- [x] **Step 7: Run API tests and verify green**

Run: `cd apps/api && uv run --extra dev pytest tests/test_service_request_intake.py tests/test_health.py -v`

Expected after implementation: all selected API tests pass.

## Task 2: Public Intake Form

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`

- [x] **Step 1: Write failing web render tests**

Update `apps/web/src/App.test.tsx` to assert that the page renders CoffeeFix Pro public intake content, required fields for name, phone, client type, brand, problem, district or address, urgency, optional Telegram and attachment metadata, and a success-state request-number phrase.

- [x] **Step 2: Run web test and verify red**

Run: `cd apps/web && npm test`

Expected before implementation: test fails because the current runtime shell has no public repair request form.

- [x] **Step 3: Implement public form**

Replace the shell with a public CoffeeFix Pro intake page preserving the Figma reference structure: service bar, header, hero, simplified MVP form, status preview, and mobile sticky CTA. The form posts JSON to `/service-requests` by default and can use `VITE_SERVICEOPS_API_BASE_URL` when provided.

- [x] **Step 4: Implement success and error states**

After a successful API response, show `Заявка <requestNumber> создана` and next-step copy. If the API is unavailable during local UI use, keep the entered data visible and show a clear submit error.

- [x] **Step 5: Run web tests and build**

Run:

```bash
cd apps/web && npm test
cd apps/web && npm run lint
cd apps/web && npm run build
```

Expected after implementation: tests, TypeScript check, and build pass.

## Task 3: Harness, Notes, And Review

**Files:**
- Modify: `domains/service-requests/domain.md`
- Modify: `domains/customers/domain.md`
- Modify: `domains/machines/domain.md`
- Modify: `docs/execution-plans/index.md`
- Modify: `docs/harness/repository-map.md`
- Modify: `project_notes.md`
- Modify: `tools/repo-checks/check_docs.py`
- Create: `docs/review/phase-02-review.md`

- [x] **Step 1: Update domain docs**

Document the Phase 02 intake model fields, status, request-number format, and cross-domain ownership.

- [x] **Step 2: Update project notes and plan index**

Set the active focus to Phase 03 planning, identify `docs/execution-plans/phases/03-client-status-and-notifications.md` as the next active phase, and record Phase 02 artifacts.

- [x] **Step 3: Extend repository checks**

Require the Phase 02 detailed plan, review artifact, API intake files, migration, and web intake files in `tools/repo-checks/check_docs.py`.

- [x] **Step 4: Run full local verification**

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

Expected: all non-Docker commands exit 0 in this environment. If Docker CLI is unavailable, record that `docker compose config` could not be executed locally.

- [x] **Step 5: Request and record Phase 02 review**

Run the review protocol from `docs/review/subagent-review-protocol.md` against the Phase 02 slice, this detailed plan, changed-file list, and verification output. Store findings and final recommendation in `docs/review/phase-02-review.md`.
