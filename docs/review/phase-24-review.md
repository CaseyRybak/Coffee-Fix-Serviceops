# Phase 24 Review: AI Assistant With Tools

## Reviewer Roles

Independent subagent review after implementation and verification:

- Backend/API safety reviewer: tool policy, authorization, privacy, persistence, migration, confirmation behavior.
- Frontend/RBAC/UI reviewer: protected route flow, assistant workspace, confirmation UI, safe link rendering, public isolation.
- Product/docs reviewer: phase acceptance criteria, roadmap boundaries, documentation consistency, review artifact requirements.
- Targeted re-reviewers: backend privacy/confirmation/finalization/stock-boundary fixes, frontend route/link/RBAC fixes, and product/docs verification evidence.

## Files Reviewed

- `docs/execution-plans/phases/24-ai-assistant-with-tools.md`
- `docs/execution-plans/detailed/24-ai-assistant-with-tools-implementation.md`
- `apps/api/src/serviceops_api/ai_agents/`
- `apps/api/src/serviceops_api/migrations/0015_ai_assistant_runs.sql`
- `apps/api/src/serviceops_api/main.py`
- `apps/api/src/serviceops_api/operations/migrate.py`
- `apps/api/tests/test_ai_assistant_tools.py`
- `apps/api/tests/test_operations_migrate.py`
- `apps/web/src/features/assistant/AssistantPage.tsx`
- `apps/web/src/features/staff-auth/StaffWorkspacePage.tsx`
- `apps/web/src/App.tsx`
- `apps/web/src/App.test.tsx`
- `apps/web/src/shared/api.ts`
- `apps/web/src/shared/staffAuth.ts`
- `apps/web/src/shared/types.ts`
- `apps/web/src/styles.css`
- `domains/ai-agents/domain.md`
- `domains/inventory/domain.md`
- `domains/service-requests/domain.md`
- `docs/operations/ai-providers.md`
- `docs/operations/operational-diagnostics.md`
- `docs/execution-plans/index.md`
- `docs/harness/repository-map.md`
- `project_notes.md`

## Verification Commands

- `python3 tools/repo-checks/check_docs.py` - passed.
- `cd apps/api && uv run --extra dev pytest` - passed: 200 tests, 1 existing FastAPI deprecation warning.
- `cd apps/api && uv run --extra dev pytest tests/test_ai_assistant_tools.py -q` - passed after targeted re-review fixes: 14 tests.
- `cd apps/worker && uv run --extra dev pytest` - passed: 15 tests. Initial sandbox run could not write `~/.cache/uv`; rerun with approved escalation passed.
- `cd apps/telegram-bot && uv run --extra dev pytest` - passed: 15 tests. Initial sandbox run could not write `~/.cache/uv`; rerun with approved escalation passed.
- `npm run web:test` - passed after targeted re-review fixes.
- `npm run web:lint` - passed.
- `npm run web:build` - passed.
- `docker compose up -d --build` - passed; local API, web, worker, Telegram bot, Postgres, Redis, and n8n containers started.
- `docker compose exec -T api python -m serviceops_api.operations.migrate` - passed; database status `ok`.
- Headless Playwright assistant smoke - passed: 15/15 real `/assistant` questions produced relevant answers with the asked question as the card title and `assistant_self_check` recorded.
- `docker compose -f docker-compose.production.yml --env-file .env.example config --quiet` - passed.
- `bash -n tools/operations/postgres_backup.sh` - passed.
- `bash -n tools/operations/postgres_restore.sh` - passed.
- `bash -n tools/operations/smoke_test.sh` - passed.
- `python3 tools/operations/test_smoke_script_contract.py` - passed.
- `python3 tools/operations/test_production_compose_contract.py` - passed.

## Findings And Resolutions

### Blocking Issues

- Assistant history stored unsafe free-form prompt text.
  - Resolution: persisted `safe_message` is now a bounded tool/request/id summary rather than raw staff prompt text.

- Free-text tool arguments for knowledge and stock tools could persist sensitive prompt fragments.
  - Resolution: persisted `search_knowledge_base` and `check_part_stock` arguments now store bounded summaries only. Regression coverage includes bearer-token-like, password, webhook-secret, Telegram-handle, phone, and internal-note text.

- Dispatcher role could bypass existing full-stock inventory read boundaries through the assistant.
  - Resolution: `check_part_stock` is limited to `admin` and `inventory` assistant users. Dispatcher full stock access remains unavailable.

- Mutating assistant confirmation was not claimed atomically before creating a purchase draft.
  - Resolution: assistant confirmation now performs a rowcount-gated `confirmation_required` to `executing` claim before executing the procurement use case, then finalizes to `completed` or `failed`. Replay confirmation is rejected and covered by tests.

- Confirmed purchase-draft creation and assistant-history finalization could leave a run stuck in `executing` if finalization failed after the draft was created.
  - Resolution: confirmation finalization failures now mark the run failed with an operationally safe summary that tells staff to check procurement records before retrying. Failure-injection regression coverage verifies no unhandled 500 and no stuck `executing` history state in that path.

