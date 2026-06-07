# Phase 07 AI Agent Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add bounded AI-assisted dispatcher workflows that create suggestions and drafts without making customer-visible or operational decisions automatically.

**Architecture:** Add an `ai_agents` API module that owns suggestion models, prompt input assembly, deterministic provider ports, persistence, and dispatcher-facing use cases. Store AI suggestions separately from service-request status, clarification questions, assignments, internal notes, and public status data. Extend the dispatcher API and React workspace so staff can generate, view, accept clarification-question suggestions, or ignore suggestions while keeping RAG context and provider calls testable without live LLM access.

**Tech Stack:** Python, FastAPI, Pydantic, sqlite3, psycopg, PostgreSQL migration SQL, pytest/httpx, React, Vite, TypeScript, node:test.

---

## Scope Decisions

- Phase 07 does not let AI change request status, assign technicians, reserve parts, send messages, or publish customer-visible content automatically.
- AI output is stored as suggestions with lifecycle state: `pending`, `accepted`, or `ignored`.
- The only Phase 07 accept action converts a diagnostic-question suggestion into an existing dispatcher clarification question through the service-request use case.
- Customer reply drafts remain drafts visible to dispatchers. Sending replies through Telegram, SMS, email, or n8n remains deferred.
- Parts suggestions are a stub connected to inventory concepts through structured part names, reasons, and compatibility notes. Stock counts, reservations, and parts catalog persistence remain Phase 08.
- Provider calls are isolated behind an `AiSuggestionProvider` protocol. Tests use deterministic suggestions assembled from service request detail and optional RAG chunks.
- RAG context comes from Phase 06 retrieval results and must be included as source metadata on diagnostic and likely-cause suggestions when available.

## File Responsibility Map

- Create: `apps/api/src/serviceops_api/ai_agents/__init__.py` for package exports.
- Create: `apps/api/src/serviceops_api/ai_agents/models.py` for suggestion kinds, statuses, prompt inputs, suggestion DTOs, and action responses.
- Create: `apps/api/src/serviceops_api/ai_agents/prompting.py` for prompt input assembly from dispatcher request snapshots and RAG chunks.
- Create: `apps/api/src/serviceops_api/ai_agents/providers.py` for `AiSuggestionProvider` and `DeterministicAiSuggestionProvider`.
- Create: `apps/api/src/serviceops_api/ai_agents/repository.py` for sqlite and PostgreSQL AI suggestion repositories.
- Create: `apps/api/src/serviceops_api/ai_agents/use_cases.py` for generate/list/accept/ignore application services.
- Create: `apps/api/src/serviceops_api/ai_agents/api.py` for dispatcher AI suggestion routes.
- Create: `apps/api/src/serviceops_api/migrations/0003_ai_suggestions.sql` for PostgreSQL AI suggestion tables and indexes.
- Modify: `apps/api/src/serviceops_api/config.py` to add local AI provider settings.
- Modify: `apps/api/src/serviceops_api/main.py` to wire repository, provider, knowledge retrieval, service-request repository, and dispatcher AI routes.
- Modify: `apps/api/src/serviceops_api/service_requests/models.py` to add `ai_suggestions` to `DispatcherRequestDetail`.
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py` to keep AI suggestions out of public status and expose dispatcher detail extension data.
- Modify: `apps/api/src/serviceops_api/service_requests/use_cases.py` only if the dispatcher detail composition needs an explicit AI suggestion port.
- Modify: `apps/api/src/serviceops_api/service_requests/api.py` to include AI suggestion routes under dispatcher protection or mount a sibling protected dispatcher router.
- Create: `apps/api/tests/test_ai_agent_prompting.py` for prompt input assembly and RAG source handling.
- Create: `apps/api/tests/test_ai_agent_suggestions.py` for generation, persistence, accept, ignore, and public/private separation.
- Modify: `apps/api/tests/test_dispatcher_requests.py` to assert dispatcher detail can include suggestions while public status does not.
- Modify: `apps/api/tests/test_repository_selection.py` to cover AI suggestion repository selection.
- Modify: `apps/web/src/App.tsx` to add dispatcher AI suggestion types, API helpers, suggestion panel, generate action, accept question action, and ignore action.
- Modify: `apps/web/src/App.test.tsx` to cover dispatcher suggestion rendering and action helper contracts.
- Modify: `apps/web/src/styles.css` to style AI suggestion panels inside the existing dispatcher workspace.
- Modify: `.env.example` and `docker-compose.yml` to document local deterministic AI provider settings.
- Modify: `domains/ai-agents/domain.md`, `domains/service-requests/domain.md`, `domains/knowledge-base/domain.md`, and `domains/inventory/domain.md` to record Phase 07 boundaries.
- Modify: `docs/harness/repository-map.md` and `tools/repo-checks/check_docs.py` after implementation artifacts exist.
- Modify: `project_notes.md` and `docs/execution-plans/index.md` after implementation to mark Phase 08 active.
- Create: `docs/review/phase-07-review.md` after verification and review.

## Task 1: AI Suggestion Models And Prompt Assembly

**Files:**
- Create: `apps/api/src/serviceops_api/ai_agents/__init__.py`
- Create: `apps/api/src/serviceops_api/ai_agents/models.py`
- Create: `apps/api/src/serviceops_api/ai_agents/prompting.py`
- Create: `apps/api/tests/test_ai_agent_prompting.py`

- [x] **Step 1: Write failing prompt assembly tests**

Create `apps/api/tests/test_ai_agent_prompting.py` with tests that build a dispatcher request snapshot and RAG chunks:

```python
def test_prompt_input_uses_service_request_and_rag_sources() -> None:
    from serviceops_api.ai_agents.prompting import build_prompt_input

    prompt = build_prompt_input(
        request={
            "request_number": "CFX-20260607-000001",
            "status": "new",
            "problem": "E61 group overheats after descaling",
            "urgency": "today",
            "customer": {"client_type": "coffee_shop"},
            "machine": {"brand": "Rocket", "model": "Appartamento", "location_type": "coffee_shop"},
            "timeline": [{"title": "Заявка создана", "description": "Получено обращение", "actor": "system"}],
            "clarification": None,
            "assignment": {"technician_name": None, "technician_phone": None, "technician_region": None, "visit_window": None},
            "internal_notes": [],
        },
        rag_results=[
            {
                "document_id": 1,
                "document_title": "E61 overheating repair guide",
                "source_uri": "seed://repair/e61-overheating",
                "chunk_id": 5,
                "chunk_index": 0,
                "start_char": 0,
                "end_char": 120,
                "content": "Check thermosiphon scale and boiler pressure.",
                "score": 0.82,
            }
        ],
    )

    assert prompt.request_number == "CFX-20260607-000001"
    assert "E61 group overheats" in prompt.problem_summary
    assert prompt.machine_label == "Rocket Appartamento"
    assert prompt.rag_sources[0].source_uri == "seed://repair/e61-overheating"
