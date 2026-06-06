# Phase 05 Staff Access And Roles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Protect internal staff workspaces and dispatcher APIs with staff login, bearer-token access, and role checks.

**Architecture:** Add a small staff-auth module beside the FastAPI app that owns staff roles, login payloads, token issuing, and authorization dependencies. Keep public service-request/status routes unauthenticated, and attach a dispatcher-role dependency only to the existing dispatcher router. In React, add `/staff/login`, persist the issued staff token in localStorage, send it on dispatcher API calls, and redirect unauthenticated dispatcher visits to the login page.

**Tech Stack:** FastAPI dependencies and HTTP bearer auth, Pydantic settings/models, Python stdlib HMAC/secrets/hashlib, React/Vite/TypeScript, node:test, pytest/httpx.

---

## Files

- Create: `apps/api/src/serviceops_api/staff_auth.py` for staff role types, login models, token service, and FastAPI dependencies.
- Modify: `apps/api/src/serviceops_api/config.py` to document local dev staff credentials and token secret settings.
- Modify: `apps/api/src/serviceops_api/main.py` to include staff auth routes and pass dispatcher auth dependency into dispatcher routes.
- Modify: `apps/api/src/serviceops_api/service_requests/api.py` to accept route-level dispatcher dependencies.
- Create: `apps/api/tests/test_staff_auth.py` for login success/failure and dispatcher role protection.
- Modify: `apps/api/tests/test_dispatcher_requests.py` to authenticate existing dispatcher API calls.
- Modify: `apps/web/src/App.tsx` to add staff login state helpers, login page, dispatcher guard, and authenticated dispatcher fetches.
- Modify: `apps/web/src/App.test.tsx` to test auth helpers, login rendering, route guard behavior, and absence of public staff links.
- Modify: `apps/web/src/styles.css` to style the staff login page and guarded workspace controls using existing workspace styling.
- Modify: `.env.example` and `docker-compose.yml` to expose local staff auth settings.
- Modify: `project_notes.md` and `docs/execution-plans/index.md` to mark Phase 06 as active after implementation.
- Create: `docs/review/phase-05-review.md` after review.

## Tasks

### Task 1: Backend Staff Auth Contract

- [ ] Add failing pytest coverage in `apps/api/tests/test_staff_auth.py`:

```python
import asyncio

import httpx

from serviceops_api.main import create_app
from serviceops_api.service_requests.repository import ServiceRequestRepository


async def post_json(path: str, body: dict[str, object]) -> httpx.Response:
    app = create_app(service_request_repository=ServiceRequestRepository.in_memory())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=body)


def test_staff_login_returns_token_for_dev_dispatcher_user() -> None:
    response = asyncio.run(
        post_json("/staff/login", {"username": "dispatcher@coffeefix.local", "password": "dispatcher-local"})
    )

    assert response.status_code == 200
    body = response.json()
    assert body["staff"]["username"] == "dispatcher@coffeefix.local"
    assert body["staff"]["roles"] == ["dispatcher"]
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_staff_login_rejects_bad_password() -> None:
    response = asyncio.run(
        post_json("/staff/login", {"username": "dispatcher@coffeefix.local", "password": "wrong"})
    )

    assert response.status_code == 401
```

- [ ] Run `cd apps/api && uv run --extra dev pytest tests/test_staff_auth.py -q`; expected: fails because `/staff/login` does not exist.
- [ ] Implement `apps/api/src/serviceops_api/staff_auth.py` with `StaffRole`, `StaffUser`, `StaffLoginPayload`, `StaffLoginResponse`, `StaffAuthenticator`, `create_staff_auth_router`, `get_current_staff`, and `require_staff_role("dispatcher")`.
- [ ] Add config defaults:

```python
staff_auth_secret: str = "local-dev-staff-auth-secret-change-me"
staff_dev_username: str = "dispatcher@coffeefix.local"
staff_dev_password: str = "dispatcher-local"
staff_dev_roles: str = "dispatcher"
```

- [ ] Include the staff router from `main.py`.
- [ ] Re-run `cd apps/api && uv run --extra dev pytest tests/test_staff_auth.py -q`; expected: passes.

### Task 2: Backend Dispatcher Role Enforcement

