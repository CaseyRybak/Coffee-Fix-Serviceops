#!/usr/bin/env bash
set -euo pipefail

SERVICEOPS_PUBLIC_API_BASE_URL="${SERVICEOPS_PUBLIC_API_BASE_URL:-http://localhost:8000}"
SERVICEOPS_PUBLIC_WEB_BASE_URL="${SERVICEOPS_PUBLIC_WEB_BASE_URL:-http://localhost:3000}"
N8N_TEST_WEBHOOK_URL="${N8N_TEST_WEBHOOK_URL:-}"
SERVICEOPS_SMOKE_STAFF_USERNAME="${SERVICEOPS_SMOKE_STAFF_USERNAME:-}"
SERVICEOPS_SMOKE_STAFF_PASSWORD="${SERVICEOPS_SMOKE_STAFF_PASSWORD:-}"

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
    "phone": "+15555550100",
    "client_type": "private"
  },
  "machine": {
    "brand": "La Marzocco",
    "model": "Linea Mini",
    "location_type": "office"
  },
  "problem": "Smoke test request",
  "address": "Smoke test address",
  "urgency": "planned"
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
PY
)"

request_number="$(printf '%s\n' "$parsed" | sed -n '1p')"

if [ -z "$request_number" ]; then
  printf 'intake response missing request_number\n' >&2
  exit 1
fi

printf 'checking status by request number: %s\n' "$request_number"
status_response="$(curl -fsS "$api_base/service-requests/$request_number/status")"
public_token="$(
  RESPONSE_JSON="$status_response" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["RESPONSE_JSON"])
print(payload["public_token"])
PY
)"

if [ -z "$public_token" ]; then
  printf 'status response missing public_token\n' >&2
  exit 1
fi

printf 'checking status by public token\n'
curl -fsS "$api_base/status/$public_token" >/dev/null

if [ -n "$SERVICEOPS_SMOKE_STAFF_USERNAME" ] || [ -n "$SERVICEOPS_SMOKE_STAFF_PASSWORD" ]; then
  if [ -z "$SERVICEOPS_SMOKE_STAFF_USERNAME" ] || [ -z "$SERVICEOPS_SMOKE_STAFF_PASSWORD" ]; then
    printf 'SERVICEOPS_SMOKE_STAFF_USERNAME and SERVICEOPS_SMOKE_STAFF_PASSWORD must be set together.\n' >&2
    exit 1
  fi

  printf 'checking persisted staff login and dispatcher route for %s\n' "$SERVICEOPS_SMOKE_STAFF_USERNAME"
  staff_login_payload="$(
    STAFF_USERNAME="$SERVICEOPS_SMOKE_STAFF_USERNAME" \
    STAFF_PASSWORD="$SERVICEOPS_SMOKE_STAFF_PASSWORD" \
    python3 - <<'PY'
import json
import os

print(json.dumps({
    "username": os.environ["STAFF_USERNAME"],
    "password": os.environ["STAFF_PASSWORD"],
}))
PY
  )"
  staff_token="$(
    curl -fsS -X POST "$api_base/staff/login" \
      -H "content-type: application/json" \
      -d "$staff_login_payload" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
  )"
  if [ -z "$staff_token" ]; then
    printf 'staff login response did not include an access token\n' >&2
    exit 1
  fi
  curl -fsS "$api_base/dispatcher/service-requests" \
    -H "authorization: Bearer $staff_token" >/dev/null
else
  printf 'SERVICEOPS_SMOKE_STAFF_USERNAME/PASSWORD not configured; skipping staff route smoke check.\n'
fi

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
