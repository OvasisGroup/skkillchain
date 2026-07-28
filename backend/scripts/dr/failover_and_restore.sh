#!/usr/bin/env bash
#
# Disaster recovery runbook — scripted steps for
# docs/06-devops-security-qa/01-devops-infra-operations.md §6.
#
# REAL SCRIPT, NOT YET RUN AGAINST REAL INFRASTRUCTURE: this codifies the
# runbook as executable steps using the AWS CLI. It has not been executed
# against a real AWS account in this environment — doing so requires this
# repo's actual resource IDs (hosted zone, ALB, DB instance identifiers) and
# AWS credentials with the relevant permissions, none of which exist here.
# Treat a clean run of this script as the actual DR drill; nothing below
# should be reported as "passed" until someone with that access runs it.
#
# Usage:
#   AWS_REGION=... HOSTED_ZONE_ID=... DNS_RECORD_NAME=... \
#   STANDBY_ALB_DNS_NAME=... DB_INSTANCE_IDENTIFIER=... \
#   RESTORE_TARGET_TIME=2026-07-28T00:00:00Z \
#   ./scripts/dr/failover_and_restore.sh

set -euo pipefail

: "${AWS_REGION:?Set AWS_REGION (e.g. us-east-1)}"
: "${HOSTED_ZONE_ID:?Set HOSTED_ZONE_ID for Route53 failover}"
: "${DNS_RECORD_NAME:?Set DNS_RECORD_NAME, e.g. api.skillchain.example.com}"
: "${STANDBY_ALB_DNS_NAME:?Set STANDBY_ALB_DNS_NAME (warm standby region ALB)}"
: "${DB_INSTANCE_IDENTIFIER:?Set DB_INSTANCE_IDENTIFIER for the RDS restore}"
: "${RESTORE_TARGET_TIME:?Set RESTORE_TARGET_TIME (ISO-8601 UTC) or 'latest'}"

RESTORED_DB_INSTANCE_IDENTIFIER="${DB_INSTANCE_IDENTIFIER}-dr-restore-$(date +%Y%m%d%H%M%S)"

echo "== Step 1: Failover DNS/ALB routing to the warm standby region =="
change_batch=$(cat <<JSON
{
  "Comment": "DR failover to warm standby",
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "${DNS_RECORD_NAME}",
      "Type": "CNAME",
      "TTL": 60,
      "ResourceRecords": [{"Value": "${STANDBY_ALB_DNS_NAME}"}]
    }
  }]
}
JSON
)
aws route53 change-resource-record-sets \
  --hosted-zone-id "${HOSTED_ZONE_ID}" \
  --change-batch "${change_batch}"

echo "== Step 2: Restore RDS to the latest restorable point (or RESTORE_TARGET_TIME) =="
if [ "${RESTORE_TARGET_TIME}" = "latest" ]; then
  aws rds restore-db-instance-to-point-in-time \
    --region "${AWS_REGION}" \
    --source-db-instance-identifier "${DB_INSTANCE_IDENTIFIER}" \
    --target-db-instance-identifier "${RESTORED_DB_INSTANCE_IDENTIFIER}" \
    --use-latest-restorable-time
else
  aws rds restore-db-instance-to-point-in-time \
    --region "${AWS_REGION}" \
    --source-db-instance-identifier "${DB_INSTANCE_IDENTIFIER}" \
    --target-db-instance-identifier "${RESTORED_DB_INSTANCE_IDENTIFIER}" \
    --restore-time "${RESTORE_TARGET_TIME}"
fi

echo "Waiting for restored instance ${RESTORED_DB_INSTANCE_IDENTIFIER} to become available..."
aws rds wait db-instance-available \
  --region "${AWS_REGION}" \
  --db-instance-identifier "${RESTORED_DB_INSTANCE_IDENTIFIER}"

echo "== Step 3: Rehydrate queues and replay idempotent events =="
echo "Point DATABASE_URL/CELERY_BROKER_URL at the restored instance, then:"
echo "  - Redeploy worker/beat pods so they pick up the restored DB."
echo "  - Celery task handlers in this codebase (payment webhooks, payout"
echo "    processing, notification dispatch) are written to be re-runnable"
echo "    against the same input without double-effect; replay any queued"
echo "    or dead-lettered messages from the broker's DLQ once workers are"
echo "    back up."

echo "== Step 4: Verify payment reconciliation integrity =="
echo "Run against the restored database:"
echo "  python manage.py verify_payment_reconciliation"
echo "This is the one step in this runbook that is fully real and already"
echo "tested (backend/apps/commerce/management/commands/"
echo "verify_payment_reconciliation.py) — it does not require this script."

echo "DR failover + restore steps complete. Confirm RTO/RPO targets (2h / 15m,"
echo "per §6) were met before declaring the drill closed."
