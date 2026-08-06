#!/usr/bin/env bash
# Nightly Postgres backup for the self-hosted VPS deploy. A single VPS
# running Postgres in Docker with no backup at all is one disk failure from
# total data loss — this is the minimum viable mitigation, not a full DR
# story (see docs/06-devops-security-qa/03-vps-deployment.md's "Backups"
# section for what's explicitly still missing: offsite/cross-region copies,
# PITR/WAL archiving, and restore rehearsal).
#
# Not run by any GitHub Actions workflow — wire it up on the VPS with cron:
#   sudo crontab -e
#   0 3 * * * /opt/skillchain/infra/vps/backup_postgres.sh >> /var/log/skillchain-backup.log 2>&1
set -euo pipefail

APP_DIR="/opt/skillchain"
COMPOSE_FILE="${APP_DIR}/infra/docker/docker-compose.prod.yml"
ENV_PROD="${APP_DIR}/.env.prod"
ENV_DEPLOY="${APP_DIR}/.env.deploy"
BACKUP_DIR="${APP_DIR}/backups"
RETENTION_DAYS=14

# shellcheck source=/dev/null
set -a && source "$ENV_PROD" && set +a

compose() {
    docker compose --env-file "$ENV_PROD" --env-file "$ENV_DEPLOY" -f "$COMPOSE_FILE" "$@"
}

TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
OUT_FILE="${BACKUP_DIR}/skillchain-${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"
echo "==> Dumping ${POSTGRES_DB} to ${OUT_FILE}"
compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT_FILE"

echo "==> Pruning backups older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -name 'skillchain-*.sql.gz' -mtime "+${RETENTION_DAYS}" -delete

echo "==> Done: $(du -h "$OUT_FILE" | cut -f1) written"
