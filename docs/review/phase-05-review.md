# Phase 05 Review: Staff Access And Roles

## Reviewer Role

Implementation-session self-review against `docs/review/subagent-review-protocol.md`.

Independent subagent review has not been performed in a separate session. Treat that as residual review risk before exposing staff workspaces beyond localhost development.

## Files Reviewed

- `docs/execution-plans/phases/05-staff-access-and-roles.md`
- `docs/execution-plans/detailed/05-staff-access-and-roles-implementation.md`
- `apps/api/src/serviceops_api/staff_auth.py`
- `apps/api/src/serviceops_api/config.py`
- `apps/api/src/serviceops_api/main.py`
- `apps/api/src/serviceops_api/service_requests/api.py`
- `apps/api/tests/test_staff_auth.py`
- `apps/api/tests/test_dispatcher_requests.py`
- `apps/web/src/App.tsx`
- `apps/web/src/App.test.tsx`
- `apps/web/src/styles.css`
- `.env.example`
- `docker-compose.yml`
- `project_notes.md`
- `docs/execution-plans/index.md`

## Verification Commands

All final verification commands exited with code 0. Python app checks were run with `UV_CACHE_DIR=/tmp/uv-cache` because the default uv cache path under the user home directory is read-only in this sandbox.

- `python3 tools/repo-checks/check_docs.py`: documentation harness check passed.
- `cd apps/api && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`: 25 passed.
- `cd apps/worker && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`: 1 passed.
- `cd apps/telegram-bot && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`: 2 passed.
- `npm run web:test`: `src/App.test.tsx` passed under the Node test runner.
- `npm run web:lint`: TypeScript check passed.
- `npm run web:build`: Vite production build completed.
- `docker compose config`: Compose configuration rendered successfully.

## Blocking Issues

None found in implementation-session review.

## Non-Blocking Issues

- Staff users are local-development seeded identities backed by environment settings and hard-coded role demo users. Production user lifecycle, password rotation, password reset, SSO/OAuth, audit logs, and persistent staff accounts remain deferred by Phase 05 scope.
- Staff tokens are stateless bearer tokens. This is adequate for the MVP access gate, but production deployment should rotate `SERVICEOPS_STAFF_AUTH_SECRET`, use HTTPS-only transport, and add token revocation or session management if operationally required.
- Independent subagent review remains pending because this artifact was produced by the same implementation session.
- The implementation-session audit found and corrected one frontend-only gap: a saved staff session without the `dispatcher` role no longer renders the dispatcher workspace shell before backend API calls fail with `403`.

## Auth Boundary Review

- Public `POST /service-requests`, status lookup, clarification answer, and Telegram opt-in routes remain unauthenticated.
- `/dispatcher/service-requests...` routes are protected by a FastAPI dependency that requires a valid staff bearer token and the `dispatcher` role.
- A staff user with `technician`, `inventory`, or `admin` only is denied dispatcher API access unless granted `dispatcher`.
- The public React homepage does not render links to `/staff/login`, `/dispatcher`, `/admin`, `/technician`, or `/inventory`.
- The `/dispatcher` React route is guarded and redirects unauthenticated browser sessions to `/staff/login?next=/dispatcher`; a staff session without `dispatcher` role is shown a wrong-role state instead of the dispatcher workspace. Backend protection remains the source of truth.

## Suggested Follow-Up Slice

- Phase 06: knowledge-base documents, chunks, embeddings, retrieval with sources.
- Before public deployment: replace local-development staff credentials with production-grade staff identity management or an ingress-auth integration.

## Documentation Updates Needed

None outstanding after this artifact and the Phase 05 harness updates.

## Final Recommendation

Proceed to Phase 06 planning.