```

Run: `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_prompting.py -q`

Expected: fails because `serviceops_api.ai_agents` does not exist.

- [x] **Step 2: Add AI models**

In `models.py`, define:
- `AiSuggestionKind = Literal["intake_classification", "diagnostic_question", "likely_cause", "parts", "customer_reply"]`
- `AiSuggestionStatus = Literal["pending", "accepted", "ignored"]`
- `AiRagSource`
- `AiPromptInput`
- `AiSuggestionCreate`
- `AiSuggestion`
- `GenerateAiSuggestionsPayload`
- `AiSuggestionListResponse`
- `AiSuggestionActionResponse`

Use field validation to trim required strings, cap suggestion content at 2000 characters, rationale at 1000 characters, and confidence between 0 and 1.

- [x] **Step 3: Implement prompt input assembly**

In `prompting.py`, implement `build_prompt_input(request: dict[str, object], rag_results: list[dict[str, object]]) -> AiPromptInput`.

The function must:
- include request number, status, urgency, customer client type, machine label, location type, problem summary, latest timeline title, clarification state, assignment state, and internal-note count;
- convert RAG results into `AiRagSource` entries with source metadata;
- avoid exposing customer phone or Telegram in prompt input.

- [x] **Step 4: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_prompting.py -q`

Expected: passes.

## Task 2: Deterministic Suggestion Provider

**Files:**
- Create: `apps/api/src/serviceops_api/ai_agents/providers.py`
- Modify: `apps/api/tests/test_ai_agent_prompting.py`

- [x] **Step 1: Add failing provider tests**

Extend `test_ai_agent_prompting.py` with:

