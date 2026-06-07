#!/usr/bin/env bash
set -euo pipefail

POSTGRES_DB="${POSTGRES_DB:-serviceops}"
POSTGRES_USER="${POSTGRES_USER:-serviceops}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-serviceops}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
SERVICEOPS_BACKUP_DIR="${SERVICEOPS_BACKUP_DIR:-./backups}"

mkdir -p "$SERVICEOPS_BACKUP_DIR"

timestamp="$(date -u +%Y%m%d-%H%M%S)"
backup_path="$SERVICEOPS_BACKUP_DIR/serviceops-$timestamp.dump"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  --host="$POSTGRES_HOST" \
  --port="$POSTGRES_PORT" \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  --format=custom \
  --no-owner \
  --no-acl \
  --file="$backup_path"

sha256sum "$backup_path" > "$backup_path.sha256"
printf '%s\n' "$backup_path"
