# Live AI Provider And Knowledge Base Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make AI suggestions and RAG retrieval production-configurable by adding OpenAI-compatible provider adapters, curated repair knowledge content, and evaluation fixtures while keeping local/test runs deterministic and human-in-the-loop.

**Architecture:** Keep the existing provider-port shape: `ai_agents` owns suggestion generation and `knowledge_base` owns embedding/retrieval. Add live OpenAI-compatible adapters behind those ports, provider factories in application wiring, and deterministic fallbacks for local/tests. Knowledge content remains source-backed repair data, and AI output remains staff-reviewed suggestions that never mutate lifecycle state without a human action.

**Tech Stack:** FastAPI, Pydantic settings, stdlib `urllib.request` or existing dependency-light HTTP adapters, sqlite/PostgreSQL repositories, pgvector, pytest/httpx, Docker Compose env config, curated Markdown/text fixtures.

---

## File Structure

- Modify `apps/api/src/serviceops_api/config.py`: add live AI and embedding provider settings, model names, API base URL, API key, timeout, retry count, and production validation helpers.
- Modify `apps/api/src/serviceops_api/main.py`: select deterministic or live providers through factories instead of hard-coding deterministic providers.
- Modify `apps/api/src/serviceops_api/ai_agents/providers.py`: keep deterministic provider and add an OpenAI-compatible chat suggestion provider plus a provider factory.
- Modify `apps/api/src/serviceops_api/ai_agents/prompting.py`: add a provider-facing prompt payload builder that excludes phone, Telegram handles, secrets, internal staff-only data, and raw provider errors.
- Modify `apps/api/src/serviceops_api/knowledge_base/embeddings.py`: add an OpenAI-compatible embedding provider plus a provider factory.
- Modify `apps/worker/src/serviceops_worker/knowledge_base_tasks.py`: share the same embedding provider selection rules for background embedding jobs.
- Modify `apps/api/src/serviceops_api/knowledge_base/seed_documents.py`: replace the single seed with a curated multi-document repair knowledge set.
- Create `apps/api/src/serviceops_api/knowledge_base/evaluation.py`: deterministic RAG evaluation cases and evaluation runner.
- Create `apps/api/tests/test_live_ai_provider.py`: tests for provider selection, chat payload assembly, response parsing, retry/error handling, and secret-safe failures.
- Create `apps/api/tests/test_live_embedding_provider.py`: tests for embedding provider selection, payload parsing, dimension checks, retry/error handling, and deterministic test isolation.
- Modify `apps/api/tests/test_ai_agent_prompting.py`, `apps/api/tests/test_ai_agent_suggestions.py`, `apps/api/tests/test_knowledge_base_seed.py`, and `apps/worker/tests/test_knowledge_base_tasks.py`: extend existing tests around privacy, source metadata, curated content, and worker provider selection.
- Create or modify `docs/operations/ai-providers.md`: production configuration, provider contracts, secret handling, local deterministic mode, and troubleshooting.
- Modify `.env.example`, `docker-compose.yml`, `docker-compose.production.yml`, `docs/operations/deployment-runbook.md`, `docs/operations/smoke-tests.md`, `tools/repo-checks/check_docs.py`, `docs/execution-plans/index.md`, and `project_notes.md`.
- Create `docs/review/phase-13-review.md` after implementation verification and independent review.

## Provider Configuration Contract

Use deterministic providers by default:

- `SERVICEOPS_AI_PROVIDER=deterministic`
- `SERVICEOPS_EMBEDDING_PROVIDER=deterministic`

Add live provider settings:

- `SERVICEOPS_AI_PROVIDER=openai-compatible`
- `SERVICEOPS_AI_MODEL=gpt-4.1-mini`
- `SERVICEOPS_AI_API_BASE_URL=https://api.openai.com/v1`
- `SERVICEOPS_AI_API_KEY=<secret>`
- `SERVICEOPS_AI_TIMEOUT_SECONDS=20`
- `SERVICEOPS_AI_MAX_RETRIES=2`
- `SERVICEOPS_EMBEDDING_PROVIDER=openai-compatible`
- `SERVICEOPS_EMBEDDING_MODEL=text-embedding-3-small`
- `SERVICEOPS_EMBEDDING_API_BASE_URL=https://api.openai.com/v1`
- `SERVICEOPS_EMBEDDING_API_KEY=<secret>`
- `SERVICEOPS_EMBEDDING_TIMEOUT_SECONDS=20`
- `SERVICEOPS_EMBEDDING_MAX_RETRIES=2`

