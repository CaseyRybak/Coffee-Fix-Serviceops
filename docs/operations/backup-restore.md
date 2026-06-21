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
SERVICEOPS_RESTORE_CONFIRM=I_UNDERSTAND_THIS_WILL_OVERWRITE_TARGET_DB \
POSTGRES_DB=serviceops_restore_drill \
tools/operations/postgres_restore.sh /var/backups/serviceops/serviceops-YYYYmmdd-HHMMSS.dump
```

The restore script verifies the matching `.sha256` file before running `pg_restore --clean --if-exists --no-owner --no-acl`. By default it refuses targets whose database name does not include `restore`, `drill`, or `test`; production restore requires `SERVICEOPS_ALLOW_PRODUCTION_RESTORE=true` plus incident-owner approval.

## Restore Drill

1. Create a non-production PostgreSQL target.
2. Restore the latest backup into that target.
3. Run `python -m serviceops_api.operations.migrate` against the restored database.
4. Run the smoke tests against the restored stack.
5. Record the backup timestamp, restore duration, and any manual steps.

## Production-Safe Restore Dry-Run

Run this dry-run at launch readiness time and after backup procedure changes. The dry-run must never target production data.

### Abort Conditions

Stop before running `postgres_restore.sh` when any condition is true:

- Target host is the production PostgreSQL host.
- Target database name is the production database name.
- `SERVICEOPS_DATABASE_URL` points at the production database.
- Backup checksum verification fails.
- Backup age is outside the approved recovery window.
- The operator cannot identify the backup timestamp, target host, target database, and restore owner.

### Dry-Run Target

Use a disposable Compose project or temporary PostgreSQL database:

```bash
export SERVICEOPS_RESTORE_DRILL_PROJECT=serviceops-restore-drill
export SERVICEOPS_RESTORE_DRILL_DB=serviceops_restore_drill

docker compose -p "$SERVICEOPS_RESTORE_DRILL_PROJECT" \
  -f docker-compose.production.yml up -d postgres redis
```

Do not route web, API, Telegram bot, or n8n publicly for the dry-run target.

Create the disposable database before running the restore script:

```bash
docker compose -p "$SERVICEOPS_RESTORE_DRILL_PROJECT" \
  -f docker-compose.production.yml exec -T \
  -e PGPASSWORD="$POSTGRES_PASSWORD" \
  postgres \
  createdb --host=localhost --port=5432 --username=serviceops "$SERVICEOPS_RESTORE_DRILL_DB"
```

Run these snippets from the repository root. If production overrides `POSTGRES_USER`, replace `serviceops` in the dry-run commands with the restore-drill database user from the disposable environment, not the production database user.

### Verify Checksum

```bash
sha256sum -c /var/backups/serviceops/serviceops-YYYYmmdd-HHMMSS.dump.sha256
```

Expected: checksum succeeds before restore begins.

### Restore Into Disposable Target

```bash
docker compose -p "$SERVICEOPS_RESTORE_DRILL_PROJECT" \
  -f docker-compose.production.yml run --rm \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB="$SERVICEOPS_RESTORE_DRILL_DB" \
  -e POSTGRES_USER=serviceops \
  -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  -v "$PWD:/workspace:ro" \
  -v /var/backups/serviceops:/backups:ro \
  postgres \
  bash -lc 'cd /workspace && tools/operations/postgres_restore.sh /backups/serviceops-YYYYmmdd-HHMMSS.dump'
```

Before running the command, print and verify the target values in the shell. The database name must include `restore`, `drill`, or another non-production marker approved by the incident owner. The restore command runs inside the Compose network so `POSTGRES_HOST=postgres` resolves to the disposable project database service, not to production.

### Migrate And Smoke

Run migrations against only the restored dry-run target:

```bash
SERVICEOPS_DATABASE_URL="postgresql+psycopg://serviceops:${POSTGRES_PASSWORD}@postgres:5432/${SERVICEOPS_RESTORE_DRILL_DB}" \
docker compose -p "$SERVICEOPS_RESTORE_DRILL_PROJECT" \
  -f docker-compose.production.yml run --rm api python -m serviceops_api.operations.migrate
```

Run smoke checks against the disposable stack or a private restore-drill API route. Do not reuse production DNS for the drill.

### Evidence To Capture

- Operator:
- Backup file:
- Backup timestamp:
- Checksum result:
- Backup age:
- Target host:
- Target database:
- Restore started at:
- Restore duration:
- Migration result:
- Smoke result:
- Abort conditions reviewed:
- Notes:

## Retention

Use `SERVICEOPS_BACKUP_RETENTION_DAYS` as the minimum local retention window. Host-level cleanup can delete backups older than that window only after confirming an off-host copy exists when required by operations policy.
