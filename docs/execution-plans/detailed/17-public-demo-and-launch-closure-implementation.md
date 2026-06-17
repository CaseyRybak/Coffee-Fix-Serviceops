# Public Demo And Launch Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing ServiceOps deployment safe and reliable enough to use as a public portfolio demo.

**Architecture:** Keep Phase 17 in the operations boundary. The application code should not gain product features in this slice; work is limited to deployment posture, environment/routing documentation, smoke evidence, Telegram polling ownership, and small script/doc updates needed to prove the public demo route. Production state remains owned by the API/PostgreSQL/n8n runtime, while evidence documents record sanitized verification results.

**Tech Stack:** Docker Compose production runtime, Dokploy/reverse proxy routing, bash smoke scripts, curl/OpenSSL/SSH operator checks, PostgreSQL backup/restore scripts, FastAPI health/public routes, React/Vite web build served by nginx, self-hosted n8n, aiogram Telegram bot.

---

## File Structure

- Create `docs/operations/public-demo-launch-evidence.md`: sanitized evidence record for the final demo posture, replacing ad-hoc chat notes with durable go/no-go evidence.
- Modify `docs/operations/deployment-runbook.md`: update the public-demo checklist, domain/HTTPS routing, direct-port closure, Dokploy restriction, and Telegram polling ownership steps.
- Modify `docs/operations/smoke-tests.md`: add public-domain smoke command examples and expected evidence fields.
- Modify `docs/operations/operational-diagnostics.md`: add external access and port-posture checks if missing.
- Modify `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`: add a dated follow-up pointer to the new public demo evidence record, without rewriting historical evidence.
- Modify `.env.example`: add or clarify public demo environment variable comments only if the current template is missing required Phase 17 variables.
- Modify `tools/operations/smoke_test.sh`: only if needed to support HTTPS domain smoke without leaking credentials or hardcoding hostnames.
- Modify `tools/operations/test_smoke_script_contract.py`: only if `smoke_test.sh` changes.
- Modify `tools/operations/test_production_compose_contract.py`: only if Phase 17 discovers a production Compose contract drift.
- Modify `tools/repo-checks/check_docs.py`: require the Phase 17 detailed plan and new evidence document once they exist.
- Modify `docs/execution-plans/index.md`: record this detailed plan as the current detailed implementation plan while Phase 17 is active.
- Modify `project_notes.md`: point next steps to this detailed plan and the Phase 17 evidence record.
- Modify `docs/harness/repository-map.md`: list the Phase 17 detailed plan and public demo evidence doc.
- Create `docs/review/phase-17-review.md`: review artifact after implementation and verification.

## Operator Inputs Needed Before Execution

The implementation worker must confirm or gather these values before running production actions:

- Public web hostname, for example `serviceops.example.com`.
- Public API hostname or reverse-proxy path, for example `api.serviceops.example.com`.
- Optional n8n UI hostname, if the n8n UI must be reachable.
- Whether Dokploy admin access will be IP-restricted, VPN-only, or temporarily disabled from public access.
- Whether local and production Telegram share one bot token or use separate tokens.
- Disposable staff smoke username and password, or a documented reason why staff-route smoke is deferred.
Do not write real hostnames, staff usernames, passwords, Telegram chat ids, bot tokens, API keys, or webhook secrets into tracked docs unless they are intentionally public placeholders.

## Task 1: Baseline Public Access And Runtime Inventory

**Files:**
- Create: `docs/operations/public-demo-launch-evidence.md`
- Modify: `docs/operations/operational-diagnostics.md`

- [ ] **Step 1: Create the evidence skeleton**

Create `docs/operations/public-demo-launch-evidence.md` with these sections:

```markdown
# Public Demo Launch Evidence: YYYY-MM-DD

This record is sanitized. Do not include passwords, bearer tokens, Telegram bot tokens, webhook secrets, API keys, raw provider payloads, customer phone numbers, Telegram chat ids, or real staff personal data.

## Scope

- Environment:
- Repository branch:
- Revision:
- Web hostname:
- API hostname:
- n8n UI hostname, if exposed:
- Operator:
- Final decision: Pending

## Baseline Access

| Check | Command | Result | Notes |
| --- | --- | --- | --- |
| Web HTTPS | `curl -fsS https://<web-host>/` | Pending | |
| API health HTTPS | `curl -fsS https://<api-host>/health` | Pending | |
| Direct web test port | `curl -I http://<host>:3001/` | Pending | Should not be needed publicly |
| Direct API test port | `curl -I http://<host>:8000/health` | Pending | Should not be needed publicly |
| Dokploy admin | `curl -I http://<host>:3000/` | Pending | Should be restricted |
| n8n direct port | `nc -vz <host> 5678` | Pending | Should not be public |
| PostgreSQL direct port | `nc -vz <host> 5432` | Pending | Should not be public |
| Redis direct port | `nc -vz <host> 6379` | Pending | Should not be public |

