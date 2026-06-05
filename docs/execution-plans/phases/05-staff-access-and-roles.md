# Phase 05: Staff Access And Roles

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Add the first production-shaped access layer for internal workspaces so dispatcher, admin, technician, and inventory areas are not reachable as public website pages.

Before implementation, create a detailed implementation plan in `docs/execution-plans/detailed/05-staff-access-and-roles-implementation.md`.

## Context To Read

- `docs/architecture/domain-architecture.md`
- `docs/architecture/tech-stack.md`
- `domains/service-requests/AGENTS.md`
- `domains/technicians/AGENTS.md`
- `domains/inventory/AGENTS.md`
- `docs/execution-plans/phases/04-dispatcher-mvp.md`

## Deliverables

- Staff login page at `/staff/login`.
- Backend authentication contract for staff users.
- Session or token-based staff access.
- Role model for `dispatcher`, `admin`, `technician`, and `inventory`.
- API protection for `/dispatcher/...` routes.
- Frontend route guard for `/dispatcher`.
- Redirect from protected workspace routes to `/staff/login` when unauthenticated.
- No public homepage links to staff workspaces.
- Seed or development-only staff user mechanism for local testing.
- Tests for unauthorized, authorized, and wrong-role access.

## Scope Boundaries

- This phase protects internal workspaces; it does not build a full user-management admin UI.
- Password reset, SSO, OAuth, audit logs, and granular permissions are deferred.
- Public client flows remain unauthenticated: intake form, public status lookup, clarification answer, and Telegram opt-in.
- Dispatcher API protection must be enforced on the backend, not only in the React route.
- Staff workspace URLs may be known directly, but access must require authentication.

## Acceptance Criteria

- Visiting `/dispatcher` without staff auth redirects to `/staff/login`.
- Calling `/dispatcher/service-requests` without staff auth returns `401` or `403`.
- A staff user with role `dispatcher` can open `/dispatcher` and use dispatcher API actions.
- A staff user without dispatcher permission cannot access dispatcher APIs.
- Public homepage does not expose links to staff login, dispatcher, admin, technician, or inventory cabinets.
- Tests cover login success, login failure, protected API access, wrong-role denial, and frontend route behavior.
- `.env.example` documents local staff auth settings.
- `project_notes.md` identifies Phase 06 as the next active phase.

## Subagent Review Gate

Review auth boundary correctness, public/private route separation, role enforcement, session/token handling, and whether dispatcher API access is protected on the backend.
