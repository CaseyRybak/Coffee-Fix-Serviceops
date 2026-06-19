# Architecture

## System Shape

The project is a modular monolith with DDD and hexagonal architecture. The monolith keeps local development, testing, and deployment simple while preserving domain boundaries for readability.

## Applications

- `apps/api`: FastAPI REST API plus operational migration entry points.
- `apps/web`: React/Vite public site, status page, dispatcher workspace, technician workspace, inventory/procurement workspace, owner dashboard, staff AI assistant, and admin workspace.
- `apps/worker`: Celery background jobs for embeddings and operational maintenance.
- `apps/telegram-bot`: aiogram bot for Telegram opt-in token consumption and customer notification linking.

## Domain Areas

- `service-requests`: repair request lifecycle from intake to closure.
- `customers`: customer identity, contact channels, and B2B organization context.
- `machines`: coffee machine brands, models, installation context, and history.
- `technicians`: technician profile, skills, regions, and availability.
- `scheduling`: appointment windows and visit coordination.
- `inventory`: parts, stock, compatibility, reservations, suppliers, and lightweight procurement.
- `knowledge-base`: documents, chunks, embeddings, and RAG retrieval.
- `ai-agents`: intake, diagnostic, parts, dispatcher, reply, and bounded staff assistant workflows.
- `notifications`: Telegram, n8n webhooks, and message delivery.
- `billing`: estimates, repair totals, acts, warranty, and payment metadata.

## Layering

Each domain follows this local shape:

```text
domain/
  model/
  value_objects/
  events/
  services/
application/
  commands/
  queries/
  handlers/
  ports/
infrastructure/
  persistence/
  integrations/
api/
  rest/
AGENTS.md
domain.md
plans/
decisions/
```

Domain code represents business concepts. Application code coordinates use cases. Infrastructure code adapts persistence and external integrations. API code exposes HTTP contracts.

## Context Flow For Contributors

```text
AGENTS.md
→ project_notes.md
→ ARCHITECTURE.md
→ docs/execution-plans/index.md
→ domains/<domain>/AGENTS.md
→ domains/<domain>/domain.md
→ relevant code and tests
```
