# Phase 17 Review: Public Demo And Launch Closure

Date: 2026-06-17

## Reviewer Role

Phase closure review based on the documented production evidence, repository checks, and operator-confirmed smoke results. This review records the Phase 17 handoff state for future workers; it does not represent a separate implementation slice.

## Files Reviewed

- `docs/execution-plans/phases/17-public-demo-and-launch-closure.md`
- `docs/execution-plans/detailed/17-public-demo-and-launch-closure-implementation.md`
- `docs/operations/public-demo-launch-evidence.md`
- `docs/operations/deployment-runbook.md`
- `docs/operations/smoke-tests.md`
- `docs/operations/operational-diagnostics.md`
- `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`
- `docs/execution-plans/index.md`
- `project_notes.md`

## Verification Commands

- `python3 tools/repo-checks/check_docs.py` -> passed.
- `git diff --check` -> passed.
- Public web HTTPS route `https://coffeefix-demo.online/` -> passed during Phase 17 evidence capture.
- Public API health route `https://api.coffeefix-demo.online/health` -> passed during Phase 17 evidence capture.
- Public intake and status smoke -> passed during Phase 17 evidence capture.
- Staff login and role-appropriate internal workspaces -> passed manually with a newly created staff user.
- n8n request-created delivery -> passed during Phase 17 evidence capture.
- Telegram opt-in ownership -> passed manually with production bot polling on the VPS and local Docker stopped.
- Backup command readiness -> passed during Phase 17 evidence capture.
- Restore dry-run readiness -> passed by non-destructive readiness audit.

## Blocking Issues

None for the current pet-project public demo posture.

## Non-Blocking Issues

- The hero image is visibly slow on first uncached load and should be optimized before portfolio screenshots or demo packaging.
- The current public demo uses a pet-project posture. A stricter commercial launch would need a separate production hardening review.
- The real database transfer remains outside this phase; repeat smoke and backup checks after any real data import.

## Public Demo Decision

Go for current pet-project public demo posture.

## Suggested Follow-Up Slice

Phase 17a: optimize the first-load hero/static assets on the public demo before portfolio packaging.

## Documentation Updates

Completed:

- Public domain, HTTPS, direct-port guard, Dokploy access restriction, smoke, n8n, Telegram, backup, and restore-readiness evidence recorded in `docs/operations/public-demo-launch-evidence.md`.
- Phase 17 closure recorded in this review artifact.
- Phase index and project notes point to Phase 17a as the next active focus.

## Final Recommendation

Phase 17 is closed for the current pet-project public demo posture. The public web and API routes work over HTTPS, direct test ports are blocked externally, Dokploy access is restricted to the operator IP, staff-route smoke was confirmed, n8n and Telegram production paths were verified, and backup/restore readiness is documented. Proceed to Phase 17a before portfolio packaging.