Production-like environments must fail clearly when a live provider is selected without the required API key or model. Local/test mode must not require live secrets and must not make external network calls unless explicitly configured.

## Task 1: Settings And Provider Selection

- [ ] Write failing tests in `apps/api/tests/test_live_ai_provider.py` proving `create_ai_suggestion_provider(settings)` returns deterministic provider for `SERVICEOPS_AI_PROVIDER=deterministic`, OpenAI-compatible provider for `openai-compatible`, and raises `ValueError("SERVICEOPS_AI_API_KEY is required when SERVICEOPS_AI_PROVIDER=openai-compatible")` when the key is missing.
- [ ] Write failing tests in `apps/api/tests/test_live_embedding_provider.py` proving `create_embedding_provider(settings)` follows the same deterministic/live/missing-secret behavior for embedding settings.
- [ ] Add the settings fields listed in "Provider Configuration Contract" to `apps/api/src/serviceops_api/config.py`.
- [ ] Add `create_ai_suggestion_provider(settings)` in `ai_agents/providers.py`.
- [ ] Add `create_embedding_provider(settings)` in `knowledge_base/embeddings.py`.
- [ ] Replace hard-coded providers in `apps/api/src/serviceops_api/main.py` with the factories.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_live_ai_provider.py tests/test_live_embedding_provider.py -v`
  - Expected: provider-selection tests pass without network access.

## Task 2: OpenAI-Compatible Chat Suggestion Adapter

- [ ] Write failing tests in `apps/api/tests/test_live_ai_provider.py` for the chat request body. The test fake transport must assert:
  - URL is `{base_url}/chat/completions`.
  - `Authorization: Bearer <key>` is sent.
  - `model` equals configured `SERVICEOPS_AI_MODEL`.
  - prompt text includes request number, status, urgency, machine label, problem summary, and RAG source snippets.
  - prompt text does not include phone numbers, Telegram handles, API keys, callback secrets, notification secrets, or raw internal note content.
- [ ] Add `OpenAiCompatibleAiSuggestionProvider` in `apps/api/src/serviceops_api/ai_agents/providers.py`.
- [ ] Make the adapter request strict JSON output shaped as:
  - `suggestions[].kind`
  - `suggestions[].title`
  - `suggestions[].content`
  - `suggestions[].rationale`
  - `suggestions[].confidence`
  - `suggestions[].source_chunk_indexes`
- [ ] Parse the provider response into `AiSuggestionCreate` values and attach `source_chunks` only by index from `prompt.rag_sources`; ignore out-of-range indexes.
- [ ] Clamp or reject invalid confidence values through the existing Pydantic model instead of silently storing impossible values.
- [ ] On malformed JSON, HTTP 429/5xx exhaustion, timeout exhaustion, or missing `choices[0].message.content`, raise `RuntimeError("AI provider request failed")` without logging secrets or raw prompt content.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_live_ai_provider.py -v`
  - Expected: chat payload, parsing, retry, and failure tests pass.

## Task 3: Prompt Privacy And Human-In-The-Loop Boundaries

- [ ] Extend `apps/api/tests/test_ai_agent_prompting.py` with a request snapshot containing customer phone, Telegram handle, technician phone, internal notes, AI suggestion history, and notification delivery details.
- [ ] Assert serialized provider prompt input does not contain:
  - phone numbers
  - Telegram handles
  - technician phone
  - internal note body
  - notification delivery errors
  - shared secrets
