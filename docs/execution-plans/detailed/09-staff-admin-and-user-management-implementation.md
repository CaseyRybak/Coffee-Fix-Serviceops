# Phase 09 Staff Admin And User Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persisted staff account management and an admin workspace so production staff users are managed through RBAC instead of hardcoded local-development accounts.

**Architecture:** Extend the staff access layer into a bounded staff-management slice with persisted accounts, role assignments, password hashes, active flags, and audit events. Keep `/staff/login` as the single staff entry point; authentication reads persisted staff users first and keeps local seed users only for development fallback. Add admin-only API routes and a compact `/admin` workspace for account lifecycle operations.

**Tech Stack:** Python, FastAPI, Pydantic, sqlite3, psycopg, PostgreSQL migration SQL, pytest/httpx, React, Vite, TypeScript, node:test.

---

## Scope Decisions

- Phase 09 implements local username/password staff account management for MVP operations.
- Phase 09 does not implement SSO, OAuth, email invitations, email delivery, multi-factor authentication, fine-grained permissions, organization hierarchy, or external identity provider sync.
- Roles remain the Phase 05 vocabulary: `admin`, `dispatcher`, `technician`, and `inventory`.
- Users may hold multiple roles, but the UI should make role assignment explicit and auditable.
- Local seed accounts remain available for development and tests, but production deployment should rely on persisted accounts.
- The system must prevent deactivating the last active admin.
- Password reset creates a new temporary password response for the admin to hand to the employee out of band.

## File Responsibility Map

- Create: `apps/api/src/serviceops_api/staff_management/__init__.py` for package exports.
- Create: `apps/api/src/serviceops_api/staff_management/models.py` for account, role, action, and audit DTOs.
- Create: `apps/api/src/serviceops_api/staff_management/repository.py` for sqlite and PostgreSQL staff account repositories.
- Create: `apps/api/src/serviceops_api/staff_management/use_cases.py` for admin account lifecycle services.
- Create: `apps/api/src/serviceops_api/staff_management/api.py` for admin-only staff-management routes.
- Create: `apps/api/src/serviceops_api/migrations/0005_staff_management.sql` for PostgreSQL staff account and audit tables.
- Modify: `apps/api/src/serviceops_api/staff_auth.py` to authenticate persisted staff accounts before development seed users.
- Modify: `apps/api/src/serviceops_api/main.py` to wire staff repositories, authenticator, and admin routes.
- Create: `apps/api/tests/test_staff_management.py` for admin lifecycle, role checks, audit, login, and last-admin protection.
- Modify: `apps/api/tests/test_staff_auth.py` to cover persisted login and existing development fallback behavior.
- Modify: `apps/api/tests/test_repository_selection.py` to cover staff account repository selection.
- Modify: `apps/web/src/App.tsx` to add `/admin` route helpers, protected admin page, staff list, create form, role controls, deactivate, and password reset actions.
- Modify: `apps/web/src/App.test.tsx` to cover admin rendering, path helpers, route guard, and role-based login landing.
- Modify: `apps/web/src/styles.css` to style the admin workspace consistently with internal workspaces.
- Modify: `domains/customers/domain.md` only if staff identity is mentioned there during implementation; otherwise leave customer identity separate.
- Modify: `docs/harness/repository-map.md` and `tools/repo-checks/check_docs.py` after implementation artifacts exist.
- Modify: `project_notes.md` and `docs/execution-plans/index.md` after implementation to mark Phase 10 active.
- Create: `docs/review/phase-09-review.md` after verification and review.

## Task 1: Staff Account Models And Persistence

**Files:**
- Create: `apps/api/src/serviceops_api/staff_management/__init__.py`
- Create: `apps/api/src/serviceops_api/staff_management/models.py`
- Create: `apps/api/src/serviceops_api/staff_management/repository.py`
- Create: `apps/api/src/serviceops_api/migrations/0005_staff_management.sql`
- Create: `apps/api/tests/test_staff_management.py`
- Modify: `apps/api/tests/test_repository_selection.py`

- [ ] **Step 1: Write failing repository tests**

Create `apps/api/tests/test_staff_management.py` with tests that instantiate `SqliteStaffAccountRepository.in_memory()` and assert account creation, role listing, active flag behavior, password reset hash changes, audit records, and last-admin protection.

Use this initial test shape:

```python
def test_staff_repository_creates_account_with_roles_and_audit() -> None:
    from serviceops_api.staff_management.models import CreateStaffAccountPayload
    from serviceops_api.staff_management.repository import SqliteStaffAccountRepository
    from serviceops_api.staff_management.use_cases import CreateStaffAccount, ListStaffAccounts

    repository = SqliteStaffAccountRepository.in_memory()
    created = CreateStaffAccount(repository).execute(
        CreateStaffAccountPayload(
            username="tech-1@coffeefix.local",
            display_name="Tech One",
            password="temporary-pass-1",
            roles=["technician"],
        ),
        actor="admin@coffeefix.local",
    )

    assert created.username == "tech-1@coffeefix.local"
    assert created.roles == ["technician"]
    assert created.active is True
    assert ListStaffAccounts(repository).execute().items[0].username == "tech-1@coffeefix.local"
    assert repository.list_audit_events()[0]["action"] == "staff.created"
```

