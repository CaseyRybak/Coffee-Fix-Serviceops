#!/usr/bin/env bash
set -euo pipefail

SERVICEOPS_PUBLIC_API_BASE_URL="${SERVICEOPS_PUBLIC_API_BASE_URL:-http://localhost:8000}"
SERVICEOPS_PUBLIC_WEB_BASE_URL="${SERVICEOPS_PUBLIC_WEB_BASE_URL:-http://localhost:3000}"
N8N_TEST_WEBHOOK_URL="${N8N_TEST_WEBHOOK_URL:-}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$1" >&2
    exit 2
  }
}

require_command curl
require_command python3

api_base="${SERVICEOPS_PUBLIC_API_BASE_URL%/}"
web_base="${SERVICEOPS_PUBLIC_WEB_BASE_URL%/}"

printf 'checking API health: %s/health\n' "$api_base"
curl -fsS "$api_base/health" >/dev/null

printf 'checking web root: %s/\n' "$web_base"
curl -fsS "$web_base/" >/dev/null

request_payload='{
  "customer": {
    "name": "Smoke Test",
    "phone": "+15555550100"
  },
  "machine": {
    "brand": "La Marzocco",
    "model": "Linea Mini"
  },
  "problem_description": "Smoke test request",
  "urgency": "standard"
}'

printf 'creating smoke service request\n'
response="$(
  curl -fsS -X POST "$api_base/service-requests" \
    -H "content-type: application/json" \
    -d "$request_payload"
)"

parsed="$(
  RESPONSE_JSON="$response" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["RESPONSE_JSON"])
print(payload["request_number"])
print(payload["public_token"])
PY
)"

request_number="$(printf '%s\n' "$parsed" | sed -n '1p')"
public_token="$(printf '%s\n' "$parsed" | sed -n '2p')"

if [ -z "$request_number" ] || [ -z "$public_token" ]; then
  printf 'intake response missing request_number or public_token\n' >&2
  exit 1
fi

printf 'checking status by request number: %s\n' "$request_number"
curl -fsS "$api_base/service-requests/$request_number/status" >/dev/null

printf 'checking status by public token\n'
curl -fsS "$api_base/status/$public_token" >/dev/null

if [ -n "$N8N_TEST_WEBHOOK_URL" ]; then
  printf 'checking n8n test webhook: %s\n' "$N8N_TEST_WEBHOOK_URL"
  curl -fsS -X POST "$N8N_TEST_WEBHOOK_URL" \
    -H "content-type: application/json" \
    -d '{"source":"serviceops-smoke"}' >/dev/null
else
  printf 'N8N_TEST_WEBHOOK_URL is not configured; manually verify the n8n webhook path.\n'
fi

printf 'manual follow-up: inspect worker logs and Telegram bot profile logs in Dokploy or Docker Compose.\n'
printf 'smoke checks passed for request %s\n' "$request_number"
