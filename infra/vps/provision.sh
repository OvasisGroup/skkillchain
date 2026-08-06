#!/usr/bin/env bash
# One-time provisioning for a fresh Ubuntu 22.04/24.04 VPS. Run once, by
# hand, over SSH as root (or a sudo-capable user):
#
#   scp infra/vps/provision.sh root@your-vps:/root/
#   ssh root@your-vps 'bash /root/provision.sh'
#
# Idempotent-ish (safe to re-run — apt/ufw/useradd calls below are all
# guarded), but it is NOT meant to run on every deploy: ongoing pushes to
# main only run infra/vps/deploy.sh, which assumes everything here already
# happened. See docs/06-devops-security-qa/03-vps-deployment.md for the full
# one-time setup checklist this script is one step of (cert bootstrap,
# .env.prod creation, and `docker login ghcr.io` all happen separately,
# after this).
set -euo pipefail

DEPLOY_USER="${DEPLOY_USER:-deploy}"
APP_DIR="/opt/skillchain"
# Must match backend/Dockerfile's pinned non-root UID/GID exactly — media
# and static are bind-mounted host directories, and the container writes to
# them as this UID.
APP_UID=10001

echo "==> apt update/upgrade"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

echo "==> Installing base packages"
apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg ufw fail2ban nginx certbot

echo "==> Installing Docker Engine + Compose plugin (official repo)"
if ! command -v docker >/dev/null 2>&1; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    # shellcheck source=/etc/os-release
    . /etc/os-release
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y --no-install-recommends \
        docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    echo "    docker already installed, skipping"
fi
systemctl enable --now docker

echo "==> Creating deploy user"
if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash "$DEPLOY_USER"
    echo "    Created user '$DEPLOY_USER' with no password set — add its SSH"
    echo "    key next: ssh-copy-id -i <your-key>.pub $DEPLOY_USER@this-host"
else
    echo "    user '$DEPLOY_USER' already exists, skipping"
fi
usermod -aG docker "$DEPLOY_USER"

echo "==> Firewall (ufw): allow SSH, HTTP, HTTPS only"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> fail2ban (protects sshd against brute-force)"
systemctl enable --now fail2ban

echo "==> Creating ${APP_DIR} layout"
mkdir -p "${APP_DIR}/data/media" "${APP_DIR}/data/static" "${APP_DIR}/backups"
mkdir -p /var/www/certbot
chown -R "${APP_UID}:${APP_UID}" "${APP_DIR}/data/media" "${APP_DIR}/data/static"
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}/backups"
chown "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}"

cat <<'EOF'

==> Provisioning complete. Remaining steps are manual — see
    docs/06-devops-security-qa/03-vps-deployment.md:

  1. Add your SSH public key for the deploy user if you haven't already.
  2. Install infra/nginx/http-bootstrap.conf, obtain a cert with certbot,
     then swap in infra/nginx/skillchain.conf (the runbook has both
     commands verbatim).
  3. Copy infra/docker/.env.prod.example to /opt/skillchain/.env.prod and
     fill in real values.
  4. docker login ghcr.io on this box (a GitHub PAT with read:packages).
  5. Add VPS_HOST / VPS_USER / VPS_SSH_KEY as GitHub Actions secrets on
     the repo, pointed at this box and the deploy user created above.

EOF

# --- Optional hardening: disable SSH password auth --------------------
# NOT applied automatically — this WILL lock you out if key-based access
# for the deploy user (or root) isn't already confirmed working. Only run
# this block by hand, after verifying you can SSH in with a key:
#
#   sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
#   systemctl reload sshd
