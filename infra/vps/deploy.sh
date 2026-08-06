#!/usr/bin/env bash
# Run remotely by .github/workflows/deploy.yml on every push to main — not
# meant to be run by hand except to reproduce/debug a deploy. Assumes
# infra/vps/provision.sh has already run and /opt/skillchain/.env.prod
# already exists (see docs/06-devops-security-qa/03-vps-deployment.md).
#
# Usage: IMAGE_TAG=<git-sha> ./deploy.sh
#
# On a failed post-deploy health check, automatically redeploys the last
# known-good image tag (single attempt, no retry loop) and still exits
# non-zero so the Action shows red either way. This rolls back application
# code only — it does NOT undo any migration the new code already ran, so a
# non-additive migration can leave old code running against new schema.
# There is no automated fix for that; write expand/contract migrations.
set -euo pipefail

APP_DIR="/opt/skillchain"
# The whole infra/ tree is scp'd fresh from the repo on every deploy run
# (see .github/workflows/deploy.yml) — .env.prod and the state files below
# deliberately live at APP_DIR's root, outside infra/, so they're never at
# risk of being overwritten by that.
COMPOSE_FILE="${APP_DIR}/infra/docker/docker-compose.prod.yml"
ENV_PROD="${APP_DIR}/.env.prod"
ENV_DEPLOY="${APP_DIR}/.env.deploy"
LAST_GOOD_TAG_FILE="${APP_DIR}/.last_good_tag"
# Append-only log of every tag that passed its post-deploy health check,
# oldest first — separate from LAST_GOOD_TAG_FILE because that file gets
# overwritten the moment *this* deploy passes, so it's useless for "this
# release passed health checks at deploy time but turned out bad three
# hours later" (infra/vps/rollback.sh needs to look further back than one
# entry for that case).
DEPLOY_HISTORY_FILE="${APP_DIR}/.deploy_history"
HEALTH_URL="http://127.0.0.1:8000/healthz/ready/"
HEALTH_RETRIES=15
HEALTH_INTERVAL=4

: "${IMAGE_TAG:?IMAGE_TAG must be set, e.g. IMAGE_TAG=$(git rev-parse HEAD) ./deploy.sh}"

if [[ ! -f "$ENV_PROD" ]]; then
    echo "ERROR: ${ENV_PROD} does not exist. Create it from" >&2
    echo "infra/docker/.env.prod.example before the first deploy (see the runbook)." >&2
    exit 1
fi

cd "$APP_DIR"

compose() {
    docker compose --env-file "$ENV_PROD" --env-file "$ENV_DEPLOY" -f "$COMPOSE_FILE" "$@"
}

write_tag() {
    echo "IMAGE_TAG=$1" > "$ENV_DEPLOY"
}

wait_healthy() {
    local attempt=1
    while (( attempt <= HEALTH_RETRIES )); do
        if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
            echo "    healthy after ${attempt} check(s)"
            return 0
        fi
        echo "    not healthy yet (attempt ${attempt}/${HEALTH_RETRIES})"
        sleep "$HEALTH_INTERVAL"
        (( attempt++ ))
    done
    return 1
}

deploy_tag() {
    local tag="$1"
    write_tag "$tag"
    echo "==> Pulling images for ${tag}"
    compose pull
    echo "==> Starting data services"
    compose up -d --wait postgres redis rabbitmq
    echo "==> Running migrations"
    compose run --rm api python manage.py migrate --noinput
    echo "==> Collecting static files"
    compose run --rm api python manage.py collectstatic --noinput
    echo "==> Recreating app services"
    compose up -d --remove-orphans --wait
}

echo "==> Deploying ${IMAGE_TAG}"
if deploy_tag "$IMAGE_TAG" && wait_healthy; then
    echo "==> ${IMAGE_TAG} is healthy"
    echo "$IMAGE_TAG" > "$LAST_GOOD_TAG_FILE"
    echo "$IMAGE_TAG" >> "$DEPLOY_HISTORY_FILE"
    exit 0
fi

echo "==> ${IMAGE_TAG} failed its post-deploy health check" >&2

if [[ ! -f "$LAST_GOOD_TAG_FILE" ]]; then
    echo "ERROR: no .last_good_tag on record (this looks like the first-ever" >&2
    echo "deploy) — nothing to roll back to. Investigate manually:" >&2
    echo "  docker compose -f ${COMPOSE_FILE} logs --tail=200 api" >&2
    exit 1
fi

PREVIOUS_TAG="$(cat "$LAST_GOOD_TAG_FILE")"
echo "==> Rolling back to previous known-good tag: ${PREVIOUS_TAG}" >&2
if deploy_tag "$PREVIOUS_TAG" && wait_healthy; then
    echo "==> Rollback to ${PREVIOUS_TAG} succeeded — ${IMAGE_TAG} was NOT deployed" >&2
else
    echo "ERROR: rollback to ${PREVIOUS_TAG} ALSO failed its health check." >&2
    echo "Investigate manually immediately:" >&2
    echo "  docker compose -f ${COMPOSE_FILE} logs --tail=200 api" >&2
fi

# Always non-zero: the push that triggered this run did not successfully
# deploy, whether or not the automatic rollback itself succeeded.
exit 1
