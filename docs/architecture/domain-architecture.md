# Domain Architecture

## Architectural Style

The backend uses DDD and hexagonal architecture inside a modular monolith. This keeps the learning and deployment surface manageable while providing strict conceptual boundaries.

## Domain Boundary Contract

Each domain owns its vocabulary, entities, value objects, events, application use cases, and ports. Integrations with databases, AI providers, Telegram, n8n, or other systems are adapters.

## Shared Kernel

`packages/shared-kernel` contains concepts that are stable and shared across domains, such as identifiers, time abstractions, result types, and event base types.

## Example Dependency Direction

```text
api/rest
  → application/handlers
    → domain/model
    → application/ports
      ← infrastructure/adapters
```

Infrastructure implements ports. Domain logic does not import API routers, ORM models, Telegram clients, or LLM clients.

## Initial Domain Priority

1. Service requests.
2. Customers.
3. Machines.
4. Notifications.
5. Technicians and scheduling.
6. Knowledge base.
7. AI agents.
8. Inventory.
9. Billing.
