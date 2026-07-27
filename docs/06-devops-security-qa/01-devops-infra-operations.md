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
