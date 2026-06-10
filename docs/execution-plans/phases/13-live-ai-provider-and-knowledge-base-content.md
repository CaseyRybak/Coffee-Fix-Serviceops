# Phase 13: Live AI Provider And Knowledge Base Content

> For implementation workers: implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Replace deterministic AI/embedding providers with production-configurable live provider adapters and populate the knowledge base with useful, source-backed repair content.

## Context To Read

- `domains/ai-agents/AGENTS.md`
- `domains/ai-agents/domain.md`
- `domains/knowledge-base/AGENTS.md`
- `domains/knowledge-base/domain.md`
- `docs/architecture/tech-stack.md`
- `docs/execution-plans/phases/06-knowledge-base-rag.md`
- `docs/execution-plans/phases/07-ai-agent-workflows.md`
- `docs/execution-plans/phases/12-notification-automation.md`

## Deliverables

- OpenAI-compatible chat/LLM suggestion provider adapter behind the existing AI suggestion provider port.
- OpenAI-compatible embedding provider adapter behind the existing embedding provider port.
- Production configuration for provider selection, model names, API base URL, API key secrets, request timeout, and suggestion limits.
- Retry, rate-limit, timeout, and provider-error handling that does not expose secrets or raw sensitive prompts in logs.
- Knowledge-base ingestion workflow for real repair content, including source URI/title metadata and operator-facing import guidance.
- Initial curated repair knowledge set for common coffee-machine symptoms, brands, maintenance concepts, and diagnostic procedures.
- RAG quality/evaluation fixture with representative queries and expected source-backed retrieval behavior.
- Tests covering provider selection, prompt/payload assembly, provider failure handling, embedding adapter contracts, ingestion metadata, and evaluation fixtures without requiring live provider calls.

## Acceptance Criteria

- Production can be configured to use live LLM and embedding providers without changing application code.
- Local development and automated tests can still use deterministic providers without external network calls.
- Missing live-provider secrets fail clearly in production-oriented configuration while remaining optional for deterministic local/test mode.
- AI suggestions remain internal staff-reviewed artifacts and never mutate service requests, notify customers, reserve inventory, or assign technicians automatically.
- Dispatcher-visible AI suggestions retain source metadata when RAG context supports the output.
- Knowledge-base content has traceable source metadata and avoids storing unrelated sensitive customer or staff data.
- RAG evaluation fixtures demonstrate useful retrieval for common repair questions before relying on live AI output quality claims.
- `project_notes.md` identifies Phase 14 as the next active phase after implementation.

## Subagent Review Gate

Review provider security, secret handling, deterministic test isolation, prompt/privacy boundaries, KB source quality, RAG evaluation usefulness, and whether live AI remains safely human-in-the-loop.
