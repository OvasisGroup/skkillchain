# DevOps, Infrastructure, and Operations

## 1. CI/CD Pipeline (GitHub Actions)

### Branch Strategy
- `main`: production
- `release/*`: staged release hardening
- `develop`: integration
- feature branches with mandatory PR checks

### Pipeline Stages
1. Lint and static checks (Python, JS/TS, Dart).
2. Unit + integration tests.
3. Security scans (SAST, dependency, secret scan).
4. Build Docker images with immutable tags.
5. Push images to ECR.
6. Deploy to staging (Helm/Kustomize).
7. Run smoke + API contract tests.
8. Manual approval gate for production.
9. Blue/green deployment to production.

## 2. Docker Configuration
- Multi-stage image for Django app (builder/runtime separation).
- Separate images for `api`, `worker`, `beat`, `websocket` roles.
- Non-root container runtime, read-only root FS where possible.
- Health checks for readiness/liveness endpoints.

## 3. Kubernetes Deployment
- Workloads:
  - `deployment/api`
  - `deployment/ws`
  - `deployment/worker`
  - `deployment/beat`
- Config:
  - ConfigMaps for non-secrets.
  - Secrets from AWS Secrets Manager via CSI.
- Scaling:
  - HPA by CPU and custom queue depth metric.
- Resilience:
  - PodDisruptionBudgets and anti-affinity rules.
  - Multi-AZ node groups.

## 4. Monitoring Strategy
- SLIs:
  - API success rate and latency percentiles.
  - Enrollment/payment success ratio.
  - Queue lag and worker success/failure ratio.
  - Playback start success and rebuffer rates.
- SLO alerts with burn-rate policies.
- Synthetic checks for login, checkout, playback, and certificate verification.

## 5. Backup Strategy
- PostgreSQL:
  - Daily snapshots + PITR with WAL archiving.
  - Cross-region snapshot copy.
- Redis:
  - Snapshot policy for persistent cache use cases.
- S3:
  - Versioning + lifecycle + object lock for critical artifacts.
- OpenSearch:
  - Daily snapshots to S3.

## 6. Disaster Recovery Plan
- RTO: 2 hours for platform core.
- RPO: 15 minutes for transactional data.
- DR topology: warm standby region.
- DR runbooks:
  - Failover DNS and ALB routing.
  - Restore RDS from latest restorable point.
  - Rehydrate queues and replay idempotent events.
  - Verify payment reconciliation integrity.

### Scripted runbook

`backend/scripts/dr/failover_and_restore.sh` codifies the four steps above
as executable AWS CLI commands (Route53 failover, `aws rds
restore-db-instance-to-point-in-time`, a worker-redeploy/replay checklist,
and the reconciliation check). It is real, working shell — parameterized by
env vars (`HOSTED_ZONE_ID`, `DB_INSTANCE_IDENTIFIER`, etc.) — but has **not
been run against real AWS infrastructure**: doing so needs this project's
actual resource IDs and AWS credentials, which don't exist in this
environment. Running it for real, end to end against a warm-standby account,
is the actual DR drill; nothing here should be read as a completed drill
until that happens.

The one step that *is* fully real, tested, and runnable today, independent
of any AWS access, is the last one:

```
python manage.py verify_payment_reconciliation
```

(`backend/apps/commerce/management/commands/verify_payment_reconciliation.py`,
covered by `backend/tests/unit/test_payment_reconciliation_command.py`). It
checks that every `paid` `Order` has a `succeeded` `Payment` whose total
covers the order total, and that no `succeeded` `Payment` points at an
order that isn't `paid` — exactly the kind of ledger corruption a botched
restore or replay would produce. Run it against any restored database
before resuming traffic, not only during a real DR event.

### Encryption / KMS status

`shared/crypto.py` (Fernet symmetric encryption) is used for the two fields
that need encryption at rest today: `MFAFactor.secret_encrypted` and
`ConferencingAccount.*_token_encrypted`. Both round-trip correctly — see
`backend/tests/unit/test_crypto.py` (encrypt/decrypt round trip, ciphertext
non-determinism, and rejection of tampered/garbage ciphertext). No other
field needs it: `OAuthIdentity` stores no token, `PaymentMethod` is
gateway-tokenized, and `Payout` has no bank fields yet.

`FIELD_ENCRYPTION_KEY` is read from the environment in staging/production
with no default (`config/settings/stage.py`, `config/settings/prod.py`) —
dev supplies a fixed dev-only fallback (`config/settings/dev.py`) so tests
don't need real secrets. Backing that environment variable with a key
actually managed by AWS KMS (rotation, access policy, audit trail) is an
ops/deploy-time task performed when provisioning each environment's
secrets — it is not application code and there is nothing further to build
here.

## 7. Production Deployment Guide
- Pre-deploy checks:
  - All quality gates green.
  - Migration dry run in staging.
  - Capacity headroom > 30%.
- Deploy steps:
  - Apply migrations with lock-step job.
  - Blue/green rollout with canary 5% -> 25% -> 100%.
  - Real-time metric watch and rollback trigger thresholds.
- Post-deploy:
  - Smoke suite and business transaction probes.
  - Audit release notes and incident watch window.

### Scripted rollout and rollback

`backend/scripts/deploy/blue_green_deploy.sh` and `rollback.sh` (see
`backend/scripts/deploy/README.md`) implement the deploy-steps bullets
above as real kubectl automation: a lock-step migration job, then a
5%/25%/100% canary ramp between two Deployments sharing one Service,
health-checked and auto-rolled-back at each stage. **Not yet run against
real infrastructure** — no Kubernetes manifests exist in this repo yet
(§3 above is the target design), so there is no cluster to run it
against from this sandbox. Running it for real, against a provisioned
`api-stable`/`api-canary` pair, is the actual rehearsal.
