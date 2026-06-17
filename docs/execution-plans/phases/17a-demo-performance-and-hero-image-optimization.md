# Phase 17a: Demo Performance And Hero Image Optimization

## Goal

Make the public demo feel fast on first open by reducing the initial hero/static asset cost discovered during the real domain launch check.

## Why This Phase Exists

During Phase 17 domain and HTTPS setup, the public page loaded correctly, but the first hero image load was visibly slow across browsers. The likely immediate cause is that the current hero PNG assets are large for a first-viewport public demo image, roughly 1.8-1.9 MB before browser caching.

This is not a domain, DNS, HTTPS, or Dokploy routing issue. It is a frontend performance and static asset delivery issue, so it should be handled after public routing is closed and before portfolio screenshots and demo packaging are finalized.

## Scope

- Measure the current hero image and first-load behavior on the production domain and local build.
- Replace or supplement heavy PNG hero assets with optimized WebP and, if useful, AVIF variants.
- Add responsive desktop/mobile image sizes so small screens do not download the largest hero asset.
- Update the frontend image markup or asset references to prefer optimized formats while keeping a safe fallback.
- Review whether the hero image should be preloaded for the public landing page.
- Verify production static asset caching behavior through the deployed web service.
- Keep the visual result equivalent to the current public page unless a tiny crop/format adjustment is required for performance.

## Out Of Scope

- Redesigning the public landing page.
- Changing public copy or product positioning.
- Changing domain, HTTPS, Dokploy, or firewall work from Phase 17.
- Adding portfolio README, screenshots, demo credentials, or demo reset flows from Phase 18.
- Broad frontend decomposition from Phase 19.

## Expected Deliverables

- Optimized hero image assets committed in the frontend public or source asset location.
- Frontend code updated to serve responsive optimized hero images.
- Build/test evidence for the web app.
- A short operations or launch-evidence note recording the before/after asset sizes and deployed-domain check.

## Acceptance Criteria

- The primary first-viewport hero image download is materially smaller than the current PNG asset.
- Target size: desktop hero asset at or below 400-600 KB if visual quality allows; mobile hero asset at or below 200-300 KB if a separate mobile size is used.
- The public page still looks correct on desktop and mobile.
- First uncached load on `https://coffeefix-demo.online` no longer shows an obvious delayed hero image on normal broadband.
- `npm run web:test`, `npm run web:lint`, and `npm run web:build` pass.
- Documentation records what changed and how it was verified.

## Implementation Notes For The Detailed Plan

- Start by locating current hero usage in `apps/web/src/` and current assets in `apps/web/public/assets/`.
- Prefer standard browser image behavior: `picture`, `source`, `srcset`, `sizes`, or equivalent React markup.
- Avoid introducing a new image pipeline unless the existing toolchain already supports it cleanly.
- If using CLI image conversion tools, document whether they are repo dependencies, system tools, or one-off generation commands.
- Preserve the original source-quality asset only if it is useful for future regeneration; otherwise avoid carrying duplicate oversized runtime assets.
