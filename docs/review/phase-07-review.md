# Phase 07 Review

## Slice

Phase 07 implemented AI-assisted dispatcher workflows from `docs/execution-plans/phases/07-ai-agent-workflows.md` using the detailed plan in `docs/execution-plans/detailed/07-ai-agent-workflows-implementation.md`.

## Implemented

- Added an `ai_agents` backend module for prompt input assembly, deterministic suggestion generation, sqlite/PostgreSQL suggestion persistence, dispatcher use cases, and protected dispatcher routes.
- Added PostgreSQL migration `0003_ai_suggestions.sql` for durable AI suggestion lifecycle state.
- Added dispatcher AI endpoints to generate, list, accept diagnostic-question suggestions, and ignore suggestions.
- Extended dispatcher request detail with internal AI suggestions while keeping public status snapshots free of AI data.
- Added a React dispatcher AI suggestion panel with source chips, status labels, generate, accept-question, and ignore actions.
- Added runtime settings for AI suggestion storage/provider behavior.
- Updated domain and harness docs for the AI suggestion boundary.

## Boundary Decisions

- AI suggestions are internal staff review artifacts, not automatic operational decisions.
- Accepting a diagnostic-question suggestion creates a normal dispatcher clarification question through the service-request lifecycle.
- Likely cause, parts, and customer reply suggestions remain drafts for manual staff use.
- Parts suggestions do not check stock, reserve parts, or mutate inventory records.
- The provider is deterministic for local development and tests; live provider integration is deferred.

## Review Notes

Follow-up consistency review on 2026-06-07 found one repository-wiring issue:

- When `create_app()` received an injected service-request repository but not injected knowledge-base or AI repositories, dispatcher detail could mix an in-memory service request with default local AI suggestion storage. This could expose stale local suggestions in tests or development scenarios with matching request numbers.

Resolution:

- `create_app()` now keeps partially injected app instances in one test scope by using in-memory knowledge-base and AI repositories for missing sibling stores.
- `apps/api/tests/test_dispatcher_requests.py` now has a regression test proving injected service-request storage does not read default AI suggestion storage.
- AI suggestion generation now applies `SERVICEOPS_AI_SUGGESTION_LIMIT`; `apps/api/tests/test_ai_agent_suggestions.py` covers the configured limit.

Formal independent subagent review has not been run in this session because the available subagent tool requires an explicit user request for delegation.

## Verification

Final verification commands are recorded after the full Phase 07 check run:

- `python3 tools/repo-checks/check_docs.py`: passed.
- `cd apps/api && uv run --extra dev pytest`: 45 passed.
- `cd apps/worker && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`: 4 passed.
- `cd apps/telegram-bot && uv run --extra dev pytest`: 2 passed.
- `npm run web:test`: 20 passed.
- `npm run web:lint`: passed.
- `npm run web:build`: passed.
- `docker compose config`: passed.

## Recommendation

Phase 07 is functionally ready for Phase 08 planning after the repository-wiring fix and fresh verification. The only remaining process gap is the formal independent subagent review gate.
