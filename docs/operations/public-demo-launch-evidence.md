# Public Demo Launch Evidence: 2026-06-17

This record is sanitized. Do not include passwords, bearer tokens, Telegram bot tokens, webhook secrets, API keys, raw provider payloads, customer phone numbers, Telegram chat ids, or real staff personal data.

## Scope

- Environment: Aeza VPS test production environment.
- Repository branch: `main`.
- Revision: `9c65409`.
- Web hostname: `coffeefix-demo.online`.
- API hostname: `api.coffeefix-demo.online`.
- n8n UI hostname, if exposed: not configured yet.
- Operator: repository operator.
- Final decision: Pending.

## Baseline Access

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Web HTTPS | `curl -I https://coffeefix-demo.online/` | Passed | Returned HTTP 200 through Dokploy/Traefik HTTPS route. |
| API health HTTPS | `curl -i https://api.coffeefix-demo.online/health` | Passed | Returned HTTP 200 healthy JSON through Dokploy/Traefik HTTPS route. |
| Direct web test port | TCP connect to `138.124.91.212:3001` | Closed externally | Docker still has a container port binding, but external access is blocked by `DOCKER-USER` port guard rules. |
| Direct API test port | TCP connect to `138.124.91.212:8000` | Closed externally | Docker still has a container port binding, but external access is blocked by `DOCKER-USER` port guard rules. |
| Dokploy admin | `curl -I http://138.124.91.212:3000/` | Blocked from workstation; allowed in UFW | UFW currently allows `3000/tcp` from anywhere. Must be restricted before public demo. |
| n8n direct port | `nc -vz 138.124.91.212 5678` | Closed from workstation; not published by ServiceOps Compose | Docker shows n8n has only container-internal `5678/tcp`. |
| PostgreSQL direct port | `nc -vz 138.124.91.212 5432` | Closed from workstation; not published by ServiceOps Compose | Docker shows ServiceOps PostgreSQL has only container-internal `5432/tcp`. |
| Redis direct port | `nc -vz 138.124.91.212 6379` | Closed from workstation; not published by ServiceOps Compose | Docker shows ServiceOps Redis has only container-internal `6379/tcp`. |

## Deployment Runtime

- Docker/Dokploy app status: ServiceOps Compose app is running from `/etc/dokploy/compose/coffeefixserviceops-coffeefixserviceops-up3whl/code`.
- API service status: Running and healthy; Docker still publishes `0.0.0.0:8000->8000/tcp`, with direct external access blocked by `serviceops-docker-port-guard.service`.
- Web service status: Running; Docker still publishes `0.0.0.0:3001->80/tcp`, with direct external access blocked by `serviceops-docker-port-guard.service`.
- Worker service status: Running; connected to Redis and ready. Celery logs warn that the worker runs as root.
- Telegram bot status: Running and polling production bot `@CoffeeeFix_bot`.
- n8n status: Running; four ServiceOps workflows activated. n8n logs mention editor URL `http://138.124.91.212:5678`, but Docker does not publish `5678` directly.
- PostgreSQL health: ServiceOps PostgreSQL running and healthy; no public port publication.
- Redis health: ServiceOps Redis running and healthy; no public port publication.

## Routing And HTTPS

- DNS records verified: `coffeefix-demo.online` and `api.coffeefix-demo.online` resolve to the VPS public IP through Spaceship DNS.
- HTTPS certificate issuer: Let's Encrypt via Dokploy/Traefik.
- Web route target: `https://coffeefix-demo.online` routes to ServiceOps `web` on container port `80`.
- API route target: `https://api.coffeefix-demo.online` routes to ServiceOps `api` on container port `8000`.
- n8n UI route target: Not publicly routed through Dokploy/Traefik in current ServiceOps Compose posture.
- CORS allowed origins: API container allows `https://coffeefix-demo.online`; OPTIONS preflight for `POST /service-requests` returned `access-control-allow-origin: https://coffeefix-demo.online`.

## Direct Port Guard

- Removed UFW allow rules for `3001/tcp` and `8000/tcp`, including IPv6 entries.
- Added IPv4 and IPv6 `DOCKER-USER` drop rules for original destination ports `3001` and `8000`, because Docker-published ports can remain reachable even after UFW allow rules are removed.
- Added and enabled `serviceops-docker-port-guard.service` so the Docker port guard rules are re-applied after server reboot.
- External TCP check after the guard: `3001 closed`, `8000 closed`, while `80 open` and `443 open`.

## Secret Rotation

Record only secret names and rotation outcome, never secret values.

| Secret | Rotated? | Where configured | Notes |
| --- | --- | --- | --- |
| `SERVICEOPS_STAFF_AUTH_SECRET` | Pending | Dokploy | |
| `SERVICEOPS_N8N_WEBHOOK_SHARED_SECRET` | Pending | Dokploy/n8n | |
| `SERVICEOPS_N8N_CALLBACK_SECRET` | Pending | Dokploy/n8n | |
| `SERVICEOPS_TELEGRAM_BOT_API_SECRET` | Pending | Dokploy/bot | |
| `N8N_ENCRYPTION_KEY` | Pending | Dokploy | Only rotate with an n8n credential migration plan. |
| n8n MCP/API key | Pending | n8n | |

## Smoke Checks

- API health: Passed from workstation against `https://api.coffeefix-demo.online/health`.
- Web root: Passed from workstation against `https://coffeefix-demo.online/`.
- Public intake: Passed through the browser for `CFX-20260617-000011`; passed through HTTPS API smoke for `CFX-20260617-000013`.
- Public status by request number: Passed from VPS smoke script for `CFX-20260617-000009`.
- Public status by token: Passed from VPS smoke script.
- Staff login: Skipped; disposable staff smoke credentials were not configured.
- Dispatcher route: Skipped; disposable staff smoke credentials were not configured.
- n8n request-created delivery: Passed for `CFX-20260617-000009`; API logs recorded `notification.event_queued` and `notification.delivery_recorded` with provider `n8n`.
- Telegram opt-in ownership: Pending. Production Telegram bot is polling; local polling ownership still needs confirmation before public demo.
- Backup command readiness: Pending.
- Restore dry-run readiness: Pending.

## Go/No-Go

- Decision: No-Go for final public demo handoff, but web/API domain routing and direct test-port closure are now passed.
- Remaining blockers: Dokploy `3000` is still allowed by UFW from anywhere; staff-route smoke is missing disposable credentials; Telegram local-vs-production polling ownership still needs confirmation; setup-exposed secrets still need rotation evidence; backup/restore readiness still needs evidence.
- Follow-up owner: Pending.
