# ADR 0001: Agent-First Modular Monolith

## Status

Accepted.

## Context

The project is a pet project for building practical skills in Python, REST APIs, SQL, RAG, AI agents, Telegram, n8n, Docker Compose, Dokploy, and VPS deployment. It must also be developed primarily through AI agents, with repository-local context replacing chat memory.

## Decision

The system will start as a modular monolith using DDD and hexagonal architecture. The repository will include agent-readable maps, domain docs, execution plans, review protocol, and repo-specific skill drafts.

## Rationale

A modular monolith keeps deployment and learning manageable while still giving agents clear domain boundaries. Harness documentation gives future agents enough context to continue work without relying on prior conversations.

## Consequences

- Domain boundaries are represented through folders and documentation before complex enforcement is introduced.
- Phase plans define small slices that can be reviewed independently.
- Repo-specific skills live in `docs/agent-skills` until `.agents/skills` is writable.

