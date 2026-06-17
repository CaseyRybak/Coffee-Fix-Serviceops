# Public Demo Launch Evidence: 2026-06-17

This record is sanitized. Do not include passwords, bearer tokens, Telegram bot tokens, webhook secrets, API keys, raw provider payloads, customer phone numbers, Telegram chat ids, or real staff personal data.

## Scope

- Environment: Aeza VPS test production environment.
- Repository branch: `main`.
- Revision: `81af2ae`.
- Web hostname: `coffeefix-demo.online`.
- API hostname: `api.coffeefix-demo.online`.
- n8n UI hostname, if exposed: not configured yet.
- Operator: repository operator.
- Final decision: Go for current pet-project public demo posture.

## Baseline Access

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Web HTTPS | `curl -I https://coffeefix-demo.online/` | Passed | Returned HTTP 200 through Dokploy/Traefik HTTPS route. |
| API health HTTPS | `curl -i https://api.coffeefix-demo.online/health` | Passed | Returned HTTP 200 healthy JSON through Dokploy/Traefik HTTPS route. |
| Direct web test port | TCP connect to `138.124.91.212:3001` | Closed externally | Docker still has a container port binding, but external access is blocked by `DOCKER-USER` port guard rules. |
| Direct API test port | TCP connect to `138.124.91.212:8000` | Closed externally | Docker still has a container port binding, but external access is blocked by `DOCKER-USER` port guard rules. |
| Dokploy admin | Browser from `80.91.223.6`; `curl -I http://138.124.91.212:3000/` from `80.91.223.6` | Restricted | Allowed only from `80.91.223.6`; browser access from that IP confirmed. |
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
- Removed the global UFW allow rule for `3000/tcp`; added UFW input and forwarded allow rules for `80.91.223.6` only.
- Added IPv4 `DOCKER-USER` rules for Dokploy `3000`: accept traffic from `80.91.223.6` to destination port `3000`, then drop other traffic to destination port `3000`. Added IPv6 drop for destination port `3000`.
- Added and enabled `serviceops-docker-port-guard.service` so the Docker port guard rules are re-applied after server reboot.
- External checks after the guard: `3000` returns HTTP 200 from allowed IP `80.91.223.6`; `3001` and `8000` time out from the same IP; HTTPS web and API routes still return HTTP 200.

## Smoke Checks

- API health: Passed from workstation against `https://api.coffeefix-demo.online/health`.
- Web root: Passed from workstation against `https://coffeefix-demo.online/`.
- Public intake: Passed through the browser for `CFX-20260617-000011`; passed through HTTPS API smoke for `CFX-20260617-000013`.
- Public status by request number: Passed from VPS smoke script for `CFX-20260617-000009`.
- Public status by token: Passed from VPS smoke script.
- Staff login: Passed manually from allowed operator IP. A new staff user was created and successfully logged in; no credential values are recorded in this evidence file.
- Staff workspaces: Passed manually. The new staff user could open the role-appropriate internal cabinets after the domain, HTTPS, CORS, and firewall changes.
- n8n request-created delivery: Passed for `CFX-20260617-000009`; API logs recorded `notification.event_queued` and `notification.delivery_recorded` with provider `n8n`.
- Telegram opt-in ownership: Passed manually. Production Telegram bot is polling on the VPS; local Docker is stopped, so no local `telegram-bot` container is competing for the shared bot token.
- Backup command readiness: Passed. Production PostgreSQL backup created `/var/backups/serviceops/serviceops-20260617-161005.dump` with matching `.sha256`; checksum verification returned `OK`.
- Restore dry-run readiness: Passed by non-destructive readiness audit. `docs/operations/backup-restore.md` defines abort conditions, checksum verification, disposable restore target `serviceops_restore_drill`, migration check, smoke check, and evidence fields; no restore command was executed against production.

## Phase 17a Hero Asset Optimization

- Original hero PNG fallback: `hero-coffee-service-wide.png`, `1514x941`, `1,865,388` bytes.
- Desktop WebP: `hero-coffee-service-wide-desktop.webp`, `1514x941`, `118,892` bytes.
- Mobile WebP: `hero-coffee-service-wide-mobile.webp`, `800x497`, `45,770` bytes.
- Browser selection verified locally with Playwright: desktop viewport selected the desktop WebP, mobile viewport selected the mobile WebP.
- Visual check: desktop and mobile screenshots confirmed the same hero composition without cropping.
- Preload decision: do not add an explicit hero preload in this slice. The `picture` element is in the first viewport, uses small responsive WebP assets, and avoids forcing the desktop asset onto mobile; revisit preload only if deployed browser evidence still shows a visible hero delay.
- Production check on 2026-06-17: `https://coffeefix-demo.online/` returned HTTP 200, desktop WebP returned HTTP 200 with `content-type: image/webp` and `content-length: 118892`, mobile WebP returned HTTP 200 with `content-type: image/webp` and `content-length: 45770`.

## Go/No-Go

- Decision: Go for current pet-project public demo posture.
- Remaining blockers: None for Phase 17 pet-project demo posture. Phase 17a local optimization and live-domain asset availability are verified; repeat browser selection checks after the next web redeploy if hero assets change again.
- Follow-up owner: Pending.