```python
def test_deterministic_provider_returns_bounded_human_review_suggestions() -> None:
    from serviceops_api.ai_agents.providers import DeterministicAiSuggestionProvider
    from serviceops_api.ai_agents.prompting import build_prompt_input

    prompt = build_prompt_input(
        request={
            "request_number": "CFX-20260607-000001",
            "status": "new",
            "problem": "E61 group overheats and pressure rises",
            "urgency": "today",
            "customer": {"client_type": "coffee_shop"},
            "machine": {"brand": "Rocket", "model": "Appartamento", "location_type": "coffee_shop"},
            "timeline": [],
            "clarification": None,
            "assignment": {"technician_name": None, "technician_phone": None, "technician_region": None, "visit_window": None},
            "internal_notes": [],
        },
        rag_results=[],
    )

    suggestions = DeterministicAiSuggestionProvider().suggest(prompt)

    assert {suggestion.kind for suggestion in suggestions} == {
        "intake_classification",
        "diagnostic_question",
        "likely_cause",
        "parts",
        "customer_reply",
    }
    assert all("диспетчер" in suggestion.rationale.lower() for suggestion in suggestions)
```

Run: `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_prompting.py -q`

Expected: fails because the provider does not exist.

- [x] **Step 2: Implement provider protocol**

In `providers.py`, add:
- `AiSuggestionProvider` protocol with `suggest(prompt: AiPromptInput) -> list[AiSuggestionCreate]`;
- `DeterministicAiSuggestionProvider`.

The deterministic provider must return exactly five suggestions:
- intake classification based on urgency, client type, and machine label;
- one diagnostic question suitable for conversion into a clarification;
- likely cause using RAG source text when present;
- parts suggestion stub with part names and `inventory_slice_pending` note;
- customer reply draft that is friendly but not sent.

- [x] **Step 3: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_prompting.py -q`

Expected: passes.

## Task 3: AI Suggestion Persistence

**Files:**
- Create: `apps/api/src/serviceops_api/ai_agents/repository.py`
- Create: `apps/api/src/serviceops_api/migrations/0003_ai_suggestions.sql`
- Modify: `apps/api/tests/test_repository_selection.py`
- Create: `apps/api/tests/test_ai_agent_suggestions.py`

- [x] **Step 1: Write failing persistence tests**

Create `apps/api/tests/test_ai_agent_suggestions.py` with sqlite repository tests:
- saving suggestions for request `CFX-20260607-000001` returns ids;
- listing suggestions returns pending suggestions newest-first;
- accepting one suggestion marks only that suggestion accepted;
- ignoring one suggestion marks only that suggestion ignored.

Run: `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_suggestions.py -q`

Expected: fails because the repository does not exist.

- [x] **Step 2: Add PostgreSQL migration**

Create `0003_ai_suggestions.sql` with:
- `ai_suggestions` table: id, request_number, kind, title, content, rationale, confidence, source_chunks JSONB, status, created_at, acted_at;
- indexes on request_number, status, kind, and created_at.

Do not add foreign keys to service requests by request number in this slice; request-number uniqueness exists in service request storage, but tests need isolated AI suggestion repositories.

- [x] **Step 3: Implement sqlite repository**

In `repository.py`, implement:
- `AiSuggestionStore` protocol;
- `SqliteAiSuggestionRepository`;
- methods `save_suggestions(request_number, suggestions)`, `list_suggestions(request_number)`, `mark_accepted(suggestion_id)`, `mark_ignored(suggestion_id)`, and `get_suggestion(suggestion_id)`.

Store `source_chunks` as JSON text in sqlite.

- [x] **Step 4: Implement PostgreSQL repository and factory**

Implement `PostgresAiSuggestionRepository` with psycopg and idempotent migrations `0001`, `0002`, and `0003`.

Add `create_ai_suggestion_repository(settings, initialize=True)` with the same URL selection behavior as existing repositories.

- [x] **Step 5: Add repository selection tests**

Extend `apps/api/tests/test_repository_selection.py` to assert:
- PostgreSQL URL creates `PostgresAiSuggestionRepository`;
- sqlite memory URL creates `SqliteAiSuggestionRepository`;
- unsupported URL raises `ValueError` with `Unsupported SERVICEOPS_DATABASE_URL`.

- [x] **Step 6: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_suggestions.py tests/test_repository_selection.py -q`

Expected: passes.

## Task 4: Dispatcher AI Use Cases And API

**Files:**
- Create: `apps/api/src/serviceops_api/ai_agents/use_cases.py`
- Create: `apps/api/src/serviceops_api/ai_agents/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/src/serviceops_api/service_requests/api.py` if routing is mounted inside the existing dispatcher router.
- Modify: `apps/api/tests/test_ai_agent_suggestions.py`

