# Execution Plan Index

Work is split into phases. Each phase is a reviewable implementation slice and should be completed before the next phase starts.

## Planning Policy

Before executing any phase, create a detailed implementation plan for that specific phase. The detailed plan should define files, tests, commands, verification steps, and subagent review checkpoints. Do this just in time for the next phase instead of fully detailing all future phases upfront.

## Active Phase

- `phases/03-client-status-and-notifications.md`

The active phase points to the next phase that needs a detailed implementation plan before execution. `phases/` contains all phase slice maps, not only active work.

## Detailed Plans

Detailed implementation plans are created just in time in `detailed/`. Completed detailed plans: `detailed/00-repository-harness-implementation.md`, `detailed/01-foundation-runtime-implementation.md`, `detailed/02-service-request-intake-implementation.md`.

## Phase Sequence

1. `phases/00-repository-harness.md`: repository harness, docs, maps, and review loop.
2. `phases/01-foundation-runtime.md`: backend, frontend, database, Docker Compose, and healthchecks.
3. `phases/02-service-request-intake.md`: request intake API and public form integration.
4. `phases/03-client-status-and-notifications.md`: status page, status timeline, Telegram opt-in.
5. `phases/04-dispatcher-mvp.md`: dispatcher request list, request card, assignment, clarification.
6. `phases/05-knowledge-base-rag.md`: RAG documents, chunks, embeddings, retrieval with sources.
7. `phases/06-ai-agent-workflows.md`: intake, diagnostic, parts, dispatcher, and reply workflows.
8. `phases/07-technician-and-inventory.md`: technician mobile flow and basic parts tracking.
9. `phases/08-deployment-and-operations.md`: Dokploy deployment, backups, observability, n8n flows.

## Review

Each phase ends with the review protocol in `docs/review/subagent-review-protocol.md`.
