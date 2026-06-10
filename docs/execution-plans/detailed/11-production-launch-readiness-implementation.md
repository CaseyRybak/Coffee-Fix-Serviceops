# Production Launch Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the first public launch blockers by adding a production-safe first-admin bootstrap path, real-environment smoke evidence guidance, and updated launch operations documentation.

**Architecture:** Keep launch readiness in operational boundaries. The API gains a CLI-only bootstrap command in `serviceops_api.operations` that uses the existing staff-management repository and password hashing instead of exposing a public route. Operations scripts and docs remain repository-level artifacts so Dokploy/VPS operators can run checks without changing application state unexpectedly.

**Tech Stack:** FastAPI service package, Pydantic settings, sqlite/PostgreSQL staff repositories, Python `uv`/pytest, bash smoke scripts, Docker Compose production docs.

---

## File Structure

- Create `apps/api/src/serviceops_api/operations/bootstrap_admin.py`: CLI and use-case function for one-time first admin creation.
- Create `apps/api/tests/test_operations_bootstrap_admin.py`: unit tests for the bootstrap command and secret-safe behavior.
- Modify `apps/api/src/serviceops_api/operations/__init__.py`: export bootstrap function for operations package consistency.
- Modify `tools/operations/smoke_test.sh`: add optional persisted staff login and dispatcher route check for real deployments.
- Modify `tools/operations/test_smoke_script_contract.py`: keep smoke script routes and secret-handling contracts pinned.
- Create `docs/operations/launch-smoke-evidence.md`: template for recording first-launch verification evidence.
- Modify `docs/operations/deployment-runbook.md`: replace the first-admin limitation with the bootstrap command and go/no-go sequence.
- Modify `docs/operations/smoke-tests.md`: document optional staff smoke variables and evidence capture.
- Modify `.env.example`: add commented first-admin bootstrap and staff smoke variable names without real credentials.
- Modify `tools/repo-checks/check_docs.py`: require the Phase 11 plan, launch evidence doc, and new bootstrap operation file.
- Modify `docs/execution-plans/index.md`: mark Phase 12 as next after implementation.
- Modify `project_notes.md`: record Phase 11 completion and Phase 12 active focus.
- Create `docs/review/phase-11-review.md`: local review artifact with verification commands and residual risks.

## Task 1: First-Admin Bootstrap Operation

**Files:**
- Create: `apps/api/src/serviceops_api/operations/bootstrap_admin.py`
- Modify: `apps/api/src/serviceops_api/operations/__init__.py`
- Test: `apps/api/tests/test_operations_bootstrap_admin.py`

- [ ] **Step 1: Write failing tests**

Add tests that prove:

```python
from serviceops_api.config import Settings
from serviceops_api.operations.bootstrap_admin import BootstrapAdminConfig, bootstrap_first_admin
from serviceops_api.staff_auth import verify_staff_password
from serviceops_api.staff_management.repository import SqliteStaffAccountRepository


def test_bootstrap_first_admin_creates_admin_and_audit_record() -> None:
    repository = SqliteStaffAccountRepository.in_memory()

    result = bootstrap_first_admin(
        BootstrapAdminConfig(
            username="owner@example.com",
            display_name="Owner",
            password="strong-admin-pass",
        ),
        Settings(environment="production", database_url="sqlite:///:memory:"),
        repository=repository,
    )

    account = repository.get_account_by_username("owner@example.com")
    assert result == {"status": "created", "username": "owner@example.com", "roles": ["admin"]}
    assert account is not None
    assert account["roles"] == ["admin"]
    assert verify_staff_password("strong-admin-pass", str(account["password_hash"]))
    assert repository.list_audit_events()[0]["action"] == "staff.bootstrap_admin_created"


def test_bootstrap_first_admin_refuses_when_active_admin_exists() -> None:
    repository = SqliteStaffAccountRepository.in_memory()
    bootstrap_first_admin(
        BootstrapAdminConfig(
            username="owner@example.com",
            display_name="Owner",
            password="strong-admin-pass",
        ),
        Settings(environment="production", database_url="sqlite:///:memory:"),
        repository=repository,
    )

    try:
        bootstrap_first_admin(
            BootstrapAdminConfig(
                username="second@example.com",
                display_name="Second",
                password="strong-admin-pass-2",
            ),
            Settings(environment="production", database_url="sqlite:///:memory:"),
            repository=repository,
        )
    except RuntimeError as exc:
        assert str(exc) == "Active admin already exists; use the admin workspace for staff management"
    else:
        raise AssertionError("expected bootstrap to refuse a second active admin")


def test_bootstrap_first_admin_validates_input_without_printing_password() -> None:
    repository = SqliteStaffAccountRepository.in_memory()

    try:
        bootstrap_first_admin(
            BootstrapAdminConfig(username=" ", display_name="Owner", password="short"),
            Settings(environment="production", database_url="sqlite:///:memory:"),
            repository=repository,
        )
    except ValueError as exc:
        message = str(exc)
        assert "password" in message
        assert "short" not in message
    else:
        raise AssertionError("expected invalid bootstrap input to fail")
```

