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

POSTGRES_DB="${POSTGRES_DB:-serviceops}"
POSTGRES_USER="${POSTGRES_USER:-serviceops}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-serviceops}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

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
