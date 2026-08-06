# VPS Deployment (GitHub Actions)

This is the **real, current deployment path** for SkillChain — a single
Ubuntu VPS, Docker Compose, nginx + Let's Encrypt, deployed automatically on
every push to `main`. It intentionally does not follow
[`01-devops-infra-operations.md`](01-devops-infra-operations.md), whose
Kubernetes/AWS/ECR content (and `backend/scripts/deploy/blue_green_deploy.sh`)
is an aspirational future-scale target explicitly documented as untested
against real infrastructure — nothing here contradicts that doc, it's a
different, smaller architecture for actually shipping today.

## 1. Architecture

One VPS runs everything via Docker Compose
(`infra/docker/docker-compose.prod.yml`): Postgres, Redis (cache + Channels
layer + Celery result backend), RabbitMQ (Celery broker), the Django API
(Daphne/ASGI, for websockets), a Celery worker, Celery beat, and the Next.js
frontend. Host-installed nginx (not containerized) terminates TLS and is the
only thing listening on 80/443; every app container binds to `127.0.0.1`
only or isn't published at all.

```
Internet ──443/80──> nginx (host) ──127.0.0.1:8000──> api (Daphne)
                                   └─127.0.0.1:3000──> frontend (Next.js)
                          api/worker/beat ──> postgres, redis, rabbitmq
                                              (compose-internal network only)
```

Images are built in GitHub Actions (not on the VPS — too heavy for a small
box) and pushed to GitHub Container Registry, tagged with the commit SHA.
The VPS only ever pulls and restarts containers.

## 2. One-time VPS setup

Do these once, in order, on a fresh Ubuntu 22.04/24.04 box.

1. **Provision the box** — copies Docker, ufw, fail2ban, nginx, certbot, and
   creates the `deploy` user and `/opt/skillchain` layout:
   ```
   scp infra/vps/provision.sh root@your-vps:/root/
   ssh root@your-vps 'bash /root/provision.sh'
   ```
2. **Add your SSH key** for the `deploy` user (`ssh-copy-id -i <key>.pub
   deploy@your-vps`), and confirm you can log in with it before doing
   anything else.
3. **Bootstrap the TLS certificate** — nginx can't start pointed at a cert
   that doesn't exist yet, so this is two phases:
   ```bash
   # phase 1: HTTP-only, just enough for the ACME challenge
   scp infra/nginx/http-bootstrap.conf deploy@your-vps:/tmp/
   ssh deploy@your-vps
   sudo mkdir -p /var/www/certbot
   sudo cp /tmp/http-bootstrap.conf /etc/nginx/sites-available/skillchain
   sudo ln -sf /etc/nginx/sites-available/skillchain /etc/nginx/sites-enabled/skillchain
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t && sudo systemctl reload nginx

   # obtain the cert (edit domains/email first) — one SAN cert covers both
   sudo certbot certonly --webroot -w /var/www/certbot \
     -d api.yourdomain.com -d app.yourdomain.com \
     --non-interactive --agree-tos -m ops@yourdomain.com --no-eff-email \
     --deploy-hook "systemctl reload nginx"

   # phase 2: swap in the real config (edit the two domain names in it first)
   exit  # back on your machine
   scp infra/nginx/skillchain.conf deploy@your-vps:/tmp/
   ssh deploy@your-vps
   sudo cp /tmp/skillchain.conf /etc/nginx/sites-available/skillchain
   sudo nginx -t && sudo systemctl reload nginx
   ```
   The `--deploy-hook` is what makes certbot's automatic renewal (its own
   systemd timer, installed with the package) actually take effect — without
   it, certs renew on disk but nginx keeps serving the stale one until
   manually reloaded.
4. **Create `/opt/skillchain/.env.prod`** from
   `infra/docker/.env.prod.example` and fill in every value — real generated
   secrets (`openssl rand -hex 24` for passwords, the `Fernet.generate_key()`
   one-liner in the file for `FIELD_ENCRYPTION_KEY`), and your real domains
   for `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS`. This
   file is never touched by GitHub Actions — it's the one thing on the VPS
   you manage by hand.
5. **Authenticate the VPS to GHCR** (one time; the pipeline never does this
   automatically):
   ```bash
   docker login ghcr.io -u <your-github-username>
   # password: a classic PAT with the read:packages scope
   ```
   This PAT is long-lived on the box with no rotation built into the
   pipeline — put a reminder somewhere to rotate it periodically.