- [ ] Add a test that generated suggestions remain `pending` and do not change service-request status, assignment, inventory, notifications, or public status snapshots.
- [ ] If current `build_prompt_input()` includes unsafe fields in future snapshots, filter at prompt assembly time rather than inside the provider adapter.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_prompting.py tests/test_ai_agent_suggestions.py -v`
  - Expected: human-in-the-loop and prompt privacy tests pass.

## Task 4: OpenAI-Compatible Embedding Adapter

- [ ] Write failing tests in `apps/api/tests/test_live_embedding_provider.py` for embedding request body. The fake transport must assert:
  - URL is `{base_url}/embeddings`.
  - `Authorization: Bearer <key>` is sent.
  - `model` equals configured `SERVICEOPS_EMBEDDING_MODEL`.
  - `input` preserves input order.
- [ ] Add `OpenAiCompatibleEmbeddingProvider` in `apps/api/src/serviceops_api/knowledge_base/embeddings.py`.
- [ ] Parse response `data[].embedding` ordered by `index`; return one vector per input text.
- [ ] Raise `RuntimeError("Embedding provider request failed")` on timeout exhaustion, HTTP 429/5xx exhaustion, malformed response, missing vectors, or mismatched vector count.
- [ ] Keep deterministic embeddings unchanged for local/test retrieval.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_live_embedding_provider.py tests/test_knowledge_base_chunking.py -v`
  - Expected: embedding adapter and existing deterministic chunk/retrieval tests pass.

## Task 5: Worker Embedding Provider Parity

- [ ] Extend `apps/worker/tests/test_knowledge_base_tasks.py` so `_default_embedding_provider()` returns deterministic provider by default and a live-compatible provider when `SERVICEOPS_EMBEDDING_PROVIDER=openai-compatible` plus required env vars are set.
- [ ] Avoid duplicating adapter logic in the worker. Prefer importing the API embedding provider factory if packaging boundaries allow it; otherwise mirror the minimal settings parser and adapter with matching tests.
- [ ] Ensure worker missing-secret failures use the same message as API configuration.
- [ ] Run:
  - `cd apps/worker && uv run --extra dev pytest`
  - Expected: worker embedding task tests pass without network access.

## Task 6: Curated Knowledge Base Content

- [ ] Replace the single seed in `apps/api/src/serviceops_api/knowledge_base/seed_documents.py` with at least eight source-backed documents covering:
  - E61 overheating and thermosiphon restrictions.
  - DeLonghi/Saeco/Jura no-coffee-flow diagnostics.
  - Grinder not grinding or weak coffee extraction.
  - Milk frothing and cappuccinatore cleaning.
  - Water leak triage: tank, drip tray, brew unit, hydraulic circuit.
  - Descaling, water hardness, and maintenance intervals.
  - Display/error-code intake checklist.
  - Professional machine pressure/steam symptom triage.
- [ ] Each document must have:
  - stable `source_uri` using `seed://repair/<slug>`
  - descriptive `title`
  - body with diagnostic procedure, checks, and escalation criteria
  - metadata keys such as `topic`, `symptom`, `machine_family`, `brand`, or `maintenance`
