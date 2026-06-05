---
name: rag-knowledge-ingestion
description: Use when adding CoffeeFix Pro knowledge documents, chunking, embeddings, pgvector retrieval, source metadata, or RAG-backed repair answers.
---

# RAG Knowledge Ingestion

## Context To Open

- `domains/knowledge-base/AGENTS.md`
- `domains/knowledge-base/domain.md`
- `docs/architecture/tech-stack.md`
- Phase 06 plan.

## Pattern

Treat RAG as a domain with documents, chunks, embeddings, retrieval results, and source metadata. Retrieval should return useful text and traceable sources.

## Document Metadata

Capture:

- Title.
- Source type.
- Brand, if relevant.
- Model, if relevant.
- Issue category, if relevant.
- Version or effective date when known.

## Test Focus

- Chunking is deterministic.
- Retrieval contract returns source metadata.
- Provider calls are behind ports so tests can use fakes.
