# MVP Scope

## MVP Includes

- Public page based on `reference/figma`.
- Short repair request form.
- Request number generation.
- Client status page.
- Dispatcher request list and request card.
- Manual status transitions.
- Manual technician assignment.
- Telegram opt-in contract and notification workflow design. Outbound Telegram/n8n delivery remains deferred until a notification delivery slice.
- PostgreSQL persistence.
- Basic RAG document ingestion with pgvector.
- First AI workflows for intake classification and diagnostic questions.
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
- Advanced inventory procurement.
- Billing automation.
- Telephony integration.
- Kubernetes.
