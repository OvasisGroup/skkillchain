#!/usr/bin/env bash
#
# Blue/green deploy with a 5% -> 25% -> 100% canary ramp, per
# docs/06-devops-security-qa/01-devops-infra-operations.md §7 (Production
# Deployment Guide) and §3 (Kubernetes Deployment).
#
# REAL SCRIPT, NOT YET RUN AGAINST REAL INFRASTRUCTURE: this is genuine,
# runnable kubectl automation, but no Kubernetes manifests exist in this
# repo yet (docs/06-devops-security-qa §3 is the target design; only
# backend/Dockerfile and infra/docker/docker-compose.yml exist today for
# local dev). Running this for real needs an actual cluster with an `api`
# Deployment + Service already in place, matching the label/selector
# convention assumed below. Treat a clean run of this script — not this
# commit — as the actual blue/green rehearsal; nothing here should be
# read as "deployed" until someone with real cluster access runs it.
#
# Traffic-split mechanism: two Deployments ("stable" and "canary") share
# one Service via a common `app: api` label, so kube-proxy round-robins
# across every ready pod matching that selector regardless of which
# Deployment owns it. The canary's share of traffic is approximated by
# its share of total ready replicas — canary_replicas / (canary_replicas
# + stable_replicas) — which is what the 5/25/100 ramp actually adjusts.
# This needs no service mesh or extra controller (Argo Rollouts / Flagger
# would give exact percentage-based splitting instead of a replica-count
# approximation, at the cost of an extra dependency this cluster may not
# have yet).
#
# Usage:
#   NAMESPACE=skillchain SERVICE_URL=https://api.skillchain.internal \
#   TOTAL_REPLICAS=20 \
#   ./scripts/deploy/blue_green_deploy.sh <new-image-tag>

set -euo pipefail

NEW_IMAGE_TAG="${1:?Usage: $0 <new-image-tag>}"
NAMESPACE="${NAMESPACE:-skillchain}"
DEPLOYMENT_STABLE="${DEPLOYMENT_STABLE:-api-stable}"
DEPLOYMENT_CANARY="${DEPLOYMENT_CANARY:-api-canary}"
IMAGE_REPOSITORY="${IMAGE_REPOSITORY:?Set IMAGE_REPOSITORY, e.g. <account>.dkr.ecr.<region>.amazonaws.com/skillchain-api}"
TOTAL_REPLICAS="${TOTAL_REPLICAS:-20}"
SERVICE_URL="${SERVICE_URL:?Set SERVICE_URL to the health-check endpoint behind the shared Service, e.g. https://api.skillchain.internal}"
BAKE_SECONDS="${BAKE_SECONDS:-120}"
HEALTH_CHECK_PATH="${HEALTH_CHECK_PATH:-/healthz/live/}"
HEALTH_CHECK_FAILURES_ALLOWED="${HEALTH_CHECK_FAILURES_ALLOWED:-2}"

NEW_IMAGE="${IMAGE_REPOSITORY}:${NEW_IMAGE_TAG}"

