# Phase 09: Staff Admin And User Management

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Replace local-development-only staff users with persisted staff account management before production deployment.

## Context To Read

- `domains/customers/AGENTS.md`
- `docs/architecture/domain-architecture.md`
- `docs/architecture/tech-stack.md`
- `docs/execution-plans/detailed/05-staff-access-and-roles-implementation.md`
- `docs/execution-plans/phases/05-staff-access-and-roles.md`

## Deliverables

- Persisted staff accounts.
- Staff account repository for sqlite tests and PostgreSQL deployment.
- Admin-only staff management API.
- Admin workspace at `/admin`.
- Staff list, create, role assignment, activation/deactivation, and password reset flows.
- Audit trail for admin staff-management actions.
- Single `/staff/login` entry that uses persisted accounts and role-based landing.
- Local seed accounts for development and tests.

## Acceptance Criteria

- Admin can create staff accounts and assign `dispatcher`, `technician`, `inventory`, and `admin` roles.
- Admin can deactivate accounts and reset a temporary password.
- The system prevents deactivating or removing the last active admin.
- Staff login authenticates persisted users before local seed fallback.
- Existing dispatcher, technician, and inventory protected workspaces still accept valid role tokens.
- Tests cover account creation, role protection, deactivation, password reset, audit records, and last-admin protection.
- `project_notes.md` identifies Phase 10 as the next active phase after implementation.

## Subagent Review Gate

Review account-management security, role consistency, auditability, and whether development seed users remain clearly separated from production staff records.