- [ ] **Step 2: Run tests to verify RED**

Run: `cd apps/api && uv run --extra dev pytest tests/test_operations_bootstrap_admin.py -v`

Expected: FAIL because `serviceops_api.operations.bootstrap_admin` does not exist.

- [ ] **Step 3: Implement minimal bootstrap operation**

Create a `BootstrapAdminConfig` dataclass, validate trimmed username/display name/password, require no active admin, create a persisted admin through the existing repository, and return only non-secret fields. The CLI reads `SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME`, `SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME`, and `SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD`, prints JSON, and never prints the password.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `cd apps/api && uv run --extra dev pytest tests/test_operations_bootstrap_admin.py -v`

Expected: PASS.

## Task 2: Launch Smoke Script Contract

**Files:**
- Modify: `tools/operations/smoke_test.sh`
- Modify: `tools/operations/test_smoke_script_contract.py`
- Modify: `docs/operations/smoke-tests.md`

- [ ] **Step 1: Write failing smoke contract tests**

Extend `tools/operations/test_smoke_script_contract.py` to assert the script supports `SERVICEOPS_SMOKE_STAFF_USERNAME`, `SERVICEOPS_SMOKE_STAFF_PASSWORD`, and does not echo the staff password.

- [ ] **Step 2: Run tests to verify RED**

Run: `python3 tools/operations/test_smoke_script_contract.py`

Expected: FAIL because the script does not yet support staff smoke credentials.

- [ ] **Step 3: Implement optional staff smoke check**

Update `tools/operations/smoke_test.sh` so that when `SERVICEOPS_SMOKE_STAFF_USERNAME` and `SERVICEOPS_SMOKE_STAFF_PASSWORD` are set, it logs in through `/staff/login`, extracts `access_token`, and checks `/dispatcher/service-requests`. If only one credential variable is set, fail with a clear message.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python3 tools/operations/test_smoke_script_contract.py`

Expected: PASS.

## Task 3: Launch Documentation And Evidence

**Files:**
- Create: `docs/operations/launch-smoke-evidence.md`
- Modify: `docs/operations/deployment-runbook.md`
- Modify: `docs/operations/smoke-tests.md`
- Modify: `.env.example`

- [ ] **Step 1: Add docs and environment contract**

Document the bootstrap command:

```bash
docker compose -f docker-compose.production.yml run --rm \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME="$SERVICEOPS_BOOTSTRAP_ADMIN_USERNAME" \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME="$SERVICEOPS_BOOTSTRAP_ADMIN_DISPLAY_NAME" \
  -e SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD="$SERVICEOPS_BOOTSTRAP_ADMIN_PASSWORD" \
  api python -m serviceops_api.operations.bootstrap_admin
```

Add evidence sections for deployment metadata, bootstrap result, API/web/staff/n8n/worker/Telegram checks, backup readiness, rollback decision, and final go/no-go.

- [ ] **Step 2: Verify docs**

Run: `python3 tools/repo-checks/check_docs.py`

Expected: PASS after repo checker is updated in Task 4.

## Task 4: Roadmap, Harness, And Review

**Files:**
- Modify: `tools/repo-checks/check_docs.py`
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-11-review.md`

- [ ] **Step 1: Update harness requirements**

Add the new Phase 11 detailed plan, bootstrap operation, launch evidence doc, and Phase 11 review artifact to `tools/repo-checks/check_docs.py`.

- [ ] **Step 2: Move active focus**

Set active phase to Phase 12 notification automation in `docs/execution-plans/index.md` and `project_notes.md`. Keep Phase 13 live AI provider follow-up visible.

- [ ] **Step 3: Add Phase 11 review artifact**

Record files changed, verification commands, residual risks, and next slice recommendation in `docs/review/phase-11-review.md`.

## Verification

- [ ] `python3 tools/repo-checks/check_docs.py`
- [ ] `cd apps/api && uv run --extra dev pytest tests/test_operations_bootstrap_admin.py tests/test_staff_management.py tests/test_operations_migrate.py`
- [ ] `python3 tools/operations/test_smoke_script_contract.py`
- [ ] `docker compose -f docker-compose.production.yml --env-file .env.example config`
- [ ] `bash -n tools/operations/smoke_test.sh`

## Self-Review

- Phase 11 deliverables are covered by bootstrap command, launch checklist/runbook, smoke evidence template, and staff smoke check.
- No step stores or prints reusable production credentials.
- Live Dokploy/VPS smoke execution remains an operator action; this slice provides executable procedure and auditable evidence template.
