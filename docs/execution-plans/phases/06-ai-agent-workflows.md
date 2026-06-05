# Phase 06: AI Agent Workflows

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Introduce bounded AI workflows that assist dispatchers without making critical decisions automatically.

## Context To Read

- `domains/ai-agents/AGENTS.md`
- `domains/ai-agents/domain.md`
- `domains/service-requests/domain.md`
- `domains/knowledge-base/domain.md`

## Deliverables

- Intake classification workflow.
- Diagnostic question suggestion workflow.
- Likely cause suggestion workflow.
- Parts suggestion workflow stub connected to inventory concepts.
- Customer reply draft workflow.
- AI suggestion persistence.
- Dispatcher UI surface for accepting or ignoring suggestions.

## Acceptance Criteria

- AI suggestions are stored separately from confirmed human actions.
- Dispatcher can view AI suggestions on request detail.
- Suggested questions can be converted into customer-visible clarification questions.
- RAG context can be included in diagnostic workflow.
- Tests cover prompt input assembly and suggestion lifecycle without requiring live LLM calls.
- `project_notes.md` identifies Phase 07 as the next active phase.

## Subagent Review Gate

Review human-in-the-loop behavior, prompt context clarity, testability without live providers, and separation from domain decisions.