log() { echo "[blue-green] $(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

rollback() {
  log "ROLLING BACK: scaling ${DEPLOYMENT_CANARY} to 0, ${DEPLOYMENT_STABLE} to ${TOTAL_REPLICAS}"
  kubectl -n "${NAMESPACE}" scale "deployment/${DEPLOYMENT_CANARY}" --replicas=0 || true
  kubectl -n "${NAMESPACE}" scale "deployment/${DEPLOYMENT_STABLE}" --replicas="${TOTAL_REPLICAS}" || true
  log "Rollback complete. ${DEPLOYMENT_STABLE} is serving 100% of traffic on the previous image."
  exit 1
}

# Real-time metric watch and rollback trigger: polls the health endpoint
# repeatedly during the bake period. A real deployment should also watch
# error-rate/latency dashboards (Prometheus/CloudWatch per §4 Monitoring
# Strategy) — that wiring depends on which metrics backend the cluster
# actually has, which isn't provisioned here, so this script's own gate
# is deliberately narrower (available + responding) rather than fabricating
# a metrics integration this sandbox can't verify.
bake_and_watch() {
  local stage_name="$1"
  log "Baking ${stage_name} for ${BAKE_SECONDS}s, watching ${SERVICE_URL}${HEALTH_CHECK_PATH}"
  local failures=0
  local elapsed=0
  local interval=10
  while [ "${elapsed}" -lt "${BAKE_SECONDS}" ]; do
    if ! curl -fsS --max-time 5 "${SERVICE_URL}${HEALTH_CHECK_PATH}" > /dev/null; then
      failures=$((failures + 1))
      log "Health check failed (${failures}/${HEALTH_CHECK_FAILURES_ALLOWED} allowed)"
      if [ "${failures}" -gt "${HEALTH_CHECK_FAILURES_ALLOWED}" ]; then
        log "Too many health-check failures during ${stage_name} — aborting."
        rollback
      fi
    fi
    sleep "${interval}"
    elapsed=$((elapsed + interval))
  done
  log "${stage_name} bake period completed cleanly."
}

canary_replicas_for_percent() {
  local percent="$1"
  # Round to nearest whole replica; minimum 1 so a real canary pod exists
  # at any nonzero percentage.
  python3 -c "
import math
total = ${TOTAL_REPLICAS}
percent = ${percent}
print(max(1, round(total * percent / 100)))
"
}

log "Pre-deploy checks"
kubectl -n "${NAMESPACE}" get deployment "${DEPLOYMENT_STABLE}" > /dev/null
log "Applying database migrations (lock-step job, must complete before any canary traffic)"
kubectl -n "${NAMESPACE}" run "migrate-${NEW_IMAGE_TAG}" \
  --image="${NEW_IMAGE}" \
  --restart=Never \
  --command -- python manage.py migrate --noinput
kubectl -n "${NAMESPACE}" wait --for=condition=complete --timeout=600s \
  "job/migrate-${NEW_IMAGE_TAG}" || {
    log "Migration job failed — aborting before any canary traffic is shifted."
    exit 1
  }

log "Deploying ${NEW_IMAGE} to ${DEPLOYMENT_CANARY} (0 replicas initially)"
kubectl -n "${NAMESPACE}" set image "deployment/${DEPLOYMENT_CANARY}" "api=${NEW_IMAGE}"
kubectl -n "${NAMESPACE}" scale "deployment/${DEPLOYMENT_CANARY}" --replicas=0
kubectl -n "${NAMESPACE}" rollout status "deployment/${DEPLOYMENT_CANARY}" --timeout=300s

for percent in 5 25 100; do
  canary_replicas="$(canary_replicas_for_percent "${percent}")"
  stable_replicas=$((TOTAL_REPLICAS - canary_replicas))
  if [ "${percent}" -eq 100 ]; then
    stable_replicas=0
  fi

  log "== Canary stage: ${percent}% (canary=${canary_replicas}, stable=${stable_replicas}) =="
  kubectl -n "${NAMESPACE}" scale "deployment/${DEPLOYMENT_CANARY}" --replicas="${canary_replicas}"
  kubectl -n "${NAMESPACE}" rollout status "deployment/${DEPLOYMENT_CANARY}" --timeout=300s
  kubectl -n "${NAMESPACE}" scale "deployment/${DEPLOYMENT_STABLE}" --replicas="${stable_replicas}"

  bake_and_watch "${percent}% canary"
done

log "Canary reached 100% cleanly. ${DEPLOYMENT_CANARY} (${NEW_IMAGE}) is now serving all traffic."
log "Post-deploy: run the smoke suite and business-transaction probes before closing out the release."
log "${DEPLOYMENT_STABLE} is scaled to 0 but not deleted — it becomes the rollback target for the next release."
