# Phase 13 Review: Live AI Provider And Knowledge Base Content

## Reviewer Role

Independent Codex consistency review requested after Phase 13 implementation. Scope focused on plan compliance, provider security, prompt privacy, deterministic test isolation, knowledge-base source quality, RAG evaluation usefulness, and human-in-the-loop behavior.

## Files Reviewed

- `apps/api/src/serviceops_api/config.py`
- `apps/api/src/serviceops_api/main.py`
- `apps/api/src/serviceops_api/ai_agents/providers.py`
- `apps/api/src/serviceops_api/ai_agents/prompting.py`
- `apps/api/src/serviceops_api/knowledge_base/embeddings.py`
- `apps/api/src/serviceops_api/knowledge_base/evaluation.py`
- `apps/api/src/serviceops_api/knowledge_base/seed_documents.py`
- `apps/worker/src/serviceops_worker/knowledge_base_tasks.py`
- `apps/api/tests/test_live_ai_provider.py`
- `apps/api/tests/test_live_embedding_provider.py`
- `apps/api/tests/test_ai_agent_prompting.py`
- `apps/api/tests/test_ai_agent_suggestions.py`
- `apps/api/tests/test_knowledge_base_seed.py`
- `apps/worker/tests/test_knowledge_base_tasks.py`
- `docs/operations/ai-providers.md`
- `.env.example`
- `docker-compose.yml`
- `docker-compose.production.yml`
- `domains/ai-agents/domain.md`
- `domains/knowledge-base/domain.md`

## Verification Commands

- `cd apps/api && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest tests/test_live_ai_provider.py tests/test_live_embedding_provider.py tests/test_ai_agent_prompting.py tests/test_ai_agent_suggestions.py tests/test_knowledge_base_seed.py -v`: passed, 23 tests after review fixes.
- `cd apps/api && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest`: passed.
- `cd apps/worker && UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest -v`: passed after review fixes.
- `python3 tools/repo-checks/check_docs.py`: passed.
- `docker compose -f docker-compose.yml config`: passed.
- `docker compose -f docker-compose.production.yml --env-file .env.example config`: passed.
- `bash -n tools/operations/smoke_test.sh`: passed.
- `python3 tools/operations/test_smoke_script_contract.py`: passed.
- `rg -n "sk-|SERVICEOPS_AI_API_KEY=.*[A-Za-z0-9_-]{20,}|SERVICEOPS_EMBEDDING_API_KEY=.*[A-Za-z0-9_-]{20,}" . --glob '!apps/**/.venv/**' --glob '!node_modules/**' --glob '!apps/web/node_modules/**'`: returned only false positives in `SUB-SKILL` text, the documented scan command, and a test assertion; no real provider API keys found.

## Blocking Issues

- None after review fixes.

## Non-Blocking Issues

- Live provider smoke against a real provider key remains an operations task and must not be run with secrets committed to the repository.
- The worker still mirrors the embedding adapter instead of importing the API implementation because the worker package does not currently depend on `serviceops_api`. Keep future changes synchronized or create a shared provider package in a later hardening/refactor slice.

## Review Fixes Applied

- Added regression tests proving malformed provider JSON from the chat and embedding transports is masked as generic provider failure.
- Fixed the API OpenAI-compatible AI suggestion provider to wrap malformed transport JSON in `RuntimeError("AI provider request failed")`.
- Fixed the API OpenAI-compatible embedding provider and worker embedding provider to wrap malformed transport JSON in `RuntimeError("Embedding provider request failed")`.

## Suggested Follow-Up Slice

- Phase 14 should expand production observability around AI/embedding provider latency, error rates, retry exhaustion, and operator runbooks without logging raw prompts or provider response bodies.
- Consider extracting the OpenAI-compatible embedding adapter to shared code once worker/API packaging boundaries are formalized.

## Documentation Updates Needed

- None identified in self-check beyond the Phase 13 documentation updates already included.

## Final Recommendation

Phase 13 is locally verified and ready to proceed to Phase 14 planning. Public/live AI enablement should still wait for production secret configuration, repair-content ingestion in the target environment, a non-sensitive live provider smoke, and launch evidence outside repository secrets.
