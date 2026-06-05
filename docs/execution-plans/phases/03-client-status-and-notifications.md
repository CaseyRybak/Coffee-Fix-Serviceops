# Phase 03: Client Status And Notifications

> For agentic workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Give clients a public request status page and initial Telegram notification path.

## Context To Read

- `domains/service-requests/domain.md`
- `domains/notifications/AGENTS.md`
- `domains/notifications/domain.md`
- `docs/product/figma-reference-review.md`

## Deliverables

- Status event model.
- Public status API endpoint.
- Status page UI with timeline.
- Clarification question display.
- Customer answer submission.
- Telegram opt-in token or link concept.
- Basic notification event adapter.

## Acceptance Criteria

- A client can open status by request number or public token.
- Status page shows current status, history, and clarification question if present.
- Customer answer is recorded.
- Telegram opt-in flow has a defined backend contract.
- Tests cover status retrieval and answer submission.
- `project_notes.md` identifies Phase 04 as the next active phase.

## Subagent Review Gate

Review public access safety, status timeline clarity, notification boundaries, and user-facing copy.
