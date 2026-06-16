# Self-Hosted n8n VPS Evidence: June 16, 2026

This record captures the production handoff from n8n Cloud to the self-hosted n8n service on the Aeza VPS. It is sanitized and must not contain passwords, bearer tokens, Telegram bot tokens, webhook secrets, API keys, raw provider payloads, customer phone numbers, or Telegram chat ids.

## Scope

- Environment: Aeza VPS test production environment.
- Repository branch: `main`.
- Relevant revisions: `6565f71` introduced the local n8n runtime and workflow import path; `2c9e472` allowed n8n workflow code nodes to read environment variables.
- n8n runtime: self-hosted service in the production Docker Compose app.
- Telegram mode: one shared Telegram bot token and one shared staff chat for the pet-project setup.

## Workflow Runtime

The following repository workflow exports were imported and published on the VPS n8n service:

- `ServiceOps - Request Created Dispatcher Alert`: `fbEwkH56MkvmDnsD`
- `ServiceOps - Status Changed Customer Notification`: `0njpM50BqmqJeZE2`
- `ServiceOps - Clarification Customer Notification`: `bJWa9A1ALnypyE2V`
- `ServiceOps - Customer Answered Dispatcher Alert`: `PVYG8clWqn9opv1l`

The production API webhook targets were changed from n8n Cloud URLs to private Compose-network URLs:

```bash
SERVICEOPS_N8N_REQUEST_CREATED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/request-created
SERVICEOPS_N8N_STATUS_CHANGED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/status-changed
SERVICEOPS_N8N_CLARIFICATION_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/clarification-requested
SERVICEOPS_N8N_CUSTOMER_ANSWERED_WEBHOOK_URL=http://n8n:5678/webhook/serviceops/customer-answered
```

n8n callback nodes use the private API service URL:

```bash
SERVICEOPS_API_BASE_URL=http://api:8000
```

## Verification

- n8n logs showed the four imported workflows activated after restart.
- Production request `CFX-20260616-000008` verified the request-created notification path end-to-end:
  - API emitted the request-created notification event.
  - Self-hosted n8n accepted the webhook and completed the workflow execution successfully.
  - Telegram delivery to the dispatcher channel succeeded.
  - n8n called `POST /notifications/n8n/delivery-results`.
  - API recorded the delivery attempt as `sent`.
- The earlier `CFX-20260616-000007` failure was caused by production API webhook URLs still pointing to n8n Cloud. It remained `queued` until the API environment was corrected and the API service was recreated.
- Full production dispatcher clarification smoke was not completed because disposable production staff credentials were not available during the check. Local smoke covers the protected opt-in simulation and clarification delivery path.

## Telegram Opt-In Runtime

For `CFX-20260616-000008`, the customer initially saw "failed to connect notifications". The cause was a local `telegram-bot` container polling the same Telegram bot token as production:

- The local bot received the production `/start <token>` update.
- The local bot called the local API with a production opt-in token.
- The local API returned `404 Not Found` because it did not own that production token.
- The local `telegram-bot` service was stopped, production polling received the retry, and the user confirmed the opt-in worked.

Current operating rule: while local and production share one Telegram bot token, keep the local `telegram-bot` stopped whenever production polling is active. Local notification smoke should simulate opt-in through the protected API endpoint instead of consuming real Telegram `/start` traffic.

## Port Posture

Observed production posture after the self-hosted n8n check:

- n8n showed only container-internal `5678/tcp`; there was no direct Docker publication like `0.0.0.0:5678->5678/tcp`.
- External reachability checks succeeded for current public/test entrypoints: `80`, `443`, `3000`, `3001`, and `8000`.
- External reachability checks for Docker Swarm/internal networking ports `2377/tcp` and `7946/tcp` timed out.
- Docker Swarm was active as a single-node manager for Dokploy internal services; the ServiceOps app was deployed as Compose, not as a Swarm stack.

Interpretation: `2377` and `7946` may listen on the host because Docker Swarm is active, but they were not externally reachable and had no explicit public firewall allow rules. They are not required to be publicly reachable for this single-node ServiceOps deployment.

## Follow-Ups

- Configure production domains and HTTPS routing for web/API/n8n UI where needed.
- Close temporary direct public web/API test ports `3001` and `8000` after reverse-proxy routing is ready.
- Restrict Dokploy `3000` to trusted IP/VPN access before public launch.
- Keep n8n `5678` private; route the UI through Dokploy/Traefik only when UI access is required.
- Rotate setup-exposed n8n MCP/API secrets before public launch.
- Repeat smoke tests after the real database transfer and after disposable production staff credentials are available.
