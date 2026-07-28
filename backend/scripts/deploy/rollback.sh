#!/usr/bin/env bash
#
# Standalone rollback: reverts to the previous release after a bad
# deploy has already reached 100% canary (for a rollback *during* the
# canary ramp itself, blue_green_deploy.sh's own rollback() fires
# automatically on health-check failure — this script is for "we
# shipped, then found a problem later").
#
# REAL SCRIPT, NOT YET RUN AGAINST REAL INFRASTRUCTURE — see the header
# comment in blue_green_deploy.sh for why (no cluster exists to run it
# against from this sandbox).
#
# Assumes blue_green_deploy.sh's convention: DEPLOYMENT_STABLE still
# exists (scaled to 0, not deleted) holding the previous release's image,
# and DEPLOYMENT_CANARY is the current release serving 100% of traffic.
# Swaps which one is scaled up; does not touch either Deployment's image,
# so this is a pure traffic revert, not a redeploy of old code from
# scratch (faster, and correct as long as DEPLOYMENT_STABLE was never
# scaled to 0 replicas *and* deleted since the last successful deploy).
#
# Usage:
#   NAMESPACE=skillchain TOTAL_REPLICAS=20 ./scripts/deploy/rollback.sh

set -euo pipefail

NAMESPACE="${NAMESPACE:-skillchain}"
DEPLOYMENT_STABLE="${DEPLOYMENT_STABLE:-api-stable}"
DEPLOYMENT_CANARY="${DEPLOYMENT_CANARY:-api-canary}"
TOTAL_REPLICAS="${TOTAL_REPLICAS:-20}"

log() { echo "[rollback] $(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

stable_image="$(kubectl -n "${NAMESPACE}" get "deployment/${DEPLOYMENT_STABLE}" \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="api")].image}')"
canary_image="$(kubectl -n "${NAMESPACE}" get "deployment/${DEPLOYMENT_CANARY}" \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="api")].image}')"

echo "About to roll back:"
echo "  ${DEPLOYMENT_CANARY} (currently live, image=${canary_image}) -> scale to 0"
echo "  ${DEPLOYMENT_STABLE} (previous release, image=${stable_image}) -> scale to ${TOTAL_REPLICAS}"
read -r -p "Proceed? [y/N] " confirm
if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ]; then
  echo "Aborted."
  exit 1
fi

log "Scaling ${DEPLOYMENT_STABLE} back up to ${TOTAL_REPLICAS}"
kubectl -n "${NAMESPACE}" scale "deployment/${DEPLOYMENT_STABLE}" --replicas="${TOTAL_REPLICAS}"
kubectl -n "${NAMESPACE}" rollout status "deployment/${DEPLOYMENT_STABLE}" --timeout=300s

log "Scaling ${DEPLOYMENT_CANARY} down to 0"
kubectl -n "${NAMESPACE}" scale "deployment/${DEPLOYMENT_CANARY}" --replicas=0

log "Rollback complete. ${DEPLOYMENT_STABLE} (${stable_image}) is serving 100% of traffic."
log "Investigate ${canary_image} before attempting to redeploy it."
