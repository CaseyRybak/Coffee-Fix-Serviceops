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

The same links remain valid on the landing page and navigate correctly from public status routes. Because the browser can resolve a cross-route hash before React has rendered its target, `PublicLandingPage` will also resolve the current hash in a mount effect and call `scrollIntoView()` after the target exists. This avoids route-specific props and custom click handlers.

## Scope

- Update shared header navigation links.
- Update shared footer service, brand, client, and top links.
- Resolve an initial landing-page hash after React renders the target section.
- Add a server-rendered regression test covering the shared header/footer markup.
- Add a unit test covering post-render hash resolution.
- Verify the actual transition from a production status route with Playwright after deployment.

No API, routing architecture, visual styling, or domain data changes are included.

## Acceptance Criteria

1. Shared landing-section links never render as bare fragments.
2. Clicking a landing-section link from `/status/<request-number>` navigates to `/#<section>`.
3. The destination section exists and is aligned in the viewport.
4. Web tests, lint, and production build pass.
