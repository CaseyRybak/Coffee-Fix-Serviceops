# Portfolio Demo Guide

This guide explains how to review Coffee Fix ServiceOps safely as a portfolio project. It is written for external reviewers and operators who need a repeatable demo path without exposing production secrets or real personal data.

## Demo URL

- Public web demo: `https://coffeefix-demo.online`
- Public API health: `https://api.coffeefix-demo.online/health`
- Public status pages are created per request after intake.

Internal staff workspaces are protected. The operator should create disposable staff accounts for a review window and share them out of band only when staff access is required.

## Demo Safety Policy

Use only fake data:

- customer names such as `Demo Customer` or `Coffee Shop Demo`;
- test phone numbers such as `+1 555 0100`;
- fake addresses such as `Demo District, Test Street 10`;
- fake Telegram handles such as `@demo_coffee_customer`;
- generic machine models such as `DeLonghi Magnifica S`, `Gaggia Classic`, or `Saeco Royal`.

Do not put these values in screenshots, evidence, docs, chat, or issues:

- real customer phone numbers;
- real Telegram chat ids;
- Telegram bot tokens;
- staff passwords;
- reusable production admin credentials;
- API keys or provider secrets;
- webhook shared secrets or callback secrets;
- raw AI provider request or response bodies;
- internal note bodies that mention real people or operational details.

Portfolio review should use deterministic AI unless the operator is intentionally running a live-provider smoke test. Live AI evidence must follow `docs/operations/ai-providers.md` and stay sanitized.

## Credential Policy

The repository must not publish production staff credentials. For a review, create disposable accounts through the admin workspace:

- dispatcher role for `/dispatcher`;
- technician role for `/technician`;
- inventory role for `/inventory`;
- admin role only if the reviewer specifically needs to see staff-management behavior.

Preferred account handling:

1. Create review accounts shortly before the review.
2. Use strong temporary passwords stored outside the repository.
3. Share credentials only through the approved private channel.
4. Deactivate the accounts or rotate their passwords after the review.

Do not use the first production admin bootstrap account as a portfolio demo login.

## Recommended Demo Path

### 1. Public Request Intake

Open the public demo and create a repair request with fake data:

- Name: `Demo Customer`
- Phone: `+1 555 0100`
- Telegram handle: `@demo_coffee_customer`
- Client type: office or coffee shop
- Brand: `DeLonghi`
- Model: `Magnifica S`
- Problem: `Water leaks under the machine after heating`
- Address: `Demo District, Test Street 10`
- Urgency: one or two days

Expected result:

- the app returns a request number shaped like `CFX-YYYYMMDD-000001`;
- the success state links to the public status page;
- the API emits a request-created notification event for n8n.

### 2. Public Status Page

Open `/status/<request-number>` or the generated token link.

Expected result:

- customer sees current status, masked phone, problem summary, timeline, appointment if scheduled, clarification if present, and Telegram opt-in action;
- customer does not see internal notes, staff personal data, AI suggestions, provider metadata, notification internals, inventory details, or audit data.

### 3. Telegram Opt-In

From the public status page, request Telegram linking.

Expected result:

- the API returns a bot deep link;
- the Telegram bot consumes `/start <token>`;
- later customer-safe status or clarification messages can be sent to the linked chat.

For local smoke tests, use the protected bot endpoint through the existing smoke script instead of consuming real production `/start` traffic. One Telegram bot token means one active polling process.

### 4. Dispatcher Triage

Log in with a disposable dispatcher account and open `/dispatcher`.

Show:

- request list and filters;
- selected request card with full intake detail;
- status update;
- clarification question;
- internal note;
- technician assignment;
- structured appointment creation or rescheduling;
- low-stock read-only visibility;
- notification delivery state.

Expected result:

- dispatcher actions update the internal request lifecycle and timeline;
- public status remains customer-safe;
- clarification questions become visible to the customer;
- n8n delivery outcomes are visible without exposing provider secrets.

### 5. AI Suggestions

From the dispatcher detail, generate AI suggestions.

Show:

- intake classification;
- diagnostic question;
- likely cause;
- likely parts;
- customer reply draft;
- source references when RAG coverage is relevant;
- knowledge-gap behavior when no relevant source applies.

Expected result:

- suggestions remain pending staff-reviewed artifacts;
- accepting a diagnostic-question suggestion creates a normal dispatcher clarification question;
- AI does not automatically assign technicians, reserve parts, change statuses, or send customer-visible messages.

### 6. Technician Workflow

Log in with a disposable technician account and open `/technician`.

Show:

- assigned visit list;
- schedule-oriented appointment timing;
- request detail;
- diagnosis checklist;
- repair result;
- parts-used form with catalog and stock context.

