# MVP Scope

## MVP Includes

- Public page based on `reference/figma`.
- Short repair request form.
- Request number generation.
- Client status page.
- Dispatcher request list and request card.
- Manual status transitions.
- Manual technician assignment.
- Structured appointment scheduling and technician schedule visibility.
- Technician protected workflow for assigned visits, diagnosis, repair result, and parts used.
- Inventory catalog, stock, compatibility, request-linked reservations, stock movement history, and low-stock visibility.
- Internal owner dashboard, SLA deadlines, overdue/near-deadline state, and daily report data.
- Lightweight procurement workflow for suppliers and purchase-request drafts, approvals, ordering, receiving, and cancellation.
- Deterministic technician recommendation lite with profile skills, regions, workload, and scheduling-conflict reasons.
- Telegram opt-in linking, backend-to-n8n notification events, delivery-result persistence, and staff-visible delivery status.
- Operational n8n automation for SLA reminders, red alerts, owner daily reports, and low-stock alerts.
- PostgreSQL persistence.
- Source-backed RAG document ingestion with pgvector, curated repair seed content, relevance filtering, and explicit knowledge-gap fallback when the seed base does not cover a new symptom.
- AI workflows for intake classification, diagnostic questions, likely causes, parts hints, and customer reply drafts, with deterministic local providers, configurable OpenAI-compatible live providers, safety-first triage for hazardous symptoms, and staff review before any operational action.
- Bounded staff AI assistant for safe read-only tools and inventory-staff confirmed purchase-draft creation.
- Docker Compose local environment.

## First Request Form Fields

- Name.
- Phone.
- Telegram handle, optional.
- Client type.
- Brand.
- Problem description.
- District or address.
- Urgency.
- Photo or video attachment, optional.

## Deferred Scope

- Full client account.
- Automatic technician assignment without dispatcher confirmation.
- Precise AI cost estimation.
- Autonomous AI decisions without staff confirmation.
- Advanced inventory procurement beyond the lightweight internal workflow.
- Billing automation.
- Telephony integration.
- Kubernetes.
