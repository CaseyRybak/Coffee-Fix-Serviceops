# Phase 19: Frontend Workspace Decomposition

> For implementation workers: create a detailed implementation plan before changing code, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Split the large React frontend into understandable workspace modules before adding more staff-facing product screens.

## Why This Phase Exists

The frontend currently concentrates public pages, staff login, dispatcher, technician, inventory, admin, API path helpers, types, formatting, and styling into very large files. This works for the current MVP, but it increases the risk of accidental regressions when adding dashboard, reports, procurement, and assistant screens.

In simple terms: this phase organizes the frontend shelves before adding new boxes.

## Context To Read

- `docs/execution-plans/roadmap-after-phase-16.md`
- `apps/web/src/App.tsx`
- `apps/web/src/App.test.tsx`
- `apps/web/src/styles.css`
- `apps/web/package.json`
- `apps/web/vite.config.ts`
- `docs/product/figma-reference-review.md`
- `domains/service-requests/domain.md`
- `domains/technicians/domain.md`
- `domains/inventory/domain.md`
- `domains/scheduling/domain.md`
- `domains/ai-agents/domain.md`

## Deliverables

- Frontend modules for public pages, staff authentication, dispatcher workspace, technician workspace, inventory workspace, admin workspace, and shared utilities.
- Shared API client/path helpers moved out of the main app file.
- Shared type definitions for request status, appointments, staff roles, inventory records, AI suggestions, and common DTOs.
- Shared formatting helpers for statuses, urgency, dates, appointment states, inventory labels, and stock movement labels.
- Styles split into maintainable files or clearly separated sections that preserve the current visual behavior.
- Tests updated to import helpers/components from the new module locations.
- No intentional user-facing behavior changes.

## Scope Boundaries

- This phase is a refactor. It should not add dashboard, SLA, procurement, AI assistant, or new business workflows.
- Do not redesign the UI unless a tiny style adjustment is required to preserve the existing layout after moving styles.
- Do not rewrite routing architecture beyond what is needed to keep existing routes working.
- Do not change backend API contracts.
- Do not reduce frontend test coverage.

## Acceptance Criteria

- Public landing, request form, success state, public status page, staff login, dispatcher, technician, inventory, and admin routes still render and behave as before.
- Existing web tests pass after imports are updated.
- Frontend build and TypeScript checks pass.
- The main app entry is small enough to reveal routing and composition rather than entire feature implementations.
- Future Phase 20/22/24 screens have obvious locations for new code.

## Subagent Review Gate

Review behavior preservation, import boundaries, route continuity, style regressions, test coverage, and whether the decomposition makes future screens easier to add.
