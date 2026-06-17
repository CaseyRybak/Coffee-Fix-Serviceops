# Phase 24: AI Assistant With Tools

> For implementation workers: create a detailed implementation plan before changing code, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Add a bounded staff-facing AI assistant that can use ServiceOps tools while keeping humans in control of operational changes.

## Why This Phase Exists

The project already has safe AI suggestions and source-backed RAG. The original platform direction also called for an AI dispatcher/owner assistant that can find requests, list overdue work, check stock, recommend technicians, draft purchases, and generate reports. This phase should happen after SLA, procurement, and technician recommendations exist so the assistant can call real domain tools.

## Context To Read

- `docs/execution-plans/roadmap-after-phase-16.md`
- `domains/ai-agents/AGENTS.md`
- `domains/ai-agents/domain.md`
- `domains/knowledge-base/domain.md`
- `domains/service-requests/domain.md`
- `domains/inventory/domain.md`
- `domains/scheduling/domain.md`
- `domains/technicians/domain.md`
- `domains/notifications/domain.md`
- `docs/operations/ai-providers.md`
- `docs/operations/operational-diagnostics.md`
- Phase 20, 22, and 23 artifacts when available.
- `apps/api/src/serviceops_api/ai_agents/`

## Deliverables

- Staff-protected assistant API.
- Tool registry with initial tools: `find_request`, `list_overdue_requests`, `search_knowledge_base`, `check_part_stock`, `recommend_technician`, `create_purchase_request_draft`, and `generate_daily_report`.
- Tool execution policy that allows read-only tools immediately and requires explicit staff confirmation for mutating tools.
- Mutating tools limited to safe drafts or normal existing use cases; no direct autonomous assignment, status change, customer notification, stock consumption, or approved purchase creation.
- Assistant conversation or request history that is safe to store and does not retain secrets, raw provider bodies, customer phone numbers, Telegram chat ids, or unrestricted source chunk text.
- Dispatcher or staff UI for assistant prompts, tool results, confirmation prompts, and final responses.
- Tests for tool policy, prompt privacy, provider failure handling, authorization, confirmation behavior, and public data isolation.
- Documentation updates for assistant boundaries and operational troubleshooting.

## Scope Boundaries

- This phase does not implement autonomous agents that mutate production state without confirmation.
- This phase does not require LangGraph unless the detailed plan proves durable state graphs are needed.
- This phase does not expose assistant output publicly.
- This phase does not bypass existing domain use cases, repositories, authorization checks, notification rules, or audit/log redaction.
- This phase does not make billing, payment, telephony, route optimization, or GPS decisions.

## Acceptance Criteria

- Authorized staff can ask the assistant to find requests, list overdue work, search knowledge, check stock, recommend a technician, create a purchase draft with confirmation, and generate a daily report.
- Read-only tools run without confirmation and return safe, bounded data.
- Mutating tools require explicit confirmation and produce normal domain artifacts through existing use cases.
- Assistant logs and stored records exclude secrets and sensitive raw payloads.
- Public status snapshots and public APIs do not expose assistant prompts, tool calls, provider metadata, or internal reasoning.
- Tests cover successful tool use, denied unauthorized access, confirmation-required flows, provider errors, and privacy boundaries.

## Subagent Review Gate

Review tool safety, human-in-the-loop enforcement, prompt/privacy boundaries, domain-use-case reuse, authorization, auditability, and whether assistant claims match actual implemented tools.
