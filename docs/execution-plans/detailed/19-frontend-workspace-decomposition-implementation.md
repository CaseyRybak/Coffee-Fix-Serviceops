# Phase 19 Frontend Workspace Decomposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the large React web application into focused workspace modules while preserving all existing user-facing behavior.

**Architecture:** Keep the existing Vite/React single-page composition and route decisions, but move shared DTOs, API path builders, auth helpers, formatters, and feature pages out of `App.tsx`. Public, staff-auth, dispatcher, technician, inventory, and admin code should live in obvious folders so Phases 20/22/24 can add screens without extending the large app file.

**Tech Stack:** React 18, TypeScript, Vite, lucide-react, Node test runner with `tsx`, server-side render assertions through `react-dom/server`.

---

## File Structure

- Create `apps/web/src/shared/types.ts`: shared DTOs and domain-ish frontend types currently embedded in `App.tsx`.
- Create `apps/web/src/shared/api.ts`: API base URL resolution, public/status path builders, dispatcher/technician/inventory/admin path builders, and payload builders.
- Create `apps/web/src/shared/staffAuth.ts`: staff session storage, staff auth headers, role checks, staff landing resolution, and staff login path.
- Create `apps/web/src/shared/formatters.ts`: status, urgency, appointment, date, AI suggestion, inventory spec, compatibility, quantity, and movement labels.
- Create `apps/web/src/shared/inventory.ts`: inventory SKU and compatibility helper functions.
- Create `apps/web/src/shared/ui.tsx`: small reusable view primitives such as `Field`, `ChipGroup`, `Logo`, `WorkspaceHeader`, and common layout helpers.
- Create `apps/web/src/features/public/PublicLandingPage.tsx`: public landing page, intake form, success state, hero, sections, and footer.
- Create `apps/web/src/features/public/StatusPage.tsx`: public status lookup and status snapshot UI.
- Create `apps/web/src/features/staff-auth/StaffLoginPage.tsx`: staff login screen.
- Create `apps/web/src/features/staff-auth/StaffWorkspacePage.tsx`: role landing workspace.
- Create `apps/web/src/features/dispatcher/DispatcherPage.tsx`: dispatcher list/detail/scheduling workspace plus protected wrapper.
- Create `apps/web/src/features/admin/AdminPage.tsx`: admin staff management workspace plus protected wrapper.
- Create `apps/web/src/features/technician/TechnicianPage.tsx`: technician request/schedule workspace plus protected wrapper.
- Create `apps/web/src/features/inventory/InventoryPage.tsx`: inventory catalog/reservation/movement workspace plus protected wrapper.
- Modify `apps/web/src/App.tsx`: keep imports, route selection, and top-level `App` composition only.
- Modify `apps/web/src/App.test.tsx`: import public exports from new module locations instead of `./App`.
- Modify `apps/web/src/styles.css`: add clear section comments for public, shared staff, dispatcher, admin, technician, and inventory styles without changing selectors or visual behavior.
- Create `docs/review/phase-19-review.md`: durable review-ready summary after implementation and verification.
- Modify `project_notes.md`: update current status and next focus after Phase 19 is implemented.

## Tasks

### Task 1: Baseline And Plan

**Files:**
- Create: `docs/execution-plans/detailed/19-frontend-workspace-decomposition-implementation.md`

- [ ] **Step 1: Verify baseline web tests**

Run: `npm run web:test`

Expected: PASS with the current `src/App.test.tsx` suite.

- [ ] **Step 2: Save this detailed implementation plan**

Create this file and keep the phase scope limited to refactor-only frontend decomposition.

- [ ] **Step 3: Confirm no code behavior has changed yet**

Run: `git status --short`

Expected: only this detailed plan file is new.

### Task 2: Extract Shared Types And API Helpers

