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

The local provider is deterministic for testability. Live OpenAI-compatible provider calls, retry policy, rate limiting, and provider observability remain later production-hardening work.
