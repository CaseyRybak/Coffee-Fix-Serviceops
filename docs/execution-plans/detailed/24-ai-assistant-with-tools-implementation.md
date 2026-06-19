# Phase 24 AI Assistant With Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded staff-facing AI assistant that can use safe ServiceOps tools while requiring explicit staff confirmation before any operational mutation.

**Architecture:** Extend the existing `ai_agents` bounded context with assistant-specific models, repository, use cases, and API routes. The assistant remains an orchestrator over existing service-request, knowledge-base, inventory, owner-dashboard, and technician recommendation use cases; it does not bypass repositories, authorization, notification rules, public DTOs, or domain state machines.

**Tech Stack:** FastAPI, Pydantic, sqlite/PostgreSQL repository pattern, existing deterministic/OpenAI-compatible AI provider settings, React/Vite staff workspace, node:test SSR tests, pytest API tests.

**Completion Note:** Implemented in the Phase 24 working branch. Checklist boxes below are preserved as the original execution plan; final verification and independent review evidence is recorded in `docs/review/phase-24-review.md`.

---

### Task 1: Backend Assistant Contracts, Policy, And History

**Files:**
- Create: `apps/api/tests/test_ai_assistant_tools.py`
- Modify: `apps/api/src/serviceops_api/ai_agents/models.py`
- Modify: `apps/api/src/serviceops_api/ai_agents/repository.py`
- Add migration: `apps/api/src/serviceops_api/migrations/0015_ai_assistant_runs.sql`
- Modify: `apps/api/src/serviceops_api/operations/migrate.py`

- [ ] Write failing tests for assistant run persistence, safe history shape, and migration wiring.
- [ ] Add assistant request/response, tool call, confirmation, and history models.
- [ ] Add sqlite and PostgreSQL assistant history repositories that store only safe prompt/result summaries.
- [ ] Add migration `0015_ai_assistant_runs.sql` for assistant runs and tool calls.
- [ ] Wire migration runner contract tests.

### Task 2: Backend Tool Registry And Confirmation Boundary

**Files:**
- Modify: `apps/api/tests/test_ai_assistant_tools.py`
- Create: `apps/api/src/serviceops_api/ai_agents/assistant_tools.py`
- Modify: `apps/api/src/serviceops_api/ai_agents/use_cases.py`
- Modify: `apps/api/src/serviceops_api/ai_agents/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`

- [ ] Write failing API tests for authorized staff, forbidden unauthorized users, read-only tool execution, confirmation-required mutation, provider failure fallback, and public-data isolation.
- [ ] Implement a deterministic intent-to-tool planner for the MVP assistant so local/tests avoid network calls.
- [ ] Add read-only tools: `find_request`, `list_overdue_requests`, `search_knowledge_base`, `check_part_stock`, `recommend_technician`, `generate_daily_report`.
- [ ] Add mutating confirmed tool: `create_purchase_request_draft`, limited to draft creation through existing procurement use cases.
- [ ] Add `POST /assistant/runs`, `GET /assistant/runs`, and `POST /assistant/runs/{run_id}/confirm` staff-protected routes.
- [ ] Log only safe operational fields: actor, action, tool names, run id, outcome, and safe reason.

### Task 3: Staff Assistant Frontend

**Files:**
- Modify: `apps/web/src/shared/api.ts`
- Modify: `apps/web/src/shared/types.ts`
- Create: `apps/web/src/features/assistant/AssistantPage.tsx`
- Modify: `apps/web/src/features/staff-auth/StaffWorkspacePage.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] Write failing frontend tests for route helpers, workspace card, protected route rendering, and confirmation UI copy.
- [ ] Add shared assistant DTOs and path builders.
- [ ] Add protected `/assistant` staff page with prompt form, tool result display, confirmation button for pending mutation, and safe history list.
- [ ] Add workspace card for dispatcher/admin/inventory users.
- [ ] Style the page consistently with existing operational workspaces using compact, scan-friendly controls.

### Task 4: Documentation, Verification, And Review

**Files:**
- Modify: `domains/ai-agents/domain.md`
- Modify: `domains/service-requests/domain.md`
- Modify: `domains/inventory/domain.md`
- Modify: `docs/operations/ai-providers.md`
- Modify: `docs/operations/operational-diagnostics.md`
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-24-review.md`

- [ ] Document assistant tool boundaries, confirmation policy, privacy rules, and public isolation.
- [ ] Run backend, frontend, docs, operations, compose, worker, and bot verification commands from `project_notes.md`.
- [ ] Run independent subagent review for backend/API safety, frontend/RBAC, and product/docs/phase compliance.
- [ ] Fix blocking review findings.
- [ ] Record final review evidence in `docs/review/phase-24-review.md`.
