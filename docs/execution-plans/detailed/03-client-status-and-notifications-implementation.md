# Client Status And Notifications Implementation Plan

> **For implementation workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give clients a public status page for their repair request, let them answer clarification questions, and define the first Telegram opt-in contract.

**Architecture:** Extend the existing service-request slice instead of adding a separate runtime. The API exposes public read/write use cases over repository ports, the sqlite repository persists status events, clarification answers, and Telegram opt-in tokens, and the web app renders a real status lookup/timeline flow using those contracts.

**Tech Stack:** Python, FastAPI, Pydantic, sqlite3, pytest, React, Vite, TypeScript, Node test runner through `tsx`, PostgreSQL migration SQL.

---

## Execution Status

- Completed: API public status contract, timeline events, clarification answer submission, and Telegram opt-in token/link generation.
- Completed: web status page, request lookup, timeline, clarification answer form, Telegram opt-in action, and success-state links.
- Completed: domain documentation, project notes, repository checks, and Phase 03 review artifact.

## Task 1: API Status Contract And Persistence

**Files:**
- Modify: `apps/api/src/serviceops_api/service_requests/models.py`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/src/serviceops_api/service_requests/use_cases.py`
- Modify: `apps/api/src/serviceops_api/service_requests/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql`
- Create: `apps/api/tests/test_service_request_status.py`

- [x] **Step 1: Write failing API tests**

Add tests for:
- `GET /service-requests/{request_number}/status` returning current status, event history, latest clarification question, Telegram opt-in link, and masked customer phone.
- `POST /service-requests/{request_number}/answers` recording a customer answer and adding a status event.
- `POST /service-requests/{request_number}/telegram-opt-in` returning a durable token/link contract.
- `GET /status/{public_token}` returning the same public status snapshot.

- [x] **Step 2: Run API status tests and verify red**

Run: `cd apps/api && uv run --extra dev pytest tests/test_service_request_status.py -v`

Expected before implementation: failures because the status routes and models do not exist.

- [x] **Step 3: Implement public status models**

Add Pydantic models for status events, clarification question display, answer payload/response, Telegram opt-in response, and public status response. Expand `RequestStatus` to include the initial lifecycle statuses documented in `domains/service-requests/domain.md`.

- [x] **Step 4: Implement repository methods**

Create sqlite tables for status events, clarification questions, customer answers, public access tokens, and Telegram opt-ins. Add methods to append events, create/find public access tokens, read status snapshots by request number or token, add clarification questions for tests/seed data, record answers, and create Telegram opt-in tokens.

- [x] **Step 5: Implement use cases and API routes**

Add use cases for public status retrieval, answer submission, and Telegram opt-in creation. Mount the new routes under the existing service-request router and allow `GET`, `POST`, and `OPTIONS` in CORS.

- [x] **Step 6: Run API tests and verify green**

Run: `cd apps/api && uv run --extra dev pytest tests/test_service_request_status.py tests/test_service_request_intake.py tests/test_health.py -v`

Expected after implementation: all selected API tests pass.

## Task 2: Web Status Page And Answer Flow

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`

- [x] **Step 1: Write failing web tests**

Update tests to assert:
- `SuccessState` links to `/status/<requestNumber>` and `/service-requests/<requestNumber>/telegram-opt-in`.
- Status page components render a request number lookup, timeline, clarification question, answer form, and Telegram opt-in action.
- API payload helpers build answer and opt-in requests with trimmed values.

- [x] **Step 2: Run web tests and verify red**

Run: `cd apps/web && npm test`

Expected before implementation: failures because the status page helpers and linked success actions do not exist.

- [x] **Step 3: Implement web status data contracts**

Add TypeScript types for the public status API, helper functions for status URL parsing, answer payloads, and request-number normalization.

- [x] **Step 4: Implement status UI**

Render a status section matching the existing CoffeeFix Pro visual language: request lookup, current status summary, timeline, machine/problem summary, clarification card with answer submission, and Telegram opt-in action. Keep the public landing page as the default route and show the status experience when the path starts with `/status`.

- [x] **Step 5: Wire API calls**

Fetch status snapshots by request number/token, submit answers to `/service-requests/{request_number}/answers`, and request Telegram opt-in links from `/service-requests/{request_number}/telegram-opt-in`. Show clear empty/error states without hiding the lookup form.

- [x] **Step 6: Run web tests and build**

Run:

```bash
cd apps/web && npm test
cd apps/web && npm run lint
cd apps/web && npm run build
```

Expected after implementation: tests, TypeScript check, and build pass.

## Task 3: Documentation, Harness, And Review

**Files:**
- Modify: `domains/service-requests/domain.md`
- Modify: `domains/notifications/domain.md`
- Modify: `docs/execution-plans/index.md`
- Modify: `docs/harness/repository-map.md`
- Modify: `project_notes.md`
- Modify: `tools/repo-checks/check_docs.py`
- Create: `docs/review/phase-03-review.md`

- [x] **Step 1: Update domain docs**

Document status events, public status access, clarification answers, and Telegram opt-in boundaries.

- [x] **Step 2: Update notes and plan index**

Mark Phase 03 complete, set Phase 04 dispatcher MVP as the active phase, and record the Phase 03 detailed plan/review artifacts.

- [x] **Step 3: Extend repository checks**

Require the Phase 03 detailed plan, review artifact, status API test file, and status implementation files in `tools/repo-checks/check_docs.py`.

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

Expected: all non-Docker commands exit 0. If Docker is unavailable, record the skipped command in the review artifact.

- [x] **Step 5: Record Phase 03 review**

Apply `docs/review/subagent-review-protocol.md` to the Phase 03 slice, detailed plan, changed-file list, and verification output. Store findings and recommendation in `docs/review/phase-03-review.md`.
