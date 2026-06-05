# Phase 05: Knowledge Base RAG

> For agentic workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Build the first RAG knowledge base for coffee machine repair documents.

## Context To Read

- `domains/knowledge-base/AGENTS.md`
- `domains/knowledge-base/domain.md`
- `docs/architecture/tech-stack.md`

## Deliverables

- Knowledge document model.
- Chunk model.
- pgvector migration.
- Ingestion command or API.
- Embedding job in worker.
- Retrieval endpoint with source metadata.
- Seed repair knowledge document.

## Acceptance Criteria

- A text document can be ingested.
- Chunks are persisted with embeddings.
- Retrieval returns relevant chunks and source metadata.
- Tests cover chunking and retrieval contract using deterministic test data.
- `project_notes.md` identifies Phase 06 as the next active phase.

## Subagent Review Gate

Review RAG data boundaries, source traceability, worker behavior, and whether AI provider calls are isolated behind ports.
