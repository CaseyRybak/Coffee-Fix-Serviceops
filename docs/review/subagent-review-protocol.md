# Subagent Review Protocol

## Purpose

Every implementation slice should be small enough to review independently. Subagent review catches drift from the plan, architecture, product intent, and Figma reference before the next slice starts.

## Review Points

Run review after a slice is implemented and local verification has completed.

## Reviewer Role

A subagent reviewer is an independent reviewer for the slice. It can be another session or a human reviewer, but it must not be the same worker that implemented the slice. The reviewer should receive only repository context, the active phase plan, the detailed implementation plan, the verification output, and the diff or changed-file list.

The reviewer does not continue implementation during review. The reviewer evaluates whether the slice can safely move forward and reports findings using the output format below.

## Review 1: Plan Compliance

The reviewer checks:

- The implemented files match the active phase scope.
- Acceptance criteria in the phase plan are satisfied.
- Deferred work stayed deferred.
- `project_notes.md` reflects the new status.
- Domain docs were updated when domain behavior changed.

## Review 2: Architecture And Quality

The reviewer checks:

- DDD/hexagonal boundaries are understandable.
- Domain code does not depend on infrastructure details.
- API contracts are explicit.
- Tests cover the implemented behavior.
- The implementation remains legible to future contributors.

## Review Output

Review findings should be grouped as:

- Blocking issues.
- Non-blocking issues.
- Suggested follow-up slice.
- Documentation updates needed.

Store review results as a durable artifact when a phase is marked complete. Use `docs/review/phase-XX-review.md` for the phase-level review summary, including reviewer role, files reviewed, verification commands, findings, and final recommendation.

## Slice Completion

A slice is complete when blocking review issues are resolved, verification commands pass, and `project_notes.md` points to the next active focus or next approved phase.
