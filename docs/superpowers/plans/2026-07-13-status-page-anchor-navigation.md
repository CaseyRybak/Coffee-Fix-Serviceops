# Status Page Anchor Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make shared landing-page anchor links navigate correctly when clicked from public status routes.

**Architecture:** Keep the existing native anchor navigation and shared Header/Footer components. Replace document-relative fragments with root-qualified fragments so browser navigation always targets sections rendered by the landing route, then resolve the initial hash in a landing-page mount effect because the browser may process the fragment before React creates the target element.

**Tech Stack:** React, TypeScript, Node test runner, Vite, Playwright CLI

---

### Task 1: Route shared section links through the landing page

**Files:**
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/features/public/PublicLandingPage.tsx`

- [ ] **Step 1: Write the failing regression test**

Import `Footer` and `Header` from `PublicLandingPage.tsx`, render both to static markup, assert that each landing section is referenced through `/#<id>`, and reject bare section fragments:

```tsx
it("routes shared section links through the landing page", () => {
  const html = renderToStaticMarkup(
    <>
      <Header />
      <Footer />
    </>,
  );

  for (const section of ["services", "brands", "how-it-works", "trust", "footer", "top"]) {
    assert.match(html, new RegExp(`href="/#${section}"`));
  }
  assert.doesNotMatch(html, /href="#(?:services|brands|how-it-works|trust|footer|top)"/);
});
```

- [ ] **Step 2: Verify the test fails for the reported defect**

Run: `npm run web:test`

Expected: FAIL because shared Header/Footer markup still contains links such as `href="#services"`.

- [ ] **Step 3: Implement the minimal link correction**

In `apps/web/src/features/public/PublicLandingPage.tsx`, change only shared landing-section destinations:

```tsx
{ label: "Услуги", href: "/#services" }
{ label: "Бренды", href: "/#brands" }
{ label: "Как работаем", href: "/#how-it-works" }
{ label: "Гарантия", href: "/#trust" }
{ label: "Контакты", href: "/#footer" }
```

Use `/#trust` in `footerClientLinks`, `/#services` and `/#brands` in generated footer columns, and `/#top` for the two footer-bottom links.

- [ ] **Step 4: Write the failing post-render scroll test**

Import `scrollToLandingHash`, pass a target lookup callback, and assert that `#services` calls the target's `scrollIntoView()` while an empty hash returns `false`.

- [ ] **Step 5: Implement post-render hash resolution**

Export `scrollToLandingHash` from `PublicLandingPage.tsx`. It strips the leading `#`, looks up the target, calls `scrollIntoView()`, and reports whether a target was found. Call it from a `useEffect` in `PublicLandingPage` with `window.location.hash`.

- [ ] **Step 6: Verify web quality gates**

Run:

```bash
npm run web:test
npm run web:lint
npm run web:build
```

Expected: all commands exit 0.

- [ ] **Step 7: Verify navigation locally or in production**

Use Playwright from `/status/CFX-20260616-000008`, click `Услуги`, and verify the URL pathname/hash become `/#services` and the `#services` section is present in the viewport.

- [ ] **Step 8: Commit, push, and deploy**

```bash
git add apps/web/src/App.test.tsx apps/web/src/features/public/PublicLandingPage.tsx docs/superpowers/specs/2026-07-13-status-page-anchor-navigation-design.md docs/superpowers/plans/2026-07-13-status-page-anchor-navigation.md
git commit -m "fix: route status page anchors home"
git push origin main
```

On the VPS, fast-forward the checkout, validate `docker-compose.production.yml`, rebuild `web`, and recreate only `web` with `--no-deps`. Confirm API health, web HTTP 200, and repeat the Playwright transition against production.
