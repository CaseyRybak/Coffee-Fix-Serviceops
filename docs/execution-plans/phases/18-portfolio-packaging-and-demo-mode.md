# Phase 18: Portfolio Packaging And Demo Mode

> For implementation workers: create a detailed implementation plan before changing code or docs, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Turn the implemented ServiceOps system into a clear portfolio case that can be understood and tried by an external reviewer.

## Why This Phase Exists

The current documentation is excellent for contributors, but the public README is too terse for recruiters, employers, or clients. The project needs a visible demo story, screenshots, demo credentials, demo scenarios, and safe demo data so the work can be evaluated quickly.

## Context To Read

- `docs/execution-plans/roadmap-after-phase-16.md`
- `README.md`
- `docs/product/vision.md`
- `docs/product/mvp-scope.md`
- `docs/harness/repository-map.md`
- `docs/operations/deployment-runbook.md`
- `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`
- `docs/operations/n8n-workflows.md`
- `domains/service-requests/domain.md`
- `domains/ai-agents/domain.md`
- `domains/inventory/domain.md`
- `domains/scheduling/domain.md`
- `domains/technicians/domain.md`

## Deliverables

- Portfolio-oriented `README.md` with demo URL, demo credentials guidance, business problem, solution overview, key workflows, architecture, AI/RAG layer, Telegram/n8n automation, inventory/scheduling, tech stack, local setup, production deployment, and skills demonstrated.
- Demo scenarios for public request intake, public status, dispatcher triage, AI suggestions, technician workflow, inventory reservation, n8n notification, and Telegram opt-in.
- Sanitized screenshots or screenshot-capture guidance for landing, request success, status page, dispatcher card, AI suggestions, technician workspace, inventory reservations, n8n workflow, Telegram notification, and operations evidence.
- Demo-mode policy that uses fake customer data, fake phone numbers, deterministic AI defaults unless live smoke is intentionally run, and no reusable admin credentials.
- Seed or reset guidance for demo data if implementation is needed; otherwise a documented manual demo-data procedure.
- README links to the current roadmap, architecture, and operations evidence without overwhelming the first-read experience.

## Scope Boundaries

- This phase packages existing capabilities; it should not build the owner dashboard, SLA workflows, procurement, or AI assistant.
- Demo credentials must not include production admin power unless there is a deliberate, documented reason and the deployment is disposable.
- Demo data must not use real customer phone numbers, Telegram chat ids, staff personal data, provider payloads, or secrets.
- If live AI provider evidence is added, it must follow `docs/operations/ai-providers.md` and stay sanitized.

## Acceptance Criteria

- An external reviewer can understand what the project does in under one minute from the README.
- The README contains a concise demo path and links to deeper docs for architecture and operations.
- Demo scenarios can be followed without prior chat context.
- Screenshots or screenshot instructions cover the main workflow surfaces.
- Demo data and credentials are safe to expose for portfolio review.
- Local setup and production demo sections do not contradict current operations docs.

## Subagent Review Gate

Review external clarity, demo safety, secret redaction, screenshot relevance, and whether the README accurately represents implemented capabilities without overstating future roadmap items.
