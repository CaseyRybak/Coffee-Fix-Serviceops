# Status Page Anchor Navigation Design

## Problem

The public status page reuses the landing page header and footer. Their section links currently use document-relative fragments such as `#services` and `#trust`. From `/status` or `/status/<request-number>`, those links resolve inside the status route, where the target sections do not exist.

## Decision

All shared links that target landing-page sections will use root-qualified fragments:

- `/#services`
- `/#brands`
- `/#how-it-works`
- `/#trust`
- `/#footer`
- `/#top`

The same links remain valid on the landing page and navigate correctly from public status routes. This avoids route-specific props and JavaScript click handlers.

## Scope

- Update shared header navigation links.
- Update shared footer service, brand, client, and top links.
- Add a server-rendered regression test covering the shared header/footer markup.
- Verify the actual transition from a production status route with Playwright after deployment.

No API, routing architecture, visual styling, or domain data changes are included.

## Acceptance Criteria

1. Shared landing-section links never render as bare fragments.
2. Clicking a landing-section link from `/status/<request-number>` navigates to `/#<section>`.
3. The destination section exists and is aligned in the viewport.
4. Web tests, lint, and production build pass.

