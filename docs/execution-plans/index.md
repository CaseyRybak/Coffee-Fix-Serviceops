# Execution Plan Index

Work is split into phases. Each phase is a reviewable implementation slice and should be completed before the next phase starts.

## Planning Policy

Before executing any phase, create a detailed implementation plan for that specific phase. The detailed plan should define files, tests, commands, verification steps, and subagent review checkpoints. Do this just in time for the next phase instead of fully detailing all future phases upfront.

## Active Phase

- Phase 20: `phases/20-owner-dashboard-and-sla-foundation.md`.

The active phase points to the next phase ready for implementation planning or execution. `phases/` contains all phase slice maps, not only active work.

Post-Phase-16 roadmap context is preserved in `roadmap-after-phase-16.md`. Use it to reconstruct the reasoning behind Phases 18-24 before creating any detailed implementation plan.

## Detailed Plans

Detailed implementation plans are created just in time in `detailed/`.

Current detailed plan: none. Create a Phase 20 detailed implementation plan before changing SLA/dashboard code.

Create later detailed implementation plans just in time before each future phase. Do not pre-write detailed plans for Phases 18-24 until their turn starts and the current code has been re-read.

Completed detailed plans: `detailed/00-repository-harness-implementation.md`, `detailed/01-foundation-runtime-implementation.md`, `detailed/02-service-request-intake-implementation.md`, `detailed/03-client-status-and-notifications-implementation.md`, `detailed/03a-postgres-persistence-implementation.md`, `detailed/04-dispatcher-mvp-implementation.md`, `detailed/05-staff-access-and-roles-implementation.md`, `detailed/06-knowledge-base-rag-implementation.md`, `detailed/07-ai-agent-workflows-implementation.md`, `detailed/08-technician-and-inventory-implementation.md`, `detailed/09-staff-admin-and-user-management-implementation.md`, `detailed/10-deployment-and-operations-implementation.md`, `detailed/11-production-launch-readiness-implementation.md`, `detailed/12-notification-automation-implementation.md`, `detailed/13-live-ai-provider-and-knowledge-base-content-implementation.md`, `detailed/14-operational-hardening-implementation.md`, `detailed/15-scheduling-depth-implementation.md`, `detailed/16-inventory-reservations-implementation.md`, `detailed/17-public-demo-and-launch-closure-implementation.md`, `detailed/18-portfolio-packaging-and-demo-mode-implementation.md`, `detailed/19-frontend-workspace-decomposition-implementation.md`.

## Phase Sequence

1. `phases/00-repository-harness.md`: repository harness, docs, maps, and review loop.
2. `phases/01-foundation-runtime.md`: backend, frontend, database, Docker Compose, and healthchecks.
3. `phases/02-service-request-intake.md`: request intake API and public form integration.
4. `phases/03-client-status-and-notifications.md`: status page, status timeline, Telegram opt-in.
5. `phases/04-dispatcher-mvp.md`: dispatcher request list, request card, assignment, clarification.
6. `phases/05-staff-access-and-roles.md`: staff login, roles, protected internal workspace and API access.
7. `phases/06-knowledge-base-rag.md`: RAG documents, chunks, embeddings, retrieval with sources.
8. `phases/07-ai-agent-workflows.md`: intake, diagnostic, parts, dispatcher, and reply workflows.
9. `phases/08-technician-and-inventory.md`: technician mobile flow and basic parts tracking.
10. `phases/09-staff-admin-and-user-management.md`: persisted staff accounts, admin workspace, role assignment, and account lifecycle.
11. `phases/10-deployment-and-operations.md`: Dokploy deployment, backups, observability, n8n flows.
12. `phases/11-production-launch-readiness.md`: first-admin bootstrap, real-environment smoke checks, launch checklist, and go/no-go evidence.
13. `phases/12-notification-automation.md`: backend-to-n8n webhook emission, delivery-result persistence, and staff delivery visibility.
14. `phases/13-live-ai-provider-and-knowledge-base-content.md`: live AI and embedding providers, production KB content, and RAG evaluation.
15. `phases/14-operational-hardening.md`: production observability, audit expansion, backup dry-runs, and incident procedures.
16. `phases/15-scheduling-depth.md`: appointment windows, rescheduling, technician availability, and schedule views.
17. `phases/16-inventory-reservations.md`: part reservations, stock movement history, compatibility hints, and low-stock visibility.
18. `phases/17-public-demo-and-launch-closure.md`: domain/HTTPS demo access, port posture, and production smoke evidence.
19. `phases/17a-demo-performance-and-hero-image-optimization.md`: first-load public demo hero/static asset optimization before screenshots and portfolio packaging.
20. `phases/18-portfolio-packaging-and-demo-mode.md`: portfolio README, screenshots, demo scenarios, and safe demo data.
21. `phases/19-frontend-workspace-decomposition.md`: frontend module split before new dashboard, procurement, and assistant screens.
22. `phases/20-owner-dashboard-and-sla-foundation.md`: owner dashboard metrics, SLA deadlines, overdue state, and daily report data.
23. `phases/21-operational-n8n-automation.md`: SLA reminders, red alerts, owner daily reports, and low-stock alerts.
24. `phases/22-procurement-lite.md`: suppliers, purchase requests, approval states, low-stock drafts, and receiving stock movements.
25. `phases/23-technician-profiles-and-recommendation.md`: technician profiles, skills, regions, workload, and explainable recommendations.
26. `phases/24-ai-assistant-with-tools.md`: bounded staff AI assistant with safe tool use and human confirmation.

## Review

Each phase ends with the review protocol in `docs/review/subagent-review-protocol.md`.
