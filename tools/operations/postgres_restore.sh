#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  printf 'usage: %s /path/to/serviceops-backup.dump\n' "$0" >&2
  exit 2
fi

backup_path="$1"
if [ ! -f "$backup_path" ]; then
  printf 'backup file not found: %s\n' "$backup_path" >&2
  exit 2
fi

checksum_path="${backup_path}.sha256"
if [ ! -f "$checksum_path" ]; then
  printf 'backup checksum file not found: %s\n' "$checksum_path" >&2
  exit 2
fi

POSTGRES_DB="${POSTGRES_DB:-serviceops}"
POSTGRES_USER="${POSTGRES_USER:-serviceops}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-serviceops}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
SERVICEOPS_RESTORE_CONFIRM="${SERVICEOPS_RESTORE_CONFIRM:-}"
SERVICEOPS_ALLOW_PRODUCTION_RESTORE="${SERVICEOPS_ALLOW_PRODUCTION_RESTORE:-false}"

if [ "$SERVICEOPS_RESTORE_CONFIRM" != "I_UNDERSTAND_THIS_WILL_OVERWRITE_TARGET_DB" ]; then
  printf 'set SERVICEOPS_RESTORE_CONFIRM=I_UNDERSTAND_THIS_WILL_OVERWRITE_TARGET_DB before restore\n' >&2
  exit 2
fi

if ! printf '%s\n' "$POSTGRES_DB" | grep -Eiq 'restore|drill|test'; then
  if [ "$SERVICEOPS_ALLOW_PRODUCTION_RESTORE" != "true" ]; then
    printf 'refusing restore into POSTGRES_DB=%s without SERVICEOPS_ALLOW_PRODUCTION_RESTORE=true\n' "$POSTGRES_DB" >&2
    exit 2
  fi
fi

sha256sum -c "$checksum_path"

PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
  --host="$POSTGRES_HOST" \
  --port="$POSTGRES_PORT" \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  "$backup_path"

printf 'restored %s\n' "$backup_path"
