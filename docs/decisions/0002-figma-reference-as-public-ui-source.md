# ADR 0002: Figma Reference As Public UI Source

## Status

Accepted.

## Context

The repository includes an exported React/Vite Figma reference in `reference/figma`. The design matches the desired client-facing tone: practical local service company, not a startup landing page.

## Decision

Use `reference/figma` as the primary visual and UX reference for the public site and status page. Treat exported code as reference material, not final production architecture.

## Rationale

The design already captures the correct service-business structure, palette, copy tone, request form, status tracking, and mobile CTA. Production code should reuse these decisions while separating design tokens, reusable components, API-backed state, and assets.

## Consequences

- Public UI implementation should consult `docs/product/figma-reference-review.md`.
- External image URLs should be replaced with controlled assets.
- The first form submission should be simplified for conversion.
