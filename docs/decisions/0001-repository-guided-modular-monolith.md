# ADR 0001: Repository-Guided Modular Monolith

## Status

Accepted.

## Context

The project is a pet project for building practical skills in Python, REST APIs, SQL, RAG, assisted workflows, Telegram, n8n, Docker Compose, Dokploy, and VPS deployment. Repository-local context replaces chat memory.

## Decision

The system will start as a modular monolith using DDD and hexagonal architecture. The repository will include readable maps, domain docs, execution plans, review protocol, and repo-specific workflow drafts.

## Rationale

A modular monolith keeps deployment and learning manageable while still giving contributors clear domain boundaries. Harness documentation gives future work enough context to continue without relying on prior conversations.

## Consequences

- Domain boundaries are represented through folders and documentation before complex enforcement is introduced.
- Phase plans define small slices that can be reviewed independently.
- Repo-specific workflow drafts live in `docs/agent-skills` until the local skill directory is ready.
