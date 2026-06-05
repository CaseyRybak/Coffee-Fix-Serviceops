---
name: figma-reference-implementation
description: Use when implementing or changing the CoffeeFix Pro public web UI, landing page, repair form, status page, responsive behavior, or visual styling from the Figma reference.
---

# Figma Reference Implementation

## Context To Open

- `reference/figma/src/app/App.tsx`
- `reference/figma/src/app/components/`
- `docs/product/figma-reference-review.md`
- `docs/product/mvp-scope.md`

## Pattern

Use the Figma export as a visual and UX reference, not as production architecture. Preserve the service-company tone, warm palette, CTA hierarchy, form concept, and status tracking idea. Move production code into reusable components, design tokens, and API-backed state.

## UI Priorities

- First screen clearly says repair coffee machines with technician visit.
- Form remains short for first submission.
- Status page feels practical and low-friction.
- AI is not visually centered in the customer-facing experience.
- Mobile CTA remains easy to reach.

## Implementation Notes

- Replace external image URLs with controlled assets.
- Avoid copying inline styles directly into production components.
- Keep legal/service wording realistic around diagnostics, warranty, and visit conditions.
