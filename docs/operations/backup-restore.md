# Backup And Restore

## Schedule

For MVP operations, run a PostgreSQL backup at least daily and before deployment changes that touch persistence or migrations. Keep `SERVICEOPS_BACKUP_RETENTION_DAYS` worth of backups on the VPS and copy critical backups to storage outside the VPS.

## Compose-Network Backup

Production Compose keeps PostgreSQL private, so run host-initiated backups through a temporary PostgreSQL client container on the Compose network instead of publishing the database port:

```bash
mkdir -p /var/backups/serviceops
docker compose -f docker-compose.production.yml run --rm \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=serviceops \
  -e POSTGRES_USER=serviceops \
  -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  -e SERVICEOPS_BACKUP_DIR=/backups \
  -v /var/backups/serviceops:/backups \
  postgres \
  /bin/sh -lc 'pg_dump --host="$POSTGRES_HOST" --port="$POSTGRES_PORT" --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --format=custom --no-owner --no-acl --file="/backups/serviceops-$(date -u +%Y%m%d-%H%M%S).dump"'
sha256sum /var/backups/serviceops/serviceops-*.dump
```

Use `tools/operations/postgres_backup.sh` from a shell that can reach the database over a private network endpoint:

## Direct Backup Script

```bash
POSTGRES_HOST=<private database host> \
POSTGRES_PORT=5432 \
POSTGRES_DB=serviceops \
POSTGRES_USER=serviceops \
POSTGRES_PASSWORD=<production password> \
SERVICEOPS_BACKUP_DIR=/var/backups/serviceops \
tools/operations/postgres_backup.sh
```

The script writes `serviceops-YYYYmmdd-HHMMSS.dump` and a matching `.sha256` file.

## Container Backup

If `pg_dump` is only available in the PostgreSQL container, use:

```bash
mkdir -p /var/backups/serviceops
docker compose -f docker-compose.production.yml exec -T postgres \
  pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
  --format=custom --no-owner --no-acl \
  > "/var/backups/serviceops/serviceops-$(date -u +%Y%m%d-%H%M%S).dump"
```

Create a checksum after the dump:

```bash
sha256sum /var/backups/serviceops/serviceops-*.dump
```

## Checksum Verification

Before restore or off-host copy validation:

```bash
sha256sum -c /var/backups/serviceops/serviceops-YYYYmmdd-HHMMSS.dump.sha256
```

## Restore

Restore only into the intended database and only after confirming the backup file and target environment:

```bash
POSTGRES_HOST=<private database host> \
POSTGRES_PORT=5432 \
POSTGRES_DB=serviceops \
POSTGRES_USER=serviceops \
POSTGRES_PASSWORD=<production password> \
tools/operations/postgres_restore.sh /var/backups/serviceops/serviceops-YYYYmmdd-HHMMSS.dump
```

The restore script uses `pg_restore --clean --if-exists --no-owner --no-acl`.

## Restore Drill

1. Create a non-production PostgreSQL target.
2. Restore the latest backup into that target.
3. Run `python -m serviceops_api.operations.migrate` against the restored database.
4. Run the smoke tests against the restored stack.
5. Record the backup timestamp, restore duration, and any manual steps.

## Retention

Use `SERVICEOPS_BACKUP_RETENTION_DAYS` as the minimum local retention window. Host-level cleanup can delete backups older than that window only after confirming an off-host copy exists when required by operations policy.