**Files:**
- Create: `apps/web/src/shared/types.ts`
- Create: `apps/web/src/shared/api.ts`
- Create: `apps/web/src/shared/staffAuth.ts`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`

- [ ] **Step 1: Move frontend DTOs and union types into `shared/types.ts`**

Move the existing type/interface declarations from the top of `App.tsx`, export them, and update imports.

- [ ] **Step 2: Move API path and payload helpers into `shared/api.ts`**

Move existing helper functions such as `resolveApiBaseUrl`, `buildServiceRequestPayload`, status path helpers, dispatcher/technician/inventory/admin path builders, and customer answer/Telegram payload builders.

- [ ] **Step 3: Move staff session helpers into `shared/staffAuth.ts`**

Move the staff storage key, workspace path, session storage helpers, auth headers, role checks, auth-failure check, and staff landing resolution.

- [ ] **Step 4: Update tests to import helpers from shared modules**

Keep the same assertions; only change import locations.

- [ ] **Step 5: Verify shared extraction**

Run: `npm run web:test`

Expected: PASS.

### Task 3: Extract Formatters, Inventory Helpers, And Shared UI

**Files:**
- Create: `apps/web/src/shared/formatters.ts`
- Create: `apps/web/src/shared/inventory.ts`
- Create: `apps/web/src/shared/ui.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`

- [ ] **Step 1: Move label/date formatter helpers into `shared/formatters.ts`**

Move status, urgency, appointment state, compact date/time, AI suggestion, inventory quantity/spec/compatibility, and stock movement label helpers. Export only helpers used by tests or other modules.

- [ ] **Step 2: Move inventory SKU/search helpers into `shared/inventory.ts`**

Move factual key normalization, SKU suggestion, inventory search text, and compatibility matching helpers that are not React components.

- [ ] **Step 3: Move common UI primitives into `shared/ui.tsx`**

Move field wrappers, chip groups, logo, service bar/header primitives, workspace header, section heading, and footer column components as needed by feature modules.

- [ ] **Step 4: Update imports and tests**

Move tests for inventory labels/SKU helpers to import from `shared/formatters` and `shared/inventory`.

- [ ] **Step 5: Verify helper/UI extraction**

Run: `npm run web:test`

Expected: PASS.

### Task 4: Extract Public And Staff Auth Features

**Files:**
- Create: `apps/web/src/features/public/PublicLandingPage.tsx`
- Create: `apps/web/src/features/public/StatusPage.tsx`
- Create: `apps/web/src/features/staff-auth/StaffLoginPage.tsx`
- Create: `apps/web/src/features/staff-auth/StaffWorkspacePage.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`

- [ ] **Step 1: Move public landing page and intake flow**

Move `RequestForm`, `HeroSection`, public sections, `SuccessState`, and the landing-page composition into `features/public/PublicLandingPage.tsx`.

- [ ] **Step 2: Move public status page**

Move `StatusPage` and related status display UI into `features/public/StatusPage.tsx`.

- [ ] **Step 3: Move staff login and workspace landing**

Move `StaffLoginPage`, `StaffWorkspacePage`, staff workspace cards, and related role landing UI into `features/staff-auth/`.

- [ ] **Step 4: Update route imports and tests**

`App.tsx` should import public/auth pages from feature modules. Tests should import these components from their new modules.

- [ ] **Step 5: Verify public/auth extraction**

Run: `npm run web:test`

Expected: PASS.

### Task 5: Extract Staff Workspaces

**Files:**
- Create: `apps/web/src/features/dispatcher/DispatcherPage.tsx`
- Create: `apps/web/src/features/admin/AdminPage.tsx`
- Create: `apps/web/src/features/technician/TechnicianPage.tsx`
- Create: `apps/web/src/features/inventory/InventoryPage.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`

- [ ] **Step 1: Move dispatcher workspace**

Move `DispatcherPage`, `ProtectedDispatcherPage`, dispatcher filters, dispatcher detail/actions, scheduling UI, AI suggestion UI, and notification delivery UI into `features/dispatcher/DispatcherPage.tsx`.

- [ ] **Step 2: Move admin workspace**

Move staff account management UI, profile draft/change request helper, `AdminPage`, and `ProtectedAdminPage` into `features/admin/AdminPage.tsx`.

- [ ] **Step 3: Move technician workspace**

Move `TechnicianPage`, `ProtectedTechnicianPage`, schedule/request detail UI, diagnosis/result/parts-used flows into `features/technician/TechnicianPage.tsx`.

- [ ] **Step 4: Move inventory workspace**

Move `InventoryPage`, `ProtectedInventoryPage`, catalog, stock, compatibility, reservation, low-stock, and movement UI into `features/inventory/InventoryPage.tsx`.

- [ ] **Step 5: Verify staff workspace extraction**

Run: `npm run web:test`

Expected: PASS.

### Task 6: Split Styles By Maintainable Sections

**Files:**
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Add stable section comments**

Group existing selectors into clear sections: base/tokens, public landing, shared staff shell, dispatcher, admin, technician, inventory, responsive rules. Do not rename selectors unless required by moved components.

- [ ] **Step 2: Verify CSS still includes core route selectors**

Run: `rg -n "staff-shell|dispatcher|technician|inventory|admin|hero|request-form" apps/web/src/styles.css`

Expected: selectors for all existing workspaces remain present.

- [ ] **Step 3: Verify styles with tests/build**

Run: `npm run web:test`

Expected: PASS.

### Task 7: Final Verification And Review Artifacts

**Files:**
- Modify: `project_notes.md`
- Create: `docs/review/phase-19-review.md`

- [ ] **Step 1: Run full web verification**

Run: `npm run web:test`

Expected: PASS.

Run: `npm run web:lint`

Expected: PASS.

Run: `npm run web:build`

Expected: PASS.

- [ ] **Step 2: Check app decomposition size**

Run: `wc -l apps/web/src/App.tsx apps/web/src/shared/*.ts apps/web/src/shared/*.tsx apps/web/src/features/*/*.tsx`

Expected: `App.tsx` is small enough to show routing/composition rather than feature implementation.

- [ ] **Step 3: Update project notes**

Update `project_notes.md` so Current Status records Phase 19 decomposition and Active Focus points to Phase 20.

- [ ] **Step 4: Create review artifact**

Create `docs/review/phase-19-review.md` with files reviewed, verification commands, findings, and final recommendation.

- [ ] **Step 5: Inspect final diff**

Run: `git status --short`

Expected: changed files are limited to web decomposition, Phase 19 detailed plan, project notes, and Phase 19 review artifact.

## Self-Review

- Spec coverage: The plan covers all Phase 19 deliverables: feature modules, shared API helpers, shared types, shared formatters, style organization, tests, no behavior changes, and review gate.
- Placeholder scan: No deferred implementation placeholders are required for this refactor plan.
- Type consistency: Type/module names match existing frontend concepts and are intentionally reused across extracted modules.
