# ADR 0003: PostgreSQL And pgvector For RAG

## Status

Accepted.

## Context

The project should strengthen SQL skills while also implementing a RAG knowledge base. A separate vector database would add operational surface before the product needs it.

## Decision

Use PostgreSQL as the primary database and pgvector for embeddings in the MVP.

## Rationale

This keeps persistence centralized, supports SQL learning goals, and is sufficient for the first RAG workflows.

## Consequences

- Knowledge documents, chunks, and vectors live in PostgreSQL.
- Retrieval behavior is implemented behind application ports.
- A separate vector database can be introduced later if scale or retrieval requirements justify it.