## Deployment Runtime

- Docker/Dokploy app status:
- API service status:
- Web service status:
- Worker service status:
- Telegram bot status:
- n8n status:
- PostgreSQL health:
- Redis health:

## Routing And HTTPS

- DNS records verified:
- HTTPS certificate issuer:
- Web route target:
- API route target:
- n8n UI route target:
- CORS allowed origins:

## Smoke Checks

- API health:
- Web root:
- Public intake:
- Public status by request number:
- Public status by token:
- Staff login:
- Dispatcher route:
- n8n request-created delivery:
- Telegram opt-in ownership:
- Backup command readiness:
- Restore dry-run readiness:

## Go/No-Go

- Decision:
- Remaining blockers:
- Follow-up owner:
```

- [ ] **Step 2: Run local baseline commands from the workstation**

Replace placeholders with the current candidate hostnames or IP. Do not paste secrets into commands.

```bash
curl -I --connect-timeout 5 --max-time 10 https://<web-host>/
curl -I --connect-timeout 5 --max-time 10 https://<api-host>/health
curl -I --connect-timeout 5 --max-time 10 http://<host>:3001/
curl -I --connect-timeout 5 --max-time 10 http://<host>:8000/health
for p in 22 80 443 3000 3001 8000 2377 7946 5432 5678 6379; do
  timeout 3 bash -c "</dev/tcp/<host>/$p" >/dev/null 2>&1 && echo "$p open" || echo "$p closed"
done
```

Expected:
- `443` reachable for public web/API routes after routing is complete.
- `5432`, `5678`, and `6379` closed externally.
- `3001` and `8000` not required externally after routing is complete.
- `3000` restricted or unavailable except from trusted access path.

- [ ] **Step 3: Run server-side runtime inventory**

Run from the VPS or approved remote shell:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs --tail=100 api
docker compose -f docker-compose.production.yml logs --tail=100 web
docker compose -f docker-compose.production.yml logs --tail=100 worker
docker compose -f docker-compose.production.yml logs --tail=100 telegram-bot
docker compose -f docker-compose.production.yml logs --tail=100 n8n
```

Expected:
- API and web are healthy or have clear deploy-time errors.
- PostgreSQL and Redis are private container services.
- n8n does not show a direct public `0.0.0.0:5678->5678/tcp` publication.
- Logs do not contain real secrets.

- [ ] **Step 4: Update diagnostics doc if the check commands are missing**

If `docs/operations/operational-diagnostics.md` does not already include external access checks, add a short section named `External Access Checks` with the curl and port-posture commands above. Keep commands placeholder-based.

## Task 2: Domain, HTTPS, And Reverse Proxy Routing

**Files:**
- Modify: `docs/operations/deployment-runbook.md`
- Modify: `.env.example` only if required values are missing or ambiguous.
- Modify: `docs/operations/public-demo-launch-evidence.md`

- [ ] **Step 1: Confirm DNS points to the VPS**

Run:

```bash
dig +short <web-host>
dig +short <api-host>
dig +short <n8n-host>
```

Expected:
- Web and API hostnames resolve to the VPS public IP.
- n8n hostname resolves only if the UI is intentionally exposed through Dokploy/Traefik.

- [ ] **Step 2: Configure Dokploy or reverse proxy routes**

In Dokploy/reverse proxy:
- Route web hostname to service `web` port `80`.
- Route API hostname to service `api` port `8000`.
- Route n8n hostname to service `n8n` port `5678` only if UI access is required.
- Do not publish n8n `5678` directly with Docker `ports`.
- Keep PostgreSQL and Redis without public routes.

- [ ] **Step 3: Verify HTTPS certificates**

Run:

