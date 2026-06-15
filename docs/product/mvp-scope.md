# MVP Scope

## MVP Includes

- Public page based on `reference/figma`.
- Short repair request form.
- Request number generation.
- Client status page.
- Dispatcher request list and request card.
- Manual status transitions.
- Manual technician assignment.
- Telegram opt-in linking, backend-to-n8n notification events, delivery-result persistence, and staff-visible delivery status.
- PostgreSQL persistence.
- Source-backed RAG document ingestion with pgvector, curated repair seed content, relevance filtering, and explicit knowledge-gap fallback when the seed base does not cover a new symptom.
- AI workflows for intake classification, diagnostic questions, likely causes, parts hints, and customer reply drafts, with deterministic local providers, configurable OpenAI-compatible live providers, safety-first triage for hazardous symptoms, and staff review before any operational action.
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
- Automatic technician assignment without confirmation.
- Precise AI cost estimation.
- Autonomous AI decisions without staff confirmation.
- Advanced inventory procurement.
- Billing automation.
- Telephony integration.
- Kubernetes.
