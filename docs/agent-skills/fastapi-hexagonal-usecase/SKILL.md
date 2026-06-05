---
name: fastapi-hexagonal-usecase
description: Use when adding FastAPI endpoints, application use cases, persistence adapters, schemas, or tests inside the CoffeeFix Pro DDD and hexagonal backend.
---

# FastAPI Hexagonal Use Case

## Context To Open

- `ARCHITECTURE.md`
- `docs/architecture/domain-architecture.md`
- Relevant `domains/<domain>/AGENTS.md`
- Relevant phase plan in `docs/execution-plans/phases/`

## Pattern

Keep API, application, domain, and infrastructure concepts separate. API routes translate HTTP into application commands or queries. Application handlers coordinate ports and domain objects. Infrastructure implements ports.

## Implementation Shape

```text
api/rest
  -> application/commands or queries
  -> application/handlers
  -> domain/model
  -> application/ports
  <- infrastructure/adapters
```

## Test Focus

- Domain behavior without database.
- Application use case with fake ports.
- API contract with test client.
- Persistence adapter with database when needed.
