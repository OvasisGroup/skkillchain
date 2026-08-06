#!/usr/bin/env bash
# Manual rollback for the case infra/vps/deploy.sh's own auto-rollback
# doesn't cover: a deploy that passed its post-deploy health check (so
# .last_good_tag already got overwritten to it) but turned out broken
# later. Run by hand over SSH — this is not called by any GitHub Actions
# workflow.
#
# Usage:
#   ./rollback.sh              interactive: lists recent releases, prompts
#   ./rollback.sh <image-tag>  non-interactive: redeploys that exact tag
#
# Like deploy.sh's auto-rollback, this only reverts application code — it
# does NOT undo any migration a bad release already ran. Check
# `python manage.py showmigrations` before assuming a rollback alone fixes
# a schema-related incident.
set -euo pipefail

APP_DIR="/opt/skillchain"
COMPOSE_FILE="${APP_DIR}/infra/docker/docker-compose.prod.yml"
ENV_PROD="${APP_DIR}/.env.prod"
ENV_DEPLOY="${APP_DIR}/.env.deploy"
DEPLOY_HISTORY_FILE="${APP_DIR}/.deploy_history"

cd "$APP_DIR"

compose() {
    docker compose --env-file "$ENV_PROD" --env-file "$ENV_DEPLOY" -f "$COMPOSE_FILE" "$@"
}

TARGET_TAG="${1:-}"

if [[ -z "$TARGET_TAG" ]]; then
    if [[ ! -f "$DEPLOY_HISTORY_FILE" ]]; then
        echo "ERROR: no ${DEPLOY_HISTORY_FILE} on record — nothing to roll back to." >&2
        exit 1
    fi
    echo "Recent releases (oldest to newest):"
    tail -n 10 "$DEPLOY_HISTORY_FILE" | nl -ba
    echo
    read -rp "Tag to redeploy: " TARGET_TAG
fi

if [[ -z "$TARGET_TAG" ]]; then
    echo "ERROR: no tag given." >&2
    exit 1
fi

read -rp "Redeploy ${TARGET_TAG}? This restarts api/worker/beat/frontend. [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Aborted."
    exit 1
fi

echo "IMAGE_TAG=${TARGET_TAG}" > "$ENV_DEPLOY"
echo "==> Pulling ${TARGET_TAG}"
compose pull
echo "==> Recreating app services on ${TARGET_TAG}"
compose up -d --remove-orphans --wait

echo "==> Rolled back to ${TARGET_TAG}. Verify with:"
echo "    curl -sf http://127.0.0.1:8000/healthz/ready/"

echo "$TARGET_TAG" > "${APP_DIR}/.last_good_tag"
echo "$TARGET_TAG" >> "$DEPLOY_HISTORY_FILE"
