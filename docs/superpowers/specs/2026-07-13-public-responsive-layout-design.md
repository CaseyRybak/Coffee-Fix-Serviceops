# Public Responsive Layout Design

**Date:** 2026-07-13

## Goal

Make the public landing page and public request-status experience readable and balanced on phones and tablets without changing React behavior, API contracts, content order, or the established CoffeeFix Pro visual language.

## Evidence

- On `/status` at 390 px, `.status-lookup` computes to `0px 280px`, collapsing the heading column.
- On a populated status page at 390 px, `.status-dashboard` remains approximately `155px 189px`.
- At 320–375 px the status grid is wider than the visible content area, while global horizontal overflow clipping hides the excess.
- At 1024 px the landing hero remains in the desktop layout: two 476 px columns, six badges in three 153 px columns, crowded navigation, and CTA buttons that wrap unevenly.
- The current breakpoint switches the public landing layout only at 980 px, so common 1024 px tablet viewports miss the tablet treatment.

## Considered Approaches

1. **Targeted intermediate tablet layout (selected).** Keep the 1024 px hero two-column, but reduce its gap, use a balanced 2×3 badge grid, compact the desktop header, and make the CTA row fluid. This fixes the reported tablet composition without turning a landscape tablet into a long phone layout.
2. **Move the entire 980 px breakpoint to 1024 or 1100 px.** Simple, but it would also change unrelated staff workspaces and stack the full landing hero at 1024 px.
3. **Use only auto-fit/auto-flow grids.** More fluid, but less deterministic around the long Russian badge and CTA labels and harder to protect with the repository's current CSS-contract tests.

## Responsive Design

### Tablet landscape: 981–1100 px

- Preserve the two-column hero and image prominence.
- Reduce the hero gap from 40 px to 24 px.
- Render service badges as two equal columns and three rows.
- Render the two hero CTAs in a fluid two-column row so neither wraps onto a separate line solely because of fixed widths.
- Tighten navigation spacing and header CTA padding without hiding navigation.

### Tablet portrait and phones: up to 768 px

- Render status lookup/header and status dashboard as one column.
- Keep the DOM order: summary, history, clarification, Telegram.
- Reset the Telegram card's explicit second-column placement.
- Stretch the “check another request” action to the available width.
- Allow long request numbers, model names, timeline titles, and descriptions to wrap safely.

### Compact phones: up to 620 px

- Reduce status page vertical and card padding.
- Use full-width answer and Telegram actions.
- Preserve at least 44 px interactive control height.

## Testing

- Add CSS-contract regression tests before implementation and observe them fail.
- Run the existing web test, TypeScript lint, and production build commands.
- Verify `/`, `/status`, and a populated status fixture with Playwright at 320, 375, 390, 620, 768, 834, 980, 1024, 1100, and 1101 px.
- Browser acceptance: no clipped content; one-column status layout at ≤768 px; balanced 2×3 tablet badges at 981–1100 px; all cards remain inside the viewport; desktop layout remains unchanged above 1100 px.

## Scope Boundaries

- No API, domain, data, copy, or navigation behavior changes.
- No redesign of staff workspaces.
- No commit or push without an explicit user instruction.