- [x] **Step 1: Add failing API lifecycle tests**

Extend `test_ai_agent_suggestions.py` with ASGI tests that:
- login as dispatcher through `/staff/login`;
- create a service request through public intake;
- ingest the E61 seed document;
- call `POST /dispatcher/service-requests/{request_number}/ai-suggestions/generate`;
- call `GET /dispatcher/service-requests/{request_number}/ai-suggestions`;
- call `POST /dispatcher/service-requests/{request_number}/ai-suggestions/{suggestion_id}/accept-clarification`;
- assert the accepted diagnostic question appears as the public clarification question;
- call `POST /dispatcher/service-requests/{request_number}/ai-suggestions/{suggestion_id}/ignore` for another suggestion.

Run: `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_suggestions.py -q`

Expected: route-not-found failures.

- [x] **Step 2: Implement use cases**

In `use_cases.py`, add:
- `GenerateAiSuggestions`;
- `ListAiSuggestions`;
- `AcceptAiClarificationSuggestion`;
- `IgnoreAiSuggestion`.

`GenerateAiSuggestions` must load dispatcher request detail, retrieve up to three RAG chunks using the problem and machine label, assemble prompt input, call provider, save suggestions, and return the saved list.

`AcceptAiClarificationSuggestion` must verify suggestion kind is `diagnostic_question`, call `service_request_repository.ask_clarification(request_number, suggestion.content)`, then mark the suggestion accepted.

- [x] **Step 3: Implement protected dispatcher routes**

Create routes:
- `POST /dispatcher/service-requests/{request_number}/ai-suggestions/generate`
- `GET /dispatcher/service-requests/{request_number}/ai-suggestions`
- `POST /dispatcher/service-requests/{request_number}/ai-suggestions/{suggestion_id}/accept-clarification`
- `POST /dispatcher/service-requests/{request_number}/ai-suggestions/{suggestion_id}/ignore`

Mount them with the same dispatcher staff dependency as existing dispatcher routes.

- [x] **Step 4: Wire `main.py`**

Instantiate the AI suggestion repository, deterministic provider, and use cases. Reuse the existing service-request repository and knowledge-base repository so tests can inject in-memory stores.

- [x] **Step 5: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_ai_agent_suggestions.py tests/test_dispatcher_requests.py tests/test_service_request_status.py -q`

Expected: passes.

## Task 5: Dispatcher Detail Suggestion Surface Contract

**Files:**
- Modify: `apps/api/src/serviceops_api/service_requests/models.py`
- Modify: `apps/api/src/serviceops_api/service_requests/repository.py`
- Modify: `apps/api/tests/test_dispatcher_requests.py`
- Modify: `apps/api/tests/test_service_request_status.py`

- [x] **Step 1: Add failing dispatcher/public separation tests**

Extend dispatcher API tests to assert:
- `GET /dispatcher/service-requests/{request_number}` includes `ai_suggestions`;
- public `GET /service-requests/{request_number}/status` and `/status/{public_token}` do not include `ai_suggestions`, source chunks, prompt input, or provider metadata.

Run: `cd apps/api && uv run --extra dev pytest tests/test_dispatcher_requests.py tests/test_service_request_status.py -q`

Expected: dispatcher detail model lacks `ai_suggestions`.

- [x] **Step 2: Add AI suggestion DTOs to dispatcher detail**

Add `DispatcherAiSuggestion` to `service_requests/models.py` or import the API-safe AI suggestion model from `ai_agents.models` if that does not create a dependency cycle.

Add `ai_suggestions: list[DispatcherAiSuggestion]` to `DispatcherRequestDetail`.

- [x] **Step 3: Extend dispatcher detail repository projection**

Keep the service-request repository free of AI generation logic. It may return `ai_suggestions: []` by default, while `GetDispatcherRequest` or route composition can merge persisted suggestions from `AiSuggestionStore`.

Choose the smaller implementation that keeps public status untouched and avoids making service-request persistence depend on AI generation.

- [x] **Step 4: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_dispatcher_requests.py tests/test_service_request_status.py tests/test_ai_agent_suggestions.py -q`

Expected: passes.