Expected result:

- technician actions append status events as technician actions;
- parts usage consumes active reservations for the same request and part before unreserved available stock;
- technician access remains read-only for catalog maintenance.

### 7. Inventory Workflow

Log in with a disposable inventory account and open `/inventory`.

Show:

- catalog search and stock summary;
- structured part identity;
- exact-model, series, or generic-group compatibility;
- stock updates;
- request-linked reservation;
- reservation release;
- stock movement history;
- low-stock state.

Expected result:

- available quantity accounts for active reservations;
- on-hand quantity changes only when stock is adjusted or parts are consumed;
- duplicate catalog protection uses factual part keys rather than fuzzy name matching.

### 8. n8n And Operations Evidence

Review these docs instead of exposing the live n8n admin UI by default:

- `docs/operations/n8n-workflows.md`
- `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`
- `docs/operations/public-demo-launch-evidence.md`

Expected result:

- reviewer can see that request-created, status-changed, clarification-requested, and customer-answered events are modeled as n8n workflows;
- evidence stays sanitized;
- n8n is not treated as the source of truth for ServiceOps state.

## Screenshot Checklist

Capture screenshots only with fake data. Redact anything sensitive before sharing outside the private review context.

Recommended screenshots:

1. Landing page first viewport.
2. Public request form with fake values.
3. Request success state with a fake request number.
4. Public status page with masked phone and customer-safe timeline.
5. Dispatcher request card with fake customer data.
6. Dispatcher AI suggestions panel with safe source references.
7. Dispatcher scheduling panel or schedule list.
8. Technician workspace with fake assigned visit.
9. Inventory catalog and reservation panel.
10. Owner dashboard with fake request data, SLA risk metrics, workload, issue groups, and low-stock risk.
11. Sanitized n8n workflow canvas or repository workflow docs.
12. Telegram notification using fake request data and redacted chat identity.
13. Operations evidence page showing HTTPS, port posture, smoke checks, and backup readiness.

Redact:

- phone numbers beyond masked or fake examples;
- Telegram chat ids and bot usernames if they identify a real private setup;
- staff emails when they are not disposable demo accounts;
- n8n credentials, URLs containing secrets, execution payloads, and headers;
- API keys, webhook secrets, callback secrets, and provider payloads;
- internal notes that were not created only for demo.

## Demo Data Reset Guidance

For the current public demo, do not run destructive production database resets. Use this safe reset pattern:

1. Create a fresh fake request for each review.
2. Use a fake customer and fake contact values.
3. Create or rotate disposable staff accounts for the review window.
4. Deactivate or password-rotate disposable staff accounts after the review.
5. Leave historical fake requests in the database unless the operator performs a controlled maintenance cleanup.

A full reset belongs only in a separate disposable environment where the database volume, n8n data volume, and Telegram setup are known to be throwaway. Never run truncate, drop database, or destructive restore commands against the public production-like demo while it may contain valuable evidence or real operational state.

## Local Demo Option

For a fully disposable walkthrough, run the system locally with Docker Compose and local seed behavior. Local staff seed accounts are intentionally blocked outside local/dev/test environments. Keep local Telegram polling stopped while production polling is active if both environments share one bot token.

Useful checks:

```bash
python3 tools/repo-checks/check_docs.py
npm run web:test
npm run web:lint
npm run web:build
bash -n tools/operations/smoke_test.sh
python3 tools/operations/test_smoke_script_contract.py
python3 tools/operations/test_production_compose_contract.py
```

## What Is Internal But Shipped

The owner dashboard and SLA foundation are shipped as an admin-only internal surface at `/owner`. Demo it only with disposable admin credentials and fake operational data. Public reviewers without staff access should use screenshots or a guided private review window rather than public links.

Phase 20 also exposes protected daily-report data for later automation, but Phase 21 owns sending owner reports and alerts through n8n.

Phase 22 procurement is shipped as an internal inventory/admin workflow at `/inventory#procurement`. Demo it only with disposable inventory/admin credentials and fake suppliers, parts, and purchase requests; do not show procurement data in public customer status pages.

Phase 23 Lite technician recommendations are shipped as an internal dispatcher/admin workflow. Demo them only as deterministic, explainable suggestions that can prefill manual assignment fields; do not present them as automatic dispatching, route optimization, ratings, durable availability calendars, part-readiness scoring, or AI-owned assignment.

## What Not To Demo As Shipped

These are roadmap items, not completed capabilities:

- full workforce-management recommendations beyond the Phase 23 Lite deterministic profile, workload, and scheduling-conflict foundation;
- tool-using staff AI assistant;
- billing, payments, telephony, GPS routing, multi-tenant SaaS, or customer accounts.