- [ ] Extend `apps/api/tests/test_knowledge_base_seed.py` to assert all seed documents have unique `source_uri`, useful metadata, non-empty bodies, and no phone numbers, customer data, staff names, or secrets.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_seed.py -v`
  - Expected: curated seed content tests pass.

## Task 7: RAG Evaluation Fixture

- [ ] Create `apps/api/src/serviceops_api/knowledge_base/evaluation.py` with:
  - `RagEvaluationCase(query: str, expected_source_uri: str, expected_terms: list[str])`
  - `RAG_EVALUATION_CASES`
  - `run_rag_evaluation(retrieve: RetrieveKnowledge) -> list[dict[str, object]]`
- [ ] Add evaluation cases for at least six representative queries:
  - "E61 overheats after descaling"
  - "Jura no coffee flow"
  - "milk foam weak"
  - "coffee machine leaking water"
  - "grinder spins but no beans ground"
  - "how often descale hard water"
- [ ] Write tests that ingest all seed documents with deterministic embeddings and assert each query returns the expected source URI in the top three results and at least one expected term in retrieved content.
- [ ] If deterministic embedding quality is too weak for a case, improve seed document wording and expected terms before changing retrieval behavior.
- [ ] Run:
  - `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_seed.py -v`
  - Expected: RAG evaluation cases pass deterministically.

## Task 8: Operations Documentation And Env Wiring

- [ ] Add AI/embedding env vars to `.env.example`, `docker-compose.yml`, and `docker-compose.production.yml` without real secrets.
- [ ] Create `docs/operations/ai-providers.md` documenting:
  - deterministic local/test mode
  - OpenAI-compatible live mode
  - required env vars
  - timeout/retry behavior
  - safe logging rules
  - how to run seed ingestion and RAG evaluation
- [ ] Update `docs/operations/deployment-runbook.md` to include live provider setup and go/no-go check before enabling AI suggestions in production.
- [ ] Update `docs/operations/smoke-tests.md` with deterministic RAG evaluation and optional live provider smoke instructions.
- [ ] Update `tools/repo-checks/check_docs.py` so Phase 13 docs and evaluation artifacts are required.
- [ ] Run:
  - `python3 tools/repo-checks/check_docs.py`
  - `docker compose -f docker-compose.yml config`
  - `docker compose -f docker-compose.production.yml --env-file .env.example config`
  - Expected: docs and compose config checks pass without secrets.

## Task 9: Phase Handoff And Review Artifact

- [ ] Update `project_notes.md` current status to include completed Phase 13 provider adapters, curated KB content, and RAG evaluation fixtures.
- [ ] Update `project_notes.md` active focus to Phase 14: Operational Hardening.
- [ ] Update `docs/execution-plans/index.md` active phase to `phases/14-operational-hardening.md`.
- [ ] Create `docs/review/phase-13-review.md` with reviewer role, files reviewed, verification commands, findings sections, and final recommendation placeholder only after implementation verification and independent review are actually available.
- [ ] Do not mark Phase 13 complete until subagent or independent human review has checked provider security, secret handling, deterministic test isolation, prompt privacy, KB source quality, and human-in-the-loop behavior.

## Verification

- [ ] `python3 tools/repo-checks/check_docs.py`
- [ ] `cd apps/api && uv run --extra dev pytest tests/test_live_ai_provider.py tests/test_live_embedding_provider.py tests/test_ai_agent_prompting.py tests/test_ai_agent_suggestions.py tests/test_knowledge_base_seed.py -v`
- [ ] `cd apps/api && uv run --extra dev pytest`
- [ ] `cd apps/worker && uv run --extra dev pytest`
- [ ] `cd apps/telegram-bot && uv run --extra dev pytest`
- [ ] `npm run web:test`
- [ ] `npm run web:lint`
- [ ] `npm run web:build`
- [ ] `docker compose -f docker-compose.yml config`
- [ ] `docker compose -f docker-compose.production.yml --env-file .env.example config`
- [ ] `bash -n tools/operations/smoke_test.sh`
- [ ] `python3 tools/operations/test_smoke_script_contract.py`
- [ ] Secret scan before commit:
  - `rg -n "sk-|SERVICEOPS_AI_API_KEY=.*[A-Za-z0-9_-]{20,}|SERVICEOPS_EMBEDDING_API_KEY=.*[A-Za-z0-9_-]{20,}" . --glob '!apps/**/.venv/**' --glob '!node_modules/**'`
  - Expected: no real API keys or provider secrets in tracked files.

## Subagent Review Gate

Ask the reviewer to inspect:

- Live provider adapters do not log API keys, raw prompts, customer contacts, Telegram handles, internal notes, or provider response bodies containing sensitive data.
- Missing live-provider secrets fail clearly only when live providers are selected.
- Deterministic providers remain the default for local/test mode and automated tests.
- AI suggestions remain staff-reviewed artifacts and do not mutate request lifecycle, assignment, notifications, or inventory automatically.
- RAG source metadata is preserved in dispatcher-visible suggestions.
- Curated KB content is repair-focused, source-traceable, and free of customer/staff secrets.
- Evaluation fixtures are meaningful enough to catch broken retrieval, not just superficial document existence.

## Self-Review

- Phase 13 deliverables are covered by Tasks 1-9.
- Provider settings, adapters, worker parity, KB content, evaluation, docs, and phase handoff each have explicit tests or checks.
- The plan avoids introducing LangGraph, SQLAlchemy, Alembic, or external orchestration because the phase can be completed through existing ports.
- The plan keeps live provider calls isolated behind ports and keeps local/test runs network-free.
- No production secret values are required or stored in the repository.