```bash
curl -fsS https://<web-host>/ >/dev/null
curl -fsS https://<api-host>/health >/dev/null
openssl s_client -connect <web-host>:443 -servername <web-host> </dev/null 2>/dev/null | openssl x509 -noout -issuer -subject -dates
openssl s_client -connect <api-host>:443 -servername <api-host> </dev/null 2>/dev/null | openssl x509 -noout -issuer -subject -dates
```

Expected:
- Web root returns HTTP 200 over HTTPS.
- API health returns HTTP 200 over HTTPS.
- Certificates are valid for the configured hostnames.

- [ ] **Step 4: Update public environment values**

Set production values in Dokploy or the production environment, not in tracked files:

```bash
SERVICEOPS_PUBLIC_WEB_BASE_URL=https://<web-host>
SERVICEOPS_PUBLIC_API_BASE_URL=https://<api-host>
SERVICEOPS_CORS_ALLOWED_ORIGINS=https://<web-host>
```

If n8n UI is exposed:

```bash
N8N_HOST=<n8n-host>
N8N_PROTOCOL=https
N8N_WEBHOOK_URL=https://<n8n-host>/
```

Keep backend-to-n8n webhook targets private:

```bash
SERVICEOPS_N8N_REQUEST_CREATED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/request-created
SERVICEOPS_N8N_STATUS_CHANGED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/status-changed
SERVICEOPS_N8N_CLARIFICATION_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/clarification-requested
SERVICEOPS_N8N_CUSTOMER_ANSWERED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/customer-answered
SERVICEOPS_API_BASE_URL=http://api:8000
```

- [ ] **Step 5: Update runbook with any route-specific decisions**

Record the chosen route shape in `docs/operations/deployment-runbook.md` using placeholders, not real secrets. If the project uses API subdomain routing, document it. If it uses `/api` path routing, document the path rewrite and CORS behavior.

## Task 3: Close Temporary Direct Ports And Restrict Admin Surfaces

**Files:**
- Modify: `docker-compose.production.yml` only if direct public port publication is still present and not needed after Dokploy routing.
- Modify: `docs/operations/deployment-runbook.md`
- Modify: `docs/operations/public-demo-launch-evidence.md`
- Test: `tools/operations/test_production_compose_contract.py` if Compose changes.

- [ ] **Step 1: Inspect current Compose port posture**

Run locally:

```bash
docker compose -f docker-compose.production.yml --env-file .env.example config
```

Expected:
- n8n does not publish `5678`.
- PostgreSQL and Redis do not publish public ports.
- API/web direct `ports` are either intentionally present for Dokploy routing or can be removed/disabled for public demo posture.

- [ ] **Step 2: Prefer Dokploy/reverse proxy routing over direct IP ports**

If direct `ports` for API/web are not needed by Dokploy:
- Remove or make them opt-in by environment for local production-config validation.
- Keep `expose` so services remain reachable inside the Compose network.

If direct `ports` must remain for Dokploy in this deployment:
- Use host firewall rules to block public access to `3001` and `8000`.
- Document the reason in `docs/operations/public-demo-launch-evidence.md`.

- [ ] **Step 3: Restrict Dokploy admin access**

Apply one approved method:
- Trusted-IP firewall allowlist for `3000`.
- VPN-only access.
- Reverse-proxy auth plus firewall default deny.
- Temporary closure when not actively administering.

Run external checks:

```bash
curl -I --connect-timeout 5 --max-time 10 http://<host>:3000/
curl -I --connect-timeout 5 --max-time 10 http://<host>:3001/
curl -I --connect-timeout 5 --max-time 10 http://<host>:8000/health
nc -vz -w 3 <host> 5678
nc -vz -w 3 <host> 5432
nc -vz -w 3 <host> 6379
```

Expected:
- `3000` is unavailable from untrusted networks or explicitly protected.
- `3001` and `8000` are not required for public demo access.
- `5678`, `5432`, and `6379` are unavailable externally.

- [ ] **Step 4: Update contract tests if Compose changed**

If `docker-compose.production.yml` changed, run:

```bash
python3 tools/operations/test_production_compose_contract.py
docker compose -f docker-compose.production.yml --env-file .env.example config --quiet
```

Expected: PASS.

## Task 4: Telegram Polling Ownership And Opt-In Smoke

