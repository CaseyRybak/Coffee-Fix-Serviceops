# Phase 23 Review: Technician Recommendation Lite

## Review Scope

Phase 23 was intentionally completed as a Lite implementation for portfolio MVP value:

- technician profiles linked to staff accounts;
- admin-maintained recommendation-active state, brand skills, service regions, and internal notes;
- dispatcher-visible deterministic recommendations with reasons and risks;
- optional requested appointment-window conflict checks;
- no automatic assignment, AI-owned assignment, GPS, route optimization, durable availability calendar, ratings, payroll, or part-readiness scoring.

Reviewed files included backend technician profile/recommendation code, the PostgreSQL migration, migration runner wiring, dispatcher/admin frontend surfaces, frontend DTO/path contracts, phase/domain docs, and the detailed implementation plan.

## Verification Commands

Fresh verification in the implementation session:

```bash
python3 tools/repo-checks/check_docs.py
cd apps/api && uv run --extra dev pytest
npm run web:test -- --run
npm run web:lint
npm run web:build
```

Observed results:

- Documentation harness check passed.
- API suite passed: 182 tests, 1 existing FastAPI deprecation warning.
- Web test suite passed: 54 tests.
- Web TypeScript lint passed.
- Web production build passed.

Independent backend reviewer also ran:

```bash
cd apps/api && uv run --extra dev pytest tests/test_technician_profiles.py tests/test_operations_migrate.py -q
```

Observed result: 10 tests passed.

## Independent Reviewers

- Backend/API/database reviewer: checked sqlite/PostgreSQL persistence, migration runner wiring, recommendation read-only behavior, authorization, public snapshot boundary, and deterministic explainability.
- Frontend/UI reviewer: checked admin profile editing, dispatcher recommendation surface, path/DTO contracts, rendering/layout risks, and frontend tests.
- Product/docs reviewer: checked Lite scope, deferred work, documentation handoff, and review closure readiness.

## Blocking Issues

None.

## Non-Blocking Issues And Resolution

- Backend reviewer noted that risky candidates could rank above viable available technicians because inactive profiles and scheduling conflicts were only represented as risks, not score penalties.
  - Resolution: recommendation scoring now penalizes inactive staff/profile and requested-window conflicts, with regression coverage ensuring a viable available technician ranks above a conflicted brand/region match.

- Product/docs reviewer noted a stale `project_notes.md` decision saying Phases 23-24 were still roadmap-level slice maps.
  - Resolution: `project_notes.md` now marks Phase 23 Lite complete and leaves only Phase 24 as roadmap-level pending detailed planning.

- Frontend reviewer noted `ProtectedAdminPage` did not pass preloaded `initialTechnicianProfiles` into `AdminPage`.
  - Resolution: the prop is now passed through, with regression coverage using unique profile values.

- Frontend reviewer noted that admin auth-refresh behavior is less consistent than dispatcher auth-refresh behavior.
  - Resolution: not changed in this phase because the issue affects multiple staff workspaces beyond Phase 23. Track as follow-up.

- Frontend reviewer noted that browser-style interaction coverage for “save technician profile” and “use recommendation in form” would be stronger than current SSR/helper tests.
  - Resolution: not required to close this Lite phase because backend API, path/DTO, SSR visibility, and helper behavior are covered. Track as follow-up.

## Suggested Follow-Up Slice

- Normalize staff-auth failure handling across admin, owner, inventory, dispatcher, and technician workspaces.
- Add browser-style frontend interaction tests with mocked `fetch` for admin technician-profile save and dispatcher recommendation selection.
- Proceed to Phase 24 bounded staff AI assistant with safe tool use and human confirmation; keep technician recommendations deterministic and backend-owned.

## Documentation Updates

Updated:

- `project_notes.md`
- `docs/execution-plans/index.md`
- `docs/execution-plans/phases/23-technician-profiles-and-recommendation.md`
- `docs/execution-plans/detailed/23-lite-technician-recommendation-foundation.md`
- `domains/technicians/domain.md`
- `domains/service-requests/domain.md`

Public/private boundary is documented: public status snapshots must not expose technician profile skills, service regions, recommendation scores, workload diagnostics, scheduling conflict reasons, or recommendation explanations.

## Final Recommendation

Phase 23 Lite is approved and ready to close.

The slice meets its MVP/portfolio goal: it adds useful, explainable technician recommendations without turning the product into a full workforce-management system and without weakening the human-confirmation boundary.

## Follow-Up Consistency Recheck: 2026-06-19

Reviewer roles:

- Backend/API/database reviewer rechecked profile lifecycle, authorization, migration wiring, read-only recommendations, deterministic ranking, and public status boundaries.
- Frontend/UI reviewer rechecked admin profile editing, dispatcher recommendation display, manual-prefill behavior, and frontend path/DTO contracts.
- Product/docs reviewer rechecked phase status, Lite scope language, portfolio-demo boundaries, and Phase 24 handoff.

Blocking issues: none.

Non-blocking issues resolved during recheck:

- `domains/technicians/domain.md` had historical Phase 08/15 wording that still said technician profiles were deferred; it now describes those statements as historical and points region/skill data to Phase 23 Lite.
- `docs/product/portfolio-demo-guide.md` listed richer technician recommendations as not shipped; it now distinguishes shipped Phase 23 Lite deterministic recommendations from deferred full workforce-management recommendations.
- `domains/technicians/AGENTS.md` implied AI agents already suggest technicians; it now says Phase 24+ AI may consume backend-owned technician recommendations.
- `docs/execution-plans/detailed/23-lite-technician-recommendation-foundation.md` had unchecked task boxes despite being listed as completed; it now includes a completion note that the checkboxes are preserved as the original execution plan.
- Frontend recommendation selection now has a tested helper that maps a recommendation into manual assignment/appointment form fields only.
- Admin technician-profile editing is gated by persisted staff roles instead of unsaved local role drafts.
- Dispatcher recommendation cards show all returned reasons and risks for the displayed candidates, so risk notes are not silently hidden.
- Backend recommendation tests now cover unauthenticated/wrong-role recommendation access and inactive staff ranking/risk behavior.
- Backend recommendation sorting now includes `staff_username` as an explicit final deterministic tie-break.
- Migration tests now assert the Phase 23 technician profile DDL contract.

Remaining non-blocking follow-ups:

- Browser-style frontend interaction tests would still be stronger than the current lightweight `node:test`/SSR suite, but the project does not currently include a DOM test harness.
- Per-item maximum lengths for technician brand/region strings could be added as a small API hardening follow-up.