Run: `cd apps/api && uv run --extra dev pytest tests/test_staff_management.py -q`

Expected: fails because `serviceops_api.staff_management` does not exist.

- [ ] **Step 2: Add staff-management models**

In `models.py`, define:
- `StaffRoleValue = Literal["admin", "dispatcher", "technician", "inventory"]`;
- `CreateStaffAccountPayload` with required trimmed `username`, `display_name`, `password`, and at least one role;
- `UpdateStaffRolesPayload` with at least one role;
- `ResetStaffPasswordPayload` with required temporary password;
- `StaffAccount`;
- `StaffAccountListResponse`;
- `StaffAccountActionResponse`;
- `StaffAuditEvent`;
- `StaffAuditListResponse`.

- [ ] **Step 3: Add PostgreSQL migration**

Create `0005_staff_management.sql` with:
- `staff_accounts`: id, username unique, display_name, password_hash, active, created_at, updated_at;
- `staff_account_roles`: staff_account_id, role, created_at, primary key on both columns;
- `staff_audit_events`: id, actor_username, target_username, action, metadata JSONB, created_at;
- indexes on active accounts, roles, and audit target/action.

- [ ] **Step 4: Implement sqlite repository**

Implement `StaffAccountStore` protocol and `SqliteStaffAccountRepository` with methods:
- `create_account(payload, password_hash, actor)`;
- `list_accounts()`;
- `get_account_by_username(username)`;
- `update_roles(username, roles, actor)`;
- `set_active(username, active, actor)`;
- `reset_password(username, password_hash, actor)`;
- `list_audit_events()`;
- `count_active_admins()`.

Raise `ValueError("Cannot deactivate the last active admin")` if active admin count would drop to zero.

- [ ] **Step 5: Implement PostgreSQL repository and factory**

Implement `PostgresStaffAccountRepository` and `create_staff_account_repository(settings, initialize=True)` with the same URL selection pattern as other repositories. PostgreSQL initialization must apply migrations `0001` through `0005`.

- [ ] **Step 6: Add repository selection tests**

Extend `apps/api/tests/test_repository_selection.py` to assert:
- PostgreSQL URL creates `PostgresStaffAccountRepository`;
- sqlite memory URL creates `SqliteStaffAccountRepository`;
- unsupported URL raises `ValueError` with `Unsupported SERVICEOPS_DATABASE_URL`.

- [ ] **Step 7: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_staff_management.py tests/test_repository_selection.py -q`

Expected: passes.

## Task 2: Persisted Authentication And Seed Fallback

**Files:**
- Modify: `apps/api/src/serviceops_api/staff_auth.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/tests/test_staff_auth.py`
- Modify: `apps/api/tests/test_staff_management.py`

- [ ] **Step 1: Write failing authentication tests**

Add tests that:
- create a persisted staff account with role `technician`;
- login through `/staff/login` succeeds with persisted credentials;
- protected `/technician/service-requests` accepts the issued token;
- deactivated account login returns 401;
- development seed users still work when no persisted account matches.

Run: `cd apps/api && uv run --extra dev pytest tests/test_staff_auth.py tests/test_staff_management.py -q`

Expected: fails because `StaffAuthenticator` does not read persisted accounts.

- [ ] **Step 2: Add password hashing helpers**

In `staff_auth.py`, add PBKDF2-SHA256 helpers using the standard library:
- `hash_staff_password(password: str, salt: str | None = None) -> str`;
- `verify_staff_password(password: str, encoded_hash: str) -> bool`.

The encoded format should include algorithm, iterations, salt, and digest.

- [ ] **Step 3: Extend StaffAuthenticator**

Allow `StaffAuthenticator(settings, staff_account_reader=None)`. During `authenticate`, check persisted staff account first:
- username must exist;
- account must be active;
- password hash must verify;
- roles must be non-empty.

If no persisted account matches, keep the existing development seed user behavior.

- [ ] **Step 4: Wire staff repository in main**

Update `create_app` to accept optional `staff_account_repository`. If no repository is injected, create it with `create_staff_account_repository(settings)`. Pass it into `StaffAuthenticator`.

- [ ] **Step 5: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_staff_auth.py tests/test_staff_management.py -q`

Expected: passes.

## Task 3: Admin Staff Management API

**Files:**
- Create: `apps/api/src/serviceops_api/staff_management/use_cases.py`
- Create: `apps/api/src/serviceops_api/staff_management/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/tests/test_staff_management.py`

- [ ] **Step 1: Write failing admin API tests**