- Direct `/assistant` login flow did not preserve the assistant route after staff login.
  - Resolution: `resolveStaffLandingPath` now preserves `/assistant` for `dispatcher`, `admin`, and `inventory`, and rejects it for `technician`.

- Assistant tool-level `403` responses were treated like expired staff sessions in the web UI.
  - Resolution: assistant fetches now redirect only on `401`; role-denied tool attempts show assistant-page feedback without clearing the valid staff session. Regression coverage verifies `403` remains on `/assistant`.

- Frontend assistant types omitted backend `executing` status.
  - Resolution: web DTO types and assistant run rendering now include `executing`; SSR coverage verifies it renders as an in-progress state rather than completed.

- Assistant tool refs rendered untrusted `href` values directly.
  - Resolution: assistant refs now render links only for safe internal paths or `http(s)` URLs; unsafe schemes render as text. Regression coverage includes a `javascript:` ref.

- Phase 24 review artifact was missing while `project_notes.md` linked it.
  - Resolution: this review artifact records the phase review and verification evidence.

- Phase 24 review evidence omitted the required docs check and the repository map still described Phase 24 as future work.
  - Resolution: `check_docs.py` is recorded in verification evidence and `docs/harness/repository-map.md` now maps the completed Phase 23/24 plans, review artifacts, assistant backend, and assistant web surface.

- Provider-failure coverage was ambiguous because the Phase 24 assistant uses a deterministic intent planner rather than a live provider call path.
  - Resolution: the assistant now can create an OpenAI-compatible planner from the same `SERVICEOPS_AI_PROVIDER` configuration used by dispatcher suggestions. Deterministic domain guardrails remain the first safety layer, and regression coverage exercises planner/provider-like failure fallback: the assistant records a safe failed run without persisting raw bearer-token prompt text.

- Assistant answers were often irrelevant because broad questions fell into the wrong tool or reused generic reports.
  - Resolution: the assistant now has domain answer tools for request metrics, schedule, technicians, stock, knowledge, and recommendations. Daily reports are used only for explicit daily-report requests; card headings use the actual staff question.

- Inventory lookup returned arbitrary stock rows when the requested part did not match.
  - Resolution: stock answers now either return matching parts or explicitly state that no stock match was found. They do not substitute unrelated parts.

- Assistant self-check did not catch wrong-domain answers before returning them.
  - Resolution: each read-only answer records `assistant_self_check`; the check validates expected tool/domain, stock match or explicit not-found, KB sources, schedule/technician routing, and request-number preservation for request lookups/recommendations.

- Operational database questions with required facets could still receive broad or unrelated answers.
  - Resolution: structured `answer_database_query` now handles date-filtered request counts, supplier count/list questions, active reservation aggregates, and technician service-region coverage. Self-check fails if date, supplier, reservation, or region questions do not use the required database-backed query spec.

- Assistant history result summaries could still persist unsafe provider or knowledge content.
  - Resolution: assistant messages and stored tool result summaries/refs are sanitized before persistence, preserving request numbers while redacting bearer/API-key/callback/password tokens, phone-like contact data, standalone Telegram handles, addresses, and private/internal notes.

### Non-Blocking Issues

- Purchase drafts created through confirmed assistant action record the procurement actor as static `assistant`; assistant history preserves the confirming staff user. A future audit-depth slice can pass staff username into procurement actors.
- Assistant UI copy is intentionally role-generic while backend tool permissions are role-specific. API enforcement is correct; a later polish pass can make examples fully role-aware.
- Assistant tool refs allow absolute `http(s)` URLs. This blocks unsafe schemes, but a stricter internal-origin allowlist can be considered later if assistant refs should remain ServiceOps-only.
- Pure-role RBAC is covered by API tests. The Playwright smoke ran through the current local dev account; that account has enough roles in the persisted Docker database to exercise all smoke domains from the UI.

## Suggested Follow-Up Slice

- Assistant RBAC/audit polish: role-aware assistant examples, confirming staff attribution in procurement artifacts, and internal-origin link allowlist.

## Documentation Updates

Updated:

- `project_notes.md`
- `docs/execution-plans/index.md`
- `docs/execution-plans/detailed/24-ai-assistant-with-tools-implementation.md`
- `domains/ai-agents/domain.md`
- `domains/service-requests/domain.md`
- `domains/inventory/domain.md`
- `docs/operations/ai-providers.md`
- `docs/operations/operational-diagnostics.md`
- `docs/harness/repository-map.md`

## Final Recommendation

Approved after fixes. Phase 24 satisfies the bounded assistant goal: staff can use assistant tools through protected APIs and UI, read-only tools respect role boundaries, purchase draft creation requires explicit confirmation, assistant history stores safe summaries, and public status surfaces remain free of assistant prompts, tool calls, provider metadata, and internal reasoning.
