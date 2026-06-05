# Phase 00: Repository Harness

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Stabilize the repository as a legible system of record before application code is generated.

## Context To Read

- `AGENTS.md`
- `project_notes.md`
- `ARCHITECTURE.md`
- `docs/architecture/harness-engineering.md`
- `docs/review/subagent-review-protocol.md`

## Deliverables

- Git repository initialized if absent.
- Root documentation map reviewed for broken links.
- `project_notes.md` updated with the active next phase.
- Basic repo check script in `tools/repo-checks`.
- Documentation structure listed in `docs/harness/repository-map.md`.

## Acceptance Criteria

- A new contributor can identify current status, active phase, product vision, architecture, and review protocol in under five file opens.
- All linked documents from `AGENTS.md` exist.
- `project_notes.md` points to Phase 01 when this phase is complete.
- Subagent review finds no missing phase-critical harness documents.

## Subagent Review Gate

Run Review 1 for plan compliance and Review 2 for architecture/readability. Resolve blocking issues before Phase 01.
