# Public Responsive Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `test-driven-development` while implementing this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the public landing and status-page composition on phones and tablets while preserving desktop behavior and all public API contracts.

**Architecture:** Keep the React component tree unchanged and solve the defect at the responsive CSS boundary. Add narrow CSS-contract regression tests to the existing Node test suite, then verify computed geometry in a real browser.

**Tech Stack:** React 18, TypeScript, Vite, CSS Grid/Flexbox, Node test runner, Playwright CLI.

---

### Task 1: Add responsive regression tests

**Files:**
- Modify: `apps/web/src/App.test.tsx`
- Test: `apps/web/src/App.test.tsx`

- [x] **Step 1: Add a failing tablet-hero CSS contract test**

Read `styles.css` and assert that a `981–1100px` media query changes `.hero-badges` to two columns, makes `.hero-actions` a fluid two-column grid, and reduces `.hero-inner` gap.

- [x] **Step 2: Add a failing status CSS contract test**

Assert that the `max-width: 768px` rules collapse `.status-lookup` and `.status-dashboard` to one column, reset `.telegram-panel`, and stretch `.secondary-status-button`. Assert that the `max-width: 620px` rules reduce card padding and stretch status action buttons.

- [x] **Step 3: Run the tests and verify RED**

Run: `npm run web:test`

Expected: the new tablet and status responsive contract tests fail because those media-query rules do not exist.

### Task 2: Implement the tablet landing layout

**Files:**
- Modify: `apps/web/src/styles.css`
- Test: `apps/web/src/App.test.tsx`

- [x] **Step 1: Add the intermediate tablet media query**

Add `@media (min-width: 981px) and (max-width: 1100px)` rules for:

```css
.hero-inner {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.hero-badges {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.hero-actions {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
}

.hero-actions .primary-cta,
.hero-actions .secondary-cta {
  width: 100%;
  padding-inline: 14px;
}
```

Also compact `.desktop-nav`, `.header-actions`, and `.header-cta` spacing inside the same tablet-only query.

- [x] **Step 2: Run the tablet contract test and verify GREEN**

Run: `npm run web:test`

Expected: the tablet contract passes; the status responsive contract remains failing until Task 3.

### Task 3: Implement status-page mobile and tablet layout

**Files:**
- Modify: `apps/web/src/styles.css`
- Test: `apps/web/src/App.test.tsx`

- [x] **Step 1: Collapse status grids at 768 px**

Add a `max-width: 768px` query that uses one column for `.status-lookup` and `.status-dashboard`, resets `.telegram-panel` to automatic placement, gives grid children `min-width: 0`, stretches `.secondary-status-button`, and enables safe wrapping for long public text.

- [x] **Step 2: Refine compact-phone spacing at 620 px**

Extend the existing `max-width: 620px` query with smaller status page/card padding and full-width clarification/Telegram submit buttons.

- [x] **Step 3: Run the web test suite and verify GREEN**

Run: `npm run web:test`

Expected: all tests pass.

### Task 4: Verify build and browser geometry

**Files:**
- Verify: `apps/web/src/styles.css`
- Verify: `apps/web/src/App.test.tsx`

- [x] **Step 1: Run static verification**

Run:

```bash
npm run web:test
npm run web:lint
npm run web:build
```

Expected: every command exits 0.

- [x] **Step 2: Run local browser verification**

Open the local Vite site with Playwright CLI and check `/`, `/status`, and a populated status response at 320, 375, 390, 620, 768, 834, 980, 1024, 1100, and 1101 px.

Expected:

- `document.documentElement.scrollWidth === innerWidth` at every viewport.
- Status grids have one track at ≤768 px and two tracks above it.
- Each status card rectangle remains inside its workspace and viewport.
- Landing badges have two tracks at 981–1100 px, three tracks at 768–980 px, and one track at ≤620 px.
- Desktop hero behavior remains unchanged above 1100 px.

- [x] **Step 3: Request independent review**

Provide the reviewer with this plan, the changed-file list, the diff, and fresh verification output. Resolve all blocking or important findings before handoff.

No commit or push is part of this plan because the user has not requested either action.
