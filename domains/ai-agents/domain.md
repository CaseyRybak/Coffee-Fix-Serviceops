# AI Agents Domain

## Responsibility

This domain coordinates bounded AI workflows. AI produces suggestions and drafts. Dispatchers or technicians confirm important actions.

## First Workflows

- Intake classification.
- Diagnostic question suggestion.
- Likely cause suggestion.
- Likely parts suggestion.
- Customer-friendly reply draft.

## Phase 07 Behavior

AI workflows create dispatcher-reviewed suggestions, not confirmed operational decisions. Suggestions are stored separately from service-request statuses, assignment metadata, internal notes, public clarification questions, and public status snapshots.

The first suggestion kinds are intake classification, diagnostic question, likely cause, parts, and customer reply draft. A dispatcher can accept a diagnostic-question suggestion, which creates a normal customer-visible clarification question through the service-request lifecycle. Other suggestions can be ignored or used manually by staff.

Prompt input assembly excludes customer phone and Telegram handles. Diagnostic and likely-cause suggestions may include knowledge-base source chunks, and those sources remain visible to dispatchers for traceability.

## Phase 13 Live Provider Behavior

The local/test provider remains deterministic for testability. Production can select an OpenAI-compatible chat provider through environment configuration without changing application code.

Live provider prompts are assembled from the existing safe `AiPromptInput` boundary. They exclude customer phone numbers, Telegram handles, technician phone numbers, internal note bodies, notification delivery errors, and shared secrets. Provider failures surface generic operator-safe errors and must not log raw prompts, API keys, provider request bodies, or provider response bodies.

Live AI output is still only a dispatcher-reviewed suggestion. It never changes service-request lifecycle state, assignment state, inventory reservations, notifications, or customer-visible content unless a staff member explicitly accepts an allowed suggestion through the normal use case.

## Current RAG Fallback Behavior

Prompt assembly filters retrieved knowledge chunks before provider calls. A chunk must share enough topic terms with the customer problem, or match a guarded safety topic such as electrical shock, before it is included as a source. This prevents a high-scoring but semantically wrong repair document from steering the dispatcher toward an unrelated scenario.

When no relevant source chunk remains, the provider prompt labels the request as having no relevant RAG coverage. The deterministic provider returns generic, symptom-grounded clarification suggestions. The live provider is instructed to treat the request as `knowledge_gap=true`, leave `source_chunk_indexes` empty, avoid using similar but different scenarios as facts, and base hypotheses on the customer's description plus safe repair triage.