**Files:**
- Modify: `docs/operations/deployment-runbook.md`
- Modify: `docs/operations/smoke-tests.md`
- Modify: `docs/operations/public-demo-launch-evidence.md`
- Modify: `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`

- [ ] **Step 1: Decide bot token posture**

Choose one:
- Separate local/development and production Telegram bot tokens.
- One shared token with production owning polling and local `telegram-bot` stopped.

Expected:
- The chosen rule is recorded in `docs/operations/deployment-runbook.md` and `docs/operations/public-demo-launch-evidence.md`.

- [ ] **Step 2: Verify production polling ownership**

Run:

```bash
docker compose -f docker-compose.production.yml logs --tail=100 telegram-bot
```

If local services are running, verify local Telegram polling is stopped or uses a separate development token:

```bash
docker compose ps telegram-bot
```

Expected:
- Only the intended bot process polls the production bot token.

- [ ] **Step 3: Smoke Telegram opt-in safely**

Preferred safe path for public demo closure:
- Create a smoke request.
- Trigger Telegram opt-in.
- Use either the production Telegram `/start <token>` flow with a test account or the protected/local simulation documented in operations docs.

Expected:
- Opt-in token links to the intended production request.
- No local bot consumes production `/start` traffic.
- Evidence records request number only if it is safe and non-sensitive.

- [ ] **Step 4: Add dated pointer to historical n8n evidence**

Append a short dated follow-up to `docs/operations/self-hosted-n8n-vps-evidence-2026-06-16.md`:

```markdown
## Follow-Up: YYYY-MM-DD

Public demo launch closure evidence now lives in `docs/operations/public-demo-launch-evidence.md`. That record supersedes this file for current port posture, HTTPS routing, and Telegram polling ownership.
```

## Task 5: Public Smoke Evidence And Backup/Restore Readiness

**Files:**
- Modify: `docs/operations/smoke-tests.md`
- Modify: `docs/operations/public-demo-launch-evidence.md`
- Modify: `docs/operations/backup-restore.md` only if the current restore-dry-run instructions are insufficient for public demo go/no-go.
- Modify: `tools/operations/smoke_test.sh` only if current script cannot support HTTPS smoke.
- Modify: `tools/operations/test_smoke_script_contract.py` only if script changes.

- [ ] **Step 1: Run public HTTPS smoke**

Run:

```bash
SERVICEOPS_PUBLIC_API_BASE_URL=https://<api-host> \
SERVICEOPS_PUBLIC_WEB_BASE_URL=https://<web-host> \
bash tools/operations/smoke_test.sh
```

If staff smoke credentials are available:

```bash
SERVICEOPS_PUBLIC_API_BASE_URL=https://<api-host> \
SERVICEOPS_PUBLIC_WEB_BASE_URL=https://<web-host> \
SERVICEOPS_SMOKE_STAFF_USERNAME="<disposable-dispatcher-username>" \
SERVICEOPS_SMOKE_STAFF_PASSWORD="<disposable-dispatcher-password>" \
bash tools/operations/smoke_test.sh
```

Expected:
- API health passes.
- Web root passes.
- Intake creates a smoke request.
- Status by request number passes.
- Status by public token passes.
- Staff login and dispatcher route pass when disposable credentials are supplied.

- [ ] **Step 2: Verify n8n notification path**

Create or reuse a smoke request that triggers `request-created`.

Inspect:

```bash
docker compose -f docker-compose.production.yml logs --tail=200 api
docker compose -f docker-compose.production.yml logs --tail=200 n8n
```

Expected:
- API emits request-created notification.
- n8n accepts the private Compose webhook URL.
- n8n calls back to `/notifications/n8n/delivery-results`.
- API records delivery as sent, queued, or failed with an operator-safe reason.

- [ ] **Step 3: Verify backup command readiness**

Run syntax checks locally:

```bash
bash -n tools/operations/postgres_backup.sh
bash -n tools/operations/postgres_restore.sh
```

Run production backup command only from the approved production shell with approved backup directory:

```bash
tools/operations/postgres_backup.sh
```

Expected:
- Backup file and checksum are created in the approved backup directory.
- Evidence records timestamp, filename pattern, checksum status, and retention path without exposing credentials.

- [ ] **Step 4: Verify restore dry-run readiness**

Follow `docs/operations/backup-restore.md` against a non-production target only.

