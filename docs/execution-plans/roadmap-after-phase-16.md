# Roadmap After Phase 16

This roadmap preserves the post-Phase-16 planning context so future contributors can reconstruct detailed implementation plans without relying on chat history.

## Sources

- Original product direction: AI ServiceOps platform for coffee machine repair operations with customers, assets, work orders, technicians, inventory, procurement, SLA, reporting, Telegram, n8n, RAG, and AI assistance.
- Current repository status after Phase 16, post-phase hardening, and self-hosted n8n handoff.
- Independent external inspection that reviewed repository docs and attempted to open the live VPS demo.
- Internal gap analysis comparing the original platform plan against the implemented phases.

## Current Baseline

The project is already more than a public intake MVP. Implemented capabilities include:

- Public repair intake, request numbers, public status snapshots, clarification answers, and Telegram opt-in link contracts.
- Dispatcher workspace, staff login/RBAC, persisted staff administration, technician workflow, scheduling, and inventory reservations.
- Knowledge-base RAG with source metadata, relevance filtering, seed repair content, deterministic local providers, and OpenAI-compatible live adapters.
- Human-reviewed AI suggestions for dispatcher workflows.
- Backend-to-n8n notification webhooks, delivery-result persistence, self-hosted n8n workflow exports, and staff-visible notification delivery state.
- Production-oriented Docker Compose, Dokploy/VPS evidence, migrations, backup/restore scripts, smoke tests, structured logs, operational diagnostics, and incident response docs.

The main gap is not the core MVP. The main gap is public demonstration readiness and the remaining ServiceOps depth that would make the project read as a complete AI automation case.

## Confirmed Gaps

- Public demo is not ready enough to rely on. Direct IP/port access is temporary, domains/HTTPS are not complete, and direct test ports still need closure or replacement by proper routing.
- README and portfolio packaging are internal-developer oriented, not recruiter/employer oriented.
- Frontend is concentrated in very large `App.tsx` and `styles.css` files, which raises change risk before adding dashboard, reports, procurement, and assistant surfaces.
- n8n currently automates notification delivery, but not broader operational automation such as SLA reminders, owner reports, low-stock alerts, or purchase approvals.
- SLA, overdue tracking, owner dashboard, daily reports, and owner-facing operational metrics are missing.
- Procurement and suppliers remain deferred even though inventory reservations are implemented.
- Technician profiles and recommendation logic are still shallow; scheduling currently identifies technicians by staff username rather than a richer technician domain profile.
- AI is currently a suggestion engine, not a tool-using assistant. This is a good safety baseline, but it does not yet satisfy the original "AI dispatcher agent with tools" ambition.
- Full customer accounts, full asset history, billing, payments, telephony, route optimization, GPS, multi-tenant SaaS, and complex calendar integrations remain intentionally out of scope for the next roadmap.

## Ordering Rationale

The next work should happen in this order:

1. Make the project safely demonstrable before adding more product surface.
2. Package the project as a portfolio case while the current functionality is still fresh and strong.
3. Decompose the frontend before adding several large staff-facing screens.
4. Add SLA and owner metrics before automating SLA notifications.
5. Add procurement before building assistant tools that create purchase drafts.
6. Add technician profiles and explainable recommendations before AI recommends technicians.
7. Add tool-using AI last, after the underlying tools have meaningful domain APIs to call.

This avoids building AI or automation around incomplete domain models and avoids growing an already large frontend file into a harder-to-maintain bottleneck.

## Phase Sequence

### Phase 17: Public Demo And Launch Closure

Close the public demonstration and launch-readiness gaps: domains, HTTPS, routing, direct port closure, Dokploy restriction, secret rotation, live smoke evidence, and Telegram polling ownership.

### Phase 18: Portfolio Packaging And Demo Mode

Turn the repository from an internal engineering record into a portfolio-ready case: README, screenshots, demo data, demo credentials, demo scenarios, and repeatable demo reset guidance.

### Phase 19: Frontend Workspace Decomposition

Split the large frontend surface into domain workspaces and shared utilities before dashboard, reports, procurement, and assistant screens are added.

### Phase 20: Owner Dashboard And SLA Foundation

Add the first owner-facing operational dashboard and SLA/overdue data model so the business can see workload, risk, waiting-parts, low-stock, and daily performance.

### Phase 21: Operational n8n Automation

Extend n8n beyond notification delivery into SLA reminders, red alerts, owner daily reports, and low-stock automation, using backend APIs as the source of truth.

### Phase 22: Procurement Lite

Add supplier and purchase-request workflows that connect low stock and reservations to a simple approval and receiving process.

### Phase 23: Technician Profiles And Recommendation

Add richer technician profiles and explainable recommendation logic based on skills, regions, active workload, appointment availability, and part readiness.

### Phase 24: AI Assistant With Tools

Add a bounded staff-facing AI assistant that can call read-only tools directly and mutating tools only through explicit human confirmation.

## Guardrails

- Do not create detailed implementation plans for all future phases at once. Detailed plans should be created just in time after reading the current code.
- Do not introduce autonomous AI decisions. Human confirmation remains required for assignment, customer-visible messages, status changes, reservations, and purchase creation.
- Do not expose internal AI, staff, audit, notification, scheduling capacity, or inventory details in public status snapshots.
- Do not expand into billing, payments, telephony, GPS, route optimization, multi-tenant SaaS, or complex calendar integrations before this roadmap is complete.
- Keep self-hosted n8n as the default production automation posture unless a later architecture decision deliberately changes it.
- Keep production secret and log redaction rules intact for every new workflow.

## How To Reconstruct Detailed Plans Later

For any future phase, read in this order:

1. `AGENTS.md`
2. `project_notes.md`
3. `ARCHITECTURE.md`
4. `docs/execution-plans/index.md`
5. This roadmap
6. The target phase file in `docs/execution-plans/phases/`
7. Relevant `domains/<domain>/AGENTS.md` and `domains/<domain>/domain.md`
8. Current implementation files and tests
9. Current operations docs when the phase touches deployment, n8n, Telegram, AI providers, logging, smoke tests, or secrets

Then create a detailed implementation plan in `docs/execution-plans/detailed/` for only that phase.
