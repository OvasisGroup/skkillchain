# Blue/green deploy + rollback

Implements docs/06-devops-security-qa/01-devops-infra-operations.md §7
(Production Deployment Guide)'s canary 5% -> 25% -> 100% rollout, on top
of the two-Deployment / one-Service convention described in §3
(Kubernetes Deployment).

**Neither script has been run against a real cluster.** No Kubernetes
manifests exist in this repo yet (only `backend/Dockerfile` and
`infra/docker/docker-compose.yml` for local dev) — §3 is the target
design these scripts implement toward, the same way the OpenAPI spec was
"aspirational" until the routes existed. Running `blue_green_deploy.sh`
for real needs an actual cluster with `api-stable` / `api-canary`
Deployments and a shared Service already provisioned, matching the
`app: api` label convention the scripts assume. Treat a clean run there
as the actual rehearsal — this commit is the tooling, not the rehearsal.

- `blue_green_deploy.sh <image-tag>` — runs the migration job, then ramps
  `api-canary` through 5% / 25% / 100% of total replicas (approximated by
  replica-count ratio against `api-stable`, since no service mesh /
  Argo Rollouts is assumed), baking and health-checking at each stage,
  auto-rolling-back on repeated health-check failure.
- `rollback.sh` — reverts to the previous release after a bad deploy
  already reached 100% (interactive confirmation, no image rebuild —
  just swaps which Deployment is scaled up).

Both are parameterized via env vars (`NAMESPACE`, `DEPLOYMENT_STABLE`,
`DEPLOYMENT_CANARY`, `TOTAL_REPLICAS`, ...) — see each script's header
comment for the full list and defaults.
