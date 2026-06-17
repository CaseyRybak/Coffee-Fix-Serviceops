# Incident Response

Use this checklist during production degradation. Keep customer-facing updates short, factual, and free of internal logs or secrets.

## Common Rules

- Assign one incident owner.
- Preserve the first failing timestamp, affected service, affected `request_number` or `event_id`, and last deployment or configuration change.
- Use `docs/operations/operational-diagnostics.md` for log and database queries.
- Do not paste passwords, tokens, webhook secrets, API keys, raw AI prompts, provider bodies, Telegram chat ids, or customer phone numbers into incident notes.
- Prefer rollback when a recent deployment caused service degradation and data integrity is intact.
- Prefer restore only when production data is corrupted, missing, or unrecoverable through application-level repair.

## Degraded API

- First checks: `/health`, API service logs, database connectivity, Redis connectivity, latest deployment timestamp.
- Customer impact: intake, status lookup, staff workspaces, notification callbacks, and AI routes may fail.
- Containment: disable public routing or put Dokploy into maintenance mode when errors are widespread.
- Rollback criteria: API errors began immediately after a deployment or environment change.
- Restore criteria: only when database corruption or destructive migration is confirmed.
- Owner handoff: backend owner plus operations owner.
- Evidence: health output, error log excerpts with `action`, `target`, `outcome`, deployment revision, and affected request numbers.

## Degraded Web

- First checks: web root response, static asset loading, browser console, web service logs, API base URL configuration.
- Customer impact: customers may be unable to submit requests or view status; staff may lose workspace access.
- Containment: route users to a maintenance page or temporary intake channel.
- Rollback criteria: broken assets, build regression, wrong `VITE_SERVICEOPS_API_BASE_URL`, or recent web image change.
- Restore criteria: not applicable unless web degradation is paired with data loss.
- Owner handoff: frontend owner plus operations owner.
- Evidence: HTTP status, screenshot when useful, web image tag, and API base URL value without secrets.

## PostgreSQL Unavailable Or Slow

- First checks: PostgreSQL container health, disk space, connection count, slow queries, recent backup or restore actions.
- Customer impact: nearly all writes and most reads may fail.
- Containment: stop nonessential write-heavy tasks and pause public routing if errors affect customers.
- Rollback criteria: recent schema or query change caused slow or failed operations.
- Restore criteria: confirmed data loss, corrupted schema, or failed destructive migration.
- Owner handoff: database owner plus backend owner.
- Evidence: `docker compose logs postgres`, disk usage, connection count, migration logs, backup timestamp, and checksum status.

## Redis Or Worker Failure

- First checks: Redis container health, worker logs, Celery ping, queue length, failed embedding task logs.
- Customer impact: background jobs and knowledge-base embedding may lag; request intake can still work if API and database are healthy.
- Containment: keep API online if synchronous paths are healthy; pause live AI/RAG workflows if embeddings are stale.
- Rollback criteria: worker image or environment change caused task crashes.
- Restore criteria: not applicable unless paired with database corruption.
- Owner handoff: backend owner plus operations owner.
- Evidence: worker log lines with `knowledge_base.embedding_*`, Redis health output, and task failure timestamps.

## Telegram Bot Failure

- First checks: Telegram bot logs, bot token presence, API base URL, opt-in link API failures, Telegram platform status.
- Customer impact: Telegram opt-in and customer notifications may fail; public status page remains the fallback.
- Containment: stop bot polling if it loops on failures.
- Rollback criteria: bot image, bot configuration, or API URL change broke linking.
- Restore criteria: not applicable unless notification data is corrupted.
- Owner handoff: integrations owner plus operations owner.
- Evidence: `telegram.opt_in_linked` failure logs, API status, and affected request numbers without tokens or chat ids.

## n8n Webhook Or Callback Failure

- First checks: n8n service logs, workflow active status, webhook URLs, shared webhook secret, callback secret, recent workflow changes.
- Customer impact: staff or customer notifications may be delayed or missing.
- Containment: pause failing workflow, disable public notification traffic if repeated failures create backlog, use manual staff notification.
- Rollback criteria: workflow edit or environment change caused webhook or callback failures.
- Restore criteria: not applicable unless delivery records are corrupted.
- Owner handoff: automation owner plus backend owner.
- Evidence: `notification.event_queued`, `notification.delivery_recorded`, `notification.callback_recorded`, n8n execution id, and workflow id.

## AI Or Embedding Provider Degradation

- First checks: provider mode, provider credentials, timeout/retry settings, API/worker logs, RAG seed status.
- Customer impact: dispatcher suggestions or embedding tasks may fail; repair workflow should continue manually.
- Containment: switch `SERVICEOPS_AI_PROVIDER` or `SERVICEOPS_EMBEDDING_PROVIDER` back to `deterministic` if live provider degradation affects staff.
- Rollback criteria: provider config or model change caused failures.
- Restore criteria: not applicable unless knowledge-base rows were corrupted.
- Owner handoff: AI/RAG owner plus operations owner.
- Evidence: `ai.suggestions_generated` logs, `knowledge_base.embedding_completed` logs, provider mode, and failure reason without raw prompts or provider bodies.

## Notification Delivery Backlog

- First checks: notification delivery attempts, n8n status, Telegram bot status, API callback route, failed delivery count.
- Customer impact: customers or dispatchers may not receive timely updates.
- Containment: communicate through manual channels for high-urgency requests and pause noisy retries.
- Rollback criteria: recent notification code or n8n workflow change introduced duplicate or failed events.
- Restore criteria: only when delivery records are corrupted or missing and must be reconstructed.
- Owner handoff: automation owner plus dispatcher lead.
- Evidence: failed delivery query, affected `event_id` values, and n8n execution ids.

## Credential Access Incident

- First checks: identify credential type, affected service, access scope, and whether related sessions or callbacks are still valid.
- Customer impact: depends on affected credential scope.
- Containment: disable the affected credential path, redeploy affected services if configuration changes, and invalidate related sessions or callbacks.
- Rollback criteria: rollback only if a deployment introduced the credential access issue.
- Restore criteria: not applicable unless attacker-modified data is confirmed.
- Owner handoff: operations owner plus product owner.
- Evidence: redacted incident summary, mitigation timestamp, and services redeployed.

## Restore-From-Backup Decision

- First checks: confirm data loss or corruption, identify latest verified backup, verify checksum, identify target database, and estimate data loss window.
- Customer impact: restore can lose writes after backup timestamp and requires maintenance mode.
- Containment: stop writes before restore and preserve current broken state for later analysis.
- Rollback criteria: use rollback instead when code is bad but data is intact.
- Restore criteria: corrupted production data, destructive migration, or accidental deletion that cannot be repaired safely.
- Owner handoff: operations owner, database owner, and product owner approval.
- Evidence: backup timestamp, checksum result, restore command target, migration result, smoke result, operator, and approval.