## Task 6: Dispatcher Web Suggestion Panel

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`

- [x] **Step 1: Write failing web tests**

Extend `App.test.tsx` with tests for:
- dispatcher detail renders pending AI suggestions grouped by kind;
- diagnostic question suggestion renders an accept button;
- non-question suggestions render ignore buttons and no accept-to-clarification action;
- API helpers build generate/list/accept/ignore suggestion paths;
- public status page markup does not include AI suggestion text.

Run: `npm run web:test`

Expected: fails because AI suggestion UI helpers and rendering do not exist.

- [x] **Step 2: Add TypeScript contracts and API helpers**

Add:
- `AiSuggestionKind`, `AiSuggestionStatus`, `DispatcherAiSuggestion`;
- `buildDispatcherAiSuggestionsPath(requestNumber)`;
- `buildGenerateAiSuggestionsPath(requestNumber)`;
- `buildAcceptAiClarificationPath(requestNumber, suggestionId)`;
- `buildIgnoreAiSuggestionPath(requestNumber, suggestionId)`.

- [x] **Step 3: Render suggestion panel**

Inside `DispatcherPage`, add an AI suggestions panel in the detail workspace:
- generate suggestions button;
- pending suggestions with kind labels, title, content, rationale, confidence, and source labels;
- accepted and ignored state markers;
- accept clarification action only for `diagnostic_question`;
- ignore action for pending suggestions.

- [x] **Step 4: Wire actions**

Use existing staff auth headers. After generate, accept, or ignore, reload dispatcher detail and suggestion list.

Do not display AI suggestions on public pages or public homepage navigation.

- [x] **Step 5: Style panel**

Add restrained workspace styling for `.ai-suggestions-panel`, `.ai-suggestion-item`, `.ai-suggestion-actions`, `.ai-source-list`, and status badges. Keep cards compact and avoid nested-card styling.

- [x] **Step 6: Verify**

Run:

```bash
npm run web:test
npm run web:lint
npm run web:build
```

Expected: passes.

## Task 7: Runtime Configuration And Documentation

**Files:**
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Modify: `domains/ai-agents/domain.md`
- Modify: `domains/service-requests/domain.md`
- Modify: `domains/knowledge-base/domain.md`
- Modify: `domains/inventory/domain.md`
- Modify: `docs/harness/repository-map.md`
- Modify: `tools/repo-checks/check_docs.py`
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-07-review.md`

- [x] **Step 1: Add runtime settings**

Add env settings:

```env
SERVICEOPS_AI_PROVIDER=deterministic
SERVICEOPS_AI_SUGGESTION_LIMIT=5
```

Expose them to the API service in `docker-compose.yml`.

- [x] **Step 2: Update domain docs**

Document:
- AI suggestions are separate from human-confirmed actions;
- only dispatcher acceptance creates customer-visible clarification questions;
- RAG sources can support diagnostic and likely-cause suggestions;
- parts suggestions are inventory concepts only until Phase 08;
- customer replies are drafts only.

- [x] **Step 3: Update harness**

After implementation artifacts exist, add AI agent files, tests, migration, and review artifact to `tools/repo-checks/check_docs.py`. Update `docs/harness/repository-map.md` with the new module and dispatcher AI suggestion surface.

- [x] **Step 4: Update phase status**

Update `project_notes.md` to mark Phase 07 complete and Phase 08 active. Update `docs/execution-plans/index.md` so active phase is `phases/08-technician-and-inventory.md` and the detailed Phase 07 plan is listed as completed.

- [x] **Step 5: Create review artifact**

After implementation and verification, create `docs/review/phase-07-review.md` with:
- files reviewed;
- verification commands and outcomes;
- human-in-the-loop behavior review;
- prompt context clarity review;
- testability without live providers;
- separation from domain decisions;
- final recommendation.

- [x] **Step 6: Verify docs**

Run: `python3 tools/repo-checks/check_docs.py`

Expected: prints `documentation harness check passed`.

## Task 8: Final Verification

- [x] Run `cd apps/api && uv run --extra dev pytest`.
- [x] Run `cd apps/worker && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`.
- [x] Run `cd apps/telegram-bot && uv run --extra dev pytest`.
- [x] Run `npm run web:test`.
- [x] Run `npm run web:lint`.
- [x] Run `npm run web:build`.
- [x] Run `docker compose config`.
- [x] Run `python3 tools/repo-checks/check_docs.py`.
- [ ] Request subagent review using `docs/review/subagent-review-protocol.md`.
- [x] Report exact command outcomes and changed files. Do not commit or push unless the user explicitly asks in the current turn.
