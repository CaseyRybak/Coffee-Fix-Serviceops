# Phase 17: Public Demo And Launch Closure

> For implementation workers: create a detailed implementation plan before changing code or production configuration, implement this phase as a bounded slice, then request subagent review using `docs/review/subagent-review-protocol.md`.

## Goal

Make the existing system safe and reliable enough to show as a public demo.

## Why This Phase Exists

The codebase and operations artifacts are strong, but the live demo posture is still temporary. The project needs a real domain/HTTPS route, closed direct test ports, restricted Dokploy access, and fresh smoke evidence before it is used as a portfolio link.

## Context To Read

- `docs/execution-plans/roadmap-after-phase-16.md`
- `docs/operations/deployment-runbook.md`
- `docs/operations/smoke-tests.md`
- `docs/operations/launch-smoke-evidence.md`
- `docs/operations/launch-smoke-evidence-2026-06-15-vps.md`
- `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`
- `docs/operations/operational-diagnostics.md`
- `docs/operations/incident-response.md`
- `docs/operations/ai-providers.md`
- `docker-compose.production.yml`
- `.env.example`

## Deliverables

- Public web route through a domain and HTTPS.
- Public API route through HTTPS, either as a subdomain or a documented reverse-proxy path.
- Direct temporary public test ports `3001` and `8000` closed or replaced by private/internal routing.
- Dokploy access on `3000` restricted to trusted IP/VPN or documented as intentionally unavailable to the public.
- n8n `5678`, PostgreSQL, and Redis verified as not directly published to the public internet.
- Telegram polling ownership clarified for demo/prod: either separate local and production bot tokens or an explicit one-active-polling rule with local simulation guidance.
- Disposable staff-route smoke credentials or equivalent safe demo smoke mechanism.
- Fresh production smoke evidence covering web, API health, public intake/status, staff login/dispatcher route, n8n callback path, Telegram opt-in ownership, backup, and restore-drill readiness.
- Updated operations docs for the final public demo posture.

## Scope Boundaries

- This phase does not add new product features.
- This phase does not build demo data, portfolio README, screenshots, or new UI screens; those belong to Phase 18.
- This phase does not implement SLA, reports, procurement, or AI assistant tools.
- This phase should not expose admin credentials, real customer data, Telegram chat ids, API keys, bot tokens, webhook secrets, or raw provider payloads in evidence.

## Acceptance Criteria

- A public user can open the web demo over HTTPS without using an IP-address port.
- API health and required public API calls work through the documented HTTPS route.
- Temporary direct ports for web/API are no longer required for public demo access.
- n8n, PostgreSQL, Redis, and internal service ports are not directly reachable from the public internet.
- Dokploy is restricted or explicitly documented as non-public.
- Smoke evidence records pass/fail status, timestamps, routes checked, and sanitized notes.
- Public launch evidence changes the posture from test-only/no-go to demo-ready or clearly records the remaining blocker.

## Subagent Review Gate

Review public exposure, HTTPS routing, smoke evidence quality, Telegram polling ownership, and whether the repository can guide a future operator without relying on chat history.