- [ ] Extend `apps/api/tests/test_staff_auth.py` with unauthorized and wrong-role dispatcher API checks. Use `create_app(..., staff_authenticator=StaffAuthenticator(...))` so one app accepts a dispatcher token and another accepts a technician-only token.
- [ ] Run the new tests; expected: unauthenticated dispatcher calls still return `200`, so the new tests fail.
- [ ] Modify `create_dispatcher_router(..., dependencies=[Depends(require_staff_role("dispatcher", authenticator))])` or equivalent route dependency wiring.
- [ ] Update existing dispatcher tests to login once and send `Authorization: Bearer <token>` for all dispatcher API requests while leaving public status requests unauthenticated.
- [ ] Run `cd apps/api && uv run --extra dev pytest tests/test_staff_auth.py tests/test_dispatcher_requests.py -q`; expected: passes.

### Task 3: Frontend Login And Route Guard

- [ ] Add node:test coverage in `apps/web/src/App.test.tsx`:

```tsx
assert.equal(buildStaffLoginPath("/dispatcher"), "/staff/login?next=%2Fdispatcher");
assert.equal(getStoredStaffSession({ getItem: () => null } as unknown as Storage), null);
assert.match(renderToStaticMarkup(<StaffLoginPage />), /Вход для сотрудников/);
assert.match(renderToStaticMarkup(<ProtectedDispatcherPage hasSession={false} />), /href="\/staff\/login\?next=%2Fdispatcher"/);
```

- [ ] Run `npm run web:test`; expected: fails because helpers/components do not exist.
- [ ] Add exported helpers: `buildStaffLoginPath`, `getStoredStaffSession`, `staffAuthHeaders`, `storeStaffSession`, `clearStaffSession`.
- [ ] Add `StaffLoginPage` with username/password fields, POST to `/staff/login`, localStorage persistence, next-route redirect, and compact internal layout.
- [ ] Add `ProtectedDispatcherPage` that renders `DispatcherPage` only when a staff session exists; otherwise renders a login redirect state and, in the browser, redirects to `/staff/login?next=/dispatcher`.
- [ ] Change dispatcher fetches to include `Authorization` headers from the stored staff session.
- [ ] Extend `App()` routing for `/staff/login` and protected `/dispatcher`.
- [ ] Run `npm run web:test`; expected: passes.

### Task 4: Styling And Public/Private Separation

- [ ] Add tests that public `App` markup contains no `/staff/login`, `/dispatcher`, `/admin`, `/technician`, or `/inventory` links.
- [ ] Style `.staff-login-page`, `.staff-login-card`, `.staff-login-form`, and `.workspace-session-actions` in `apps/web/src/styles.css` with the existing restrained service/workspace palette.
- [ ] Add a logout button in `WorkspaceHeader` for staff sessions, clearing localStorage and sending the browser to `/staff/login`.
- [ ] Run `npm run web:test` and `npm run web:lint`; expected: pass.

### Task 5: Runtime Configuration And Docs

- [ ] Add staff auth variables to `.env.example` and `docker-compose.yml` API environment:

```env
SERVICEOPS_STAFF_AUTH_SECRET=local-dev-staff-auth-secret-change-me
SERVICEOPS_STAFF_DEV_USERNAME=dispatcher@coffeefix.local
SERVICEOPS_STAFF_DEV_PASSWORD=dispatcher-local
SERVICEOPS_STAFF_DEV_ROLES=dispatcher
```

- [ ] Update `project_notes.md` status/latest changes/active focus/next steps/active artifacts/recent decisions for Phase 05 complete and Phase 06 active.
- [ ] Update `docs/execution-plans/index.md` active phase to `phases/06-knowledge-base-rag.md` and list the detailed Phase 05 plan.
- [ ] Create `docs/review/phase-05-review.md` summarizing checks against auth boundary correctness, public/private route separation, role enforcement, token handling, and backend dispatcher protection.
- [ ] Run `python3 tools/repo-checks/check_docs.py`; expected: pass.

### Task 6: Final Verification

- [ ] Run `cd apps/api && uv run --extra dev pytest`.
- [ ] Run `cd apps/worker && uv run --extra dev pytest`.
- [ ] Run `cd apps/telegram-bot && uv run --extra dev pytest`.
- [ ] Run `npm run web:test`.
- [ ] Run `npm run web:lint`.
- [ ] Run `npm run web:build`.
- [ ] Run `docker compose config`.
- [ ] Report exact commands and outcomes. Do not commit or push unless the user explicitly asks in the current turn.
