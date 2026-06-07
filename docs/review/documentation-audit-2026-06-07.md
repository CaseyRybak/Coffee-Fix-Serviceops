# Documentation Audit 2026-06-07

## Scope

Reviewed the repository entry documents, architecture docs, product scope, execution-plan index, phase/review artifacts, domain maps, operations runbooks, and documentation harness checks after Phase 10.

## Findings Fixed

- `README.md` overstated implemented notification/deployment behavior. It now distinguishes Telegram opt-in contracts, n8n workflow design records, and deployment artifacts from live delivery automation.
- `ARCHITECTURE.md` still described dispatcher UI as future work. It now reflects the current web workspaces and operations migration entry point.
- `docs/architecture/tech-stack.md` listed SQLAlchemy and Alembic as current stack components even though the code uses `sqlite3`, `psycopg`, and hand-written SQL migrations. It now records the actual implementation and keeps SQLAlchemy/Alembic as deferred choices.
- `docs/product/mvp-scope.md` implied outbound status notifications were implemented. It now describes Telegram opt-in plus notification workflow design, with delivery deferred.
- `domains/notifications/domain.md` lacked the Phase 10 n8n boundary. It now states that n8n workflow design exists but backend webhook emission and Telegram token consumption remain future work.
- `domains/service-requests/domain.md` did not spell out the current public status API paths. It now records the request-number and token status endpoints used by web and smoke tests.
- `docs/operations/deployment-runbook.md` implied production staff bootstrap was executable, but the current seed command is local-only. It now marks first-admin bootstrap as a public-launch prerequisite.
- `docs/review/phase-10-review.md` duplicated the smoke-script contract file and verification command. The duplicates were removed and the production staff bootstrap gap was recorded.
- `project_notes.md` now calls out production first-admin bootstrap as a next step and recent decision.
- `project_notes.md` was too long for an entry dashboard. It is now a compact current-state file, with historical chronology and deferred work moved to `docs/harness/project-history.md`.
- `AGENTS.md`, `docs/harness/repository-map.md`, `docs/agent-skills/agent-context-gardening/SKILL.md`, and `docs/review/subagent-review-protocol.md` now use the new split between current dashboard and project history.

## Current Documentation Quality

The documentation harness is strong for project continuity: entry points are clear, phase plans and review artifacts are discoverable, domain maps exist for every domain, and operations docs now cover deployment, backups, smoke tests, n8n boundaries, and production caveats.

The main quality risk is that historical phase plans are intentionally preserved and can mention deferred work or old review gates in their original context. Contributors should treat `project_notes.md`, `docs/execution-plans/index.md`, and the latest review artifacts as the source of current status.

## Remaining Gaps

- No production-safe first-admin bootstrap command exists yet.
- No backend-to-n8n webhook emission exists yet.
- No real Dokploy/VPS smoke-test results are recorded.
- No log shipping, alerting, or uptime monitoring guidance beyond stdout/Dokploy logs exists yet.
- Keep `project_notes.md` and `docs/harness/project-history.md` synchronized when future phases complete.

## Score

Documentation quality after this audit and the `project_notes.md` split: 8.6/10.

Rationale: the repository is navigable and implementation-ready for the next slice, with good review and operations coverage. The score is capped by production launch gaps, the need to keep current notes and history synchronized, and the absence of real deployment smoke-test evidence.
