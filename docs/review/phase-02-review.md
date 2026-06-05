# Phase 02 Review

## Reviewer Role

Independent reviewer for Phase 02 service request intake, following `docs/review/subagent-review-protocol.md`.

## Files Reviewed

- `docs/execution-plans/phases/02-service-request-intake.md`
- `docs/execution-plans/detailed/02-service-request-intake-implementation.md`
- `apps/api/src/serviceops_api/service_requests/`
- `apps/api/src/serviceops_api/migrations/0001_service_request_intake.sql`
- `apps/api/tests/test_service_request_intake.py`
- `apps/web/package.json`
- `apps/web/src/App.tsx`
- `apps/web/src/App.test.tsx`
- `apps/web/src/styles.css`
- `apps/web/vite.config.ts`
- `apps/web/Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `domains/service-requests/domain.md`
- `domains/customers/domain.md`
- `domains/machines/domain.md`
- `project_notes.md`
- `tools/repo-checks/check_docs.py`

## Verification Commands

- `python3 tools/repo-checks/check_docs.py`: passed.
- `cd apps/api && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`: 6 passed.
- `cd apps/worker && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`: 1 passed.
- `cd apps/telegram-bot && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`: 2 passed.
- `npm run web:test`: passed.
- `npm run web:lint`: passed.
- `npm run web:build`: passed.
- `sg docker -c 'docker compose config'`: passed; API, web, PostgreSQL, and Redis ports publish on `127.0.0.1`, and web build args include `VITE_SERVICEOPS_API_BASE_URL=http://localhost:8000`.
- `sg docker -c 'docker compose build web'`: passed.
- Previously recorded local smoke: `GET http://127.0.0.1:8000/health` returned a healthy API payload.
- Previously recorded local smoke: `POST http://127.0.0.1:3000/service-requests` through Vite proxy returned `201 Created` with `CFX-20260605-000002`.

## Plan Compliance Findings

- Blocking issues: none after remediation.
- Non-blocking issues: none against the Phase 02 acceptance criteria.
- Suggested follow-up slice: Phase 03 should implement public status lookup and Telegram notification opt-in.
- Documentation updates needed: none recorded yet.
- Consistency update: the detailed Phase 02 plan now marks completed tasks as complete instead of planned.
- Remediated issue: Docker web initially had no production route from the static nginx site to the API because the Vite API base URL was not passed into the web image build. `apps/web/Dockerfile` now accepts `VITE_SERVICEOPS_API_BASE_URL`, and `docker-compose.yml` passes `http://localhost:8000`.
- Remediated issue: local Compose port bindings now use `127.0.0.1` for API, web, PostgreSQL, and Redis to avoid exposing development services on the wider LAN.

## Architecture And Quality Findings

- Blocking issues: none.
- Non-blocking issues: request number generation currently uses a local persistence count to allocate the next sequence. This is acceptable for the MVP local slice, but real PostgreSQL persistence should replace it with an atomic sequence or counter before concurrent public submissions are expected.
- Non-blocking issues: API HTTP tests use `httpx.ASGITransport` instead of Starlette `TestClient` because `TestClient` hangs in this sandbox before dispatching ASGI requests. The tests still exercise the FastAPI ASGI contract.
- Suggested follow-up slice: replace local sqlite persistence with managed migration execution when the deployment/runtime phase introduces database migration tooling.
- Documentation updates needed: none.

## Final Recommendation

Proceed to Phase 03 planning. Phase 02 satisfies the required intake API, persistence, request number, public form, success state, validation coverage, and project status updates.