6. **Add GitHub repo secrets/variables** — see §3 below.
7. **Turn on branch protection for `main`**: require the `Backend CI` and
   `Frontend CI` status checks, and disallow direct pushes. `deploy.yml`
   triggers on `push: [main]` directly rather than chaining off those
   workflows (chaining would deadlock — each CI workflow is path-filtered,
   so a backend-only change never triggers `Frontend CI` at all); branch
   protection is what actually guarantees only CI-passed code reaches `main`.
8. **(Optional) wire up nightly backups** — see §6.

From here, every push to `main` deploys automatically.

## 3. Required GitHub secrets / variables

| Name | Type | Purpose |
|---|---|---|
| `VPS_HOST` | secret | VPS IP/hostname |
| `VPS_USER` | secret | SSH user (`deploy`, from provisioning) |
| `VPS_SSH_KEY` | secret | Private key matching the key added in step 2 |
| `VPS_SSH_PORT` | secret (optional) | Defaults to `22` if unset |
| `NEXT_PUBLIC_API_BASE_URL` | variable | e.g. `https://api.yourdomain.com/api/v1` — inlined at frontend build time |
| `NEXT_PUBLIC_SITE_URL` | variable | e.g. `https://app.yourdomain.com` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | variable | Must match `GOOGLE_OAUTH_CLIENT_ID` in `.env.prod` — same OAuth client, checked from both ends |

`GITHUB_TOKEN` (registry push) is automatic — nothing to add for it. The
~40 backend app secrets (Stripe/Mpesa/Zoom/etc.) live only in `.env.prod` on
the VPS, never in GitHub — see step 4 above for why.

## 4. How a deploy actually runs

`.github/workflows/deploy.yml`, on push to `main`:
1. Builds and pushes `skillchain-backend`/`skillchain-frontend` images to
   GHCR, tagged with the commit SHA.
2. Copies the whole `infra/` tree to `/opt/skillchain/infra` on the VPS
   (always matches the repo at that commit — `.env.prod` and deploy state
   files live outside this tree, so they're never overwritten).
3. Runs `infra/vps/deploy.sh` over SSH, which: pulls the new images, brings
   up Postgres/Redis/RabbitMQ and waits for them to report healthy, runs
   migrations, runs `collectstatic`, recreates the api/worker/beat/frontend
   containers, then polls `/healthz/ready/` with backoff.
4. On success, records the tag in `.last_good_tag` and appends it to
   `.deploy_history`.
5. On a failed health check, **automatically redeploys the previous
   `.last_good_tag`** (one attempt) and still fails the Action either way,
   so a red run always means "look at this," whether or not the auto-revert
   itself worked.

## 5. Rollback

**Automatic** (§4 step 5) covers "this deploy never became healthy." For a
release that passed its health check at deploy time but broke later, use
`infra/vps/rollback.sh` by hand — it reads `.deploy_history` and lets you
pick an earlier tag to redeploy:
```bash
ssh deploy@your-vps
cd /opt/skillchain && ./infra/vps/rollback.sh
```

**Neither rollback path undoes a database migration.** They only revert
which application code is running — if a bad release shipped a
non-additive migration, rolling back the code alone can leave old code
running against new schema, which is often worse than the original failure.
There is no automated fix for this on a single-VPS setup; the real
mitigation is expand/contract migration discipline (add nullable/backfill in
one release, tighten/remove in a later one), not tooling. If a rollback
follows a schema change, check `python manage.py showmigrations` before
assuming the incident is resolved.

## 6. Backups

`infra/vps/backup_postgres.sh` does a nightly `pg_dump` + gzip into
`/opt/skillchain/backups`, pruning anything older than 14 days. Wire it up
once, on the VPS:
```bash
sudo crontab -e
# add:
0 3 * * * /opt/skillchain/infra/vps/backup_postgres.sh >> /var/log/skillchain-backup.log 2>&1
```

This is a minimum-viable mitigation, not the full DR story in
`01-devops-infra-operations.md` §5–6 (PITR/WAL archiving, cross-region
copies, a rehearsed restore). At minimum, copy backups offsite periodically
(`rsync`/`rclone` to another host or object storage) — a nightly dump that
only ever lives on the same disk as the database it's backing up doesn't
protect against the VPS itself being lost.

## 7. Known gaps, stated plainly

- **Not rehearsed against a real VPS** — this tooling has been written and
  reviewed against the actual repo, but (like the K8s scripts in
  `01-devops-infra-operations.md`) has no VPS credentials in this
  environment to run an end-to-end deploy against. A clean run through §2's
  checklist against a real box is the actual rehearsal.
- **Single VPS, no redundancy.** A box failure is downtime until a new one
  is provisioned and restored from backup — there is no standby.
- **GHCR PAT on the VPS has no automated rotation** (§2 step 5).
- **No offsite backup copy is built** (§6) — only documented as a follow-up.