Expected:
- Restore target name clearly marks non-production.
- Restore command refuses or is not run against production.
- Evidence records whether the dry run passed or remains blocked.

## Task 6: Documentation Harness And Phase Handoff

**Files:**
- Modify: `tools/repo-checks/check_docs.py`
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`
- Modify: `docs/harness/repository-map.md`
- Create: `docs/review/phase-17-review.md`

- [ ] **Step 1: Update repo checks**

Add required paths to `tools/repo-checks/check_docs.py`:

```python
"docs/execution-plans/detailed/17-public-demo-and-launch-closure-implementation.md",
"docs/operations/public-demo-launch-evidence.md",
"docs/review/phase-17-review.md",
```

Only require the review artifact after it exists in the same implementation branch.

- [ ] **Step 2: Update execution index after Phase 17 implementation**

When Phase 17 is implemented and reviewed:
- Mark current detailed plan as completed by leaving it in `docs/execution-plans/detailed/`.
- Set active phase to `phases/18-portfolio-packaging-and-demo-mode.md`.
- Set current detailed plan to none until Phase 18 planning begins.

- [ ] **Step 3: Update project notes after Phase 17 implementation**

Record:
- Public demo route.
- HTTPS posture.
- Direct port posture.
- Dokploy access decision.
- Smoke evidence path.
- Remaining launch risks, if any.

- [ ] **Step 4: Update repository map**

Add:
- Phase 17 detailed plan.
- Public demo launch evidence doc.
- Phase 17 review artifact.

- [ ] **Step 5: Create Phase 17 review artifact**

Create `docs/review/phase-17-review.md` with:

```markdown
# Phase 17 Review: Public Demo And Launch Closure

Date:

## Reviewer Role

## Files Reviewed

## Verification Commands

## Blocking Issues

## Non-Blocking Issues

## Public Demo Decision

## Suggested Follow-Up Slice

## Documentation Updates

## Final Recommendation
```

## Verification

Run these before requesting review:

- [ ] `python3 tools/repo-checks/check_docs.py`
- [ ] `python3 tools/operations/test_smoke_script_contract.py`
- [ ] `python3 tools/operations/test_production_compose_contract.py`
- [ ] `docker compose -f docker-compose.production.yml --env-file .env.example config --quiet`
- [ ] `bash -n tools/operations/postgres_backup.sh`
- [ ] `bash -n tools/operations/postgres_restore.sh`
- [ ] `bash -n tools/operations/smoke_test.sh`
- [ ] `SERVICEOPS_PUBLIC_API_BASE_URL=https://<api-host> SERVICEOPS_PUBLIC_WEB_BASE_URL=https://<web-host> bash tools/operations/smoke_test.sh`
- [ ] Staff-route smoke with disposable credentials, or record why it remains blocked.
- [ ] External port posture check for `22`, `80`, `443`, `3000`, `3001`, `8000`, `2377`, `7946`, `5432`, `5678`, and `6379`.
- [ ] Production n8n request-created delivery smoke or documented equivalent evidence.
- [ ] Telegram opt-in ownership smoke or documented equivalent evidence.
- [ ] Tracked-file hygiene scan:

```bash
rg -n "sk-|SERVICEOPS_[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|API_KEY)=.+[A-Za-z0-9_-]{16,}" . \
  --glob '!apps/**/.venv/**' \
  --glob '!node_modules/**' \
  --glob '!reference/figma/node_modules/**'
```

Expected: no real reusable secrets in tracked files.

## Subagent Review Gate

Ask the reviewer to inspect:

- Public web and API demo routes work over HTTPS and do not require IP-address test ports.
- Direct exposure of n8n, PostgreSQL, Redis, and temporary API/web test ports is closed or justified.
- Dokploy admin access is restricted or explicitly documented as non-public.
- Smoke evidence is specific, dated, sanitized, and reproducible.
- Telegram polling ownership prevents local and production bots from competing for the same token.
- Phase 17 does not add unrelated product features.
- Phase 18 can start from a stable public demo baseline.

## Self-Review

- Phase 17 deliverables are covered by Tasks 1-6.
- The plan preserves the operations boundary and does not add product features.
- The plan records real demo readiness with evidence rather than assuming readiness from docs.
- The plan keeps all sensitive values out of tracked files.
- The plan updates repository entry points so future workers can find the Phase 17 evidence and review.