Add tests that:
- login as `admin@coffeefix.local`;
- `POST /admin/staff` creates a user;
- `GET /admin/staff` lists users;
- `POST /admin/staff/{username}/roles` changes roles;
- `POST /admin/staff/{username}/deactivate` deactivates a user;
- `POST /admin/staff/{username}/reset-password` returns a one-time temporary password response;
- `GET /admin/staff/audit` lists audit events;
- non-admin staff receives 403.

Run: `cd apps/api && uv run --extra dev pytest tests/test_staff_management.py -q`

Expected: fails because admin staff routes do not exist.

- [ ] **Step 2: Implement use cases**

Add:
- `CreateStaffAccount`;
- `ListStaffAccounts`;
- `UpdateStaffRoles`;
- `DeactivateStaffAccount`;
- `ActivateStaffAccount`;
- `ResetStaffPassword`;
- `ListStaffAuditEvents`.

Every mutating use case receives the current admin username as actor and records audit events.

- [ ] **Step 3: Implement admin router**

Create `create_staff_management_router(...)` under prefix `/admin/staff`, protected with `require_staff_role("admin", authenticator)`.

Routes:
- `GET /admin/staff`;
- `POST /admin/staff`;
- `POST /admin/staff/{username}/roles`;
- `POST /admin/staff/{username}/activate`;
- `POST /admin/staff/{username}/deactivate`;
- `POST /admin/staff/{username}/reset-password`;
- `GET /admin/staff/audit`.

- [ ] **Step 4: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_staff_management.py tests/test_staff_auth.py -q`

Expected: passes.

## Task 4: Admin Web Workspace

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Write failing web tests**

Extend `apps/web/src/App.test.tsx` to cover:
- `buildAdminStaffPath()`;
- `buildAdminStaffRolesPath(username)`;
- `buildAdminStaffActivatePath(username)`;
- `buildAdminStaffDeactivatePath(username)`;
- `buildAdminStaffResetPasswordPath(username)`;
- `buildAdminStaffAuditPath()`;
- `/admin` route guard requires `admin`;
- admin workspace renders staff list, role controls, create account form, deactivate action, reset password action, and audit list;
- public page still does not link to `/admin`.

Run: `npm run web:test`

Expected: fails because admin helpers and page do not exist.

- [ ] **Step 2: Add admin route helpers and types**

Add TypeScript interfaces for staff account DTOs and exported path builders for admin staff routes.

- [ ] **Step 3: Add ProtectedAdminPage and AdminPage**

Implement a compact internal workspace at `/admin` with:
- staff table;
- create staff form;
- role checkboxes for `admin`, `dispatcher`, `technician`, and `inventory`;
- activate/deactivate actions;
- reset password action showing the temporary password response;
- audit event list.

Use existing staff session storage and `staffAuthHeaders`.

- [ ] **Step 4: Add route switching**

Update `App()` so `/admin` renders `ProtectedAdminPage`. Update `resolveStaffLandingPath` so an admin-only account lands on `/admin`, while multi-role admin users can still follow a role-valid `next` path.

- [ ] **Step 5: Style admin workspace**

Add scoped CSS for admin staff table, role chips, audit list, and temporary password result. Keep it consistent with dispatcher, technician, and inventory workspaces.

- [ ] **Step 6: Verify**

Run:

```bash
npm run web:test
npm run web:lint
npm run web:build
```

Expected: all pass.

## Task 5: Documentation, Harness, And Review

**Files:**
- Modify: `docs/harness/repository-map.md`
- Modify: `tools/repo-checks/check_docs.py`
- Modify: `project_notes.md`
- Modify: `docs/execution-plans/index.md`
- Create: `docs/review/phase-09-review.md`

- [ ] **Step 1: Update harness docs and checks**

After implementation files exist, add staff-management module files, migration `0005_staff_management.sql`, tests, detailed Phase 09 plan, and Phase 09 review artifact to `docs/harness/repository-map.md` and `tools/repo-checks/check_docs.py`.

- [ ] **Step 2: Update operational status**

After implementation and review, update `project_notes.md` to mark Phase 09 complete and Phase 10 active. Update `docs/execution-plans/index.md` so active phase is `phases/10-deployment-and-operations.md` and detailed Phase 09 is listed as completed.

- [ ] **Step 3: Run full verification**

Run:

```bash
python3 tools/repo-checks/check_docs.py
cd apps/api && uv run --extra dev pytest
cd ../worker && uv run --extra dev pytest
cd ../telegram-bot && uv run --extra dev pytest
cd ../..
npm run web:test
npm run web:lint
npm run web:build
```

Expected: all pass.

- [ ] **Step 4: Prepare subagent review**

Create `docs/review/phase-09-review.md` using `docs/review/subagent-review-protocol.md`. Include changed files, verification output, findings grouped by blocking issues, non-blocking issues, suggested follow-up slice, documentation updates needed, and final recommendation.

## Review Handoff

Before implementation starts, review this plan against `docs/execution-plans/phases/09-staff-admin-and-user-management.md`. The review should focus on account-management security, role consistency, least-privilege behavior, auditability, last-admin protection, and separation between development seed users and production persisted staff accounts.
