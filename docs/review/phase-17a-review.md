# Phase 17a Review: Demo Performance And Hero Image Optimization

Date: 2026-06-17

## Reviewer Role

Phase closure review for the small public-demo performance slice. The operator explicitly instructed the worker not to create a separate detailed implementation plan for Phase 17a, so this slice intentionally used the phase map plus review artifact as the durable record.

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

- Live-domain HEAD checks on 2026-06-17 confirmed the public web route and both WebP assets are available from `https://coffeefix-demo.online`; repeat browser selection checks after future web redeploys that touch hero assets.
- The original PNG remains as a browser fallback. It is not expected to be downloaded by modern browsers that support WebP.
- No separate detailed implementation plan was created for Phase 17a by direct operator instruction. This is not a Phase 17a finding or score penalty; future slices should still follow the normal detailed-plan policy unless the operator explicitly overrides it again.

## Suggested Follow-Up Slice

Phase 18: portfolio packaging and demo mode.

## Documentation Updates

Completed:

- Phase 17a closure recorded in this review artifact.
- Public demo launch evidence records the hero asset optimization result.
- Phase index and project notes point to Phase 18 as the next active focus.

## Final Recommendation

Phase 17a is closed for the current public demo posture. The public hero image now uses responsive WebP assets for desktop and mobile while preserving the original PNG fallback and the existing visual composition, and the optimized WebP assets are available on the live domain.
