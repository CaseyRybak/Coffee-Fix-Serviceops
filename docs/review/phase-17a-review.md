# Phase 17a Review: Demo Performance And Hero Image Optimization

Date: 2026-06-17

## Reviewer Role

Phase closure review for the small public-demo performance slice. The operator explicitly treated Phase 17a as a simple direct fix, so no separate detailed implementation plan was created for this slice.

## Files Reviewed

- `docs/execution-plans/phases/17a-demo-performance-and-hero-image-optimization.md`
- `apps/web/src/App.tsx`
- `apps/web/src/App.test.tsx`
- `apps/web/src/styles.css`
- `apps/web/public/assets/hero-coffee-service-wide-desktop.webp`
- `apps/web/public/assets/hero-coffee-service-wide-mobile.webp`
- `docs/operations/public-demo-launch-evidence.md`
- `docs/execution-plans/index.md`
- `project_notes.md`

## Verification Commands

- `npm run web:test` -> passed.
- `npm run web:lint` -> passed.
- `npm run web:build` -> passed.
- `git diff --check` -> passed.
- Playwright desktop check -> browser selected `/assets/hero-coffee-service-wide-desktop.webp`.
- Playwright mobile check -> browser selected `/assets/hero-coffee-service-wide-mobile.webp`.
- Playwright screenshots saved under `output/playwright/` during local verification and visually confirmed that the hero image remained uncropped.

## Asset Size Evidence

| Asset | Dimensions | Size |
| --- | ---: | ---: |
| Original PNG fallback | 1514x941 | 1,865,388 bytes |
| Desktop WebP | 1514x941 | 118,892 bytes |
| Mobile WebP | 800x497 | 45,770 bytes |

## Blocking Issues

None.

## Non-Blocking Issues

- Production redeploy is still required before the live domain can serve the optimized assets.
- The original PNG remains as a browser fallback. It is not expected to be downloaded by modern browsers that support WebP.

## Suggested Follow-Up Slice

Phase 18: portfolio packaging and demo mode.

## Documentation Updates

Completed:

- Phase 17a closure recorded in this review artifact.
- Public demo launch evidence records the hero asset optimization result.
- Phase index and project notes point to Phase 18 as the next active focus.

## Final Recommendation

Phase 17a is closed. The public hero image now uses responsive WebP assets for desktop and mobile while preserving the original PNG fallback and the existing visual composition. Proceed to Phase 18 after redeploying the current `main` branch to the public demo environment.
