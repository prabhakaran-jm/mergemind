#!/usr/bin/env bash
set -euo pipefail

# -------- arguments --------
HOST=""
TLS_MODE="letsencrypt"  # or "selfsigned"
LE_EMAIL=""
RUNNER_REGISTER="false"
RUNNER_TOKEN=""
RUNNER_TAGS="demo"
RUNNER_UNTAGGED="true"
ENABLE_GCS_BACKUP="true"
GCS_BUCKET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --tls) TLS_MODE="$2"; shift 2 ;;
    --email) LE_EMAIL="$2"; shift 2 ;;
    --runner-register) RUNNER_REGISTER="$2"; shift 2 ;;
    --runner-token) RUNNER_TOKEN="$2"; shift 2 ;;
    --runner-tags) RUNNER_TAGS="$2"; shift 2 ;;
    --runner-untagged) RUNNER_UNTAGGED="$2"; shift 2 ;;
    --enable-gcs-backup) ENABLE_GCS_BACKUP="$2"; shift 2 ;;
    --gcs-bucket) GCS_BUCKET="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "${HOST}" ]]; then
  echo "Usage: $0 --host <gitlab.domain> [--tls letsencrypt|selfsigned] [--email you@example.com] [--runner-register true|false] [--runner-token TOKEN] [--enable-gcs-backup true|false]"
  exit 1
fi

if [[ "${TLS_MODE}" == "letsencrypt" && -z "${LE_EMAIL}" ]]; then
  echo "For Let's Encrypt, provide --email you@example.com"
  exit 1
fi

echo "==> Bootstrap GitLab CE"
echo "    Host: ${HOST}"
echo "    TLS : ${TLS_MODE}"
echo "    Runner: ${RUNNER_REGISTER}"
echo "    GCS Backup: ${ENABLE_GCS_BACKUP}"

# -------- 1) OS prep --------
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y upgrade
apt-get -y install curl ca-certificates tzdata jq apt-transport-https gnupg lsb-release

# -------- 2) Mount data disk (/dev/sdb -> /mnt/gitlab-data) --------
DATA_DEV="/dev/sdb"
MNT="/mnt/gitlab-data"
if ! lsblk | grep -q "$(basename ${DATA_DEV})"; then
  echo "ERROR: ${DATA_DEV} not found. Check attached disk."
  exit 1
fi

mkdir -p "${MNT}"
if ! blkid "${DATA_DEV}" >/dev/null 2>&1; then
  echo "Formatting ${DATA_DEV} as ext4..."
  mkfs.ext4 -F "${DATA_DEV}"
fi

if ! grep -q "${DATA_DEV} " /etc/fstab; then
  echo "${DATA_DEV} ${MNT} ext4 defaults,nofail 0 2" >> /etc/fstab
fi

mount -a

# Create data/logs dirs
mkdir -p "${MNT}/var_opt_gitlab" "${MNT}/var_log_gitlab"

# -------- 3) Add 4G swap (idempotent) --------
if ! swapon --show | grep -q "/swapfile"; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# -------- 4) Install GitLab CE (start with HTTP) --------
if ! command -v gitlab-ctl >/dev/null 2>&1; then
  curl -fsSL https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | bash
  EXTERNAL_URL="http://${HOST}" apt-get install -y gitlab-ce
else
  echo "GitLab CE already installed; skipping."
fi

# -------- 5) Move /var/opt/gitlab and /var/log/gitlab to data disk (bind mounts) --------
gitlab-ctl stop || true

if ! mount | grep -q " on /var/opt/gitlab "; then
  rsync -aHAX /var/opt/gitlab/ "${MNT}/var_opt_gitlab/"
  mv /var/opt/gitlab /var/opt/gitlab.bak || true
  mkdir -p /var/opt/gitlab
  echo "${MNT}/var_opt_gitlab /var/opt/gitlab none bind 0 0" >> /etc/fstab
  mount -a
fi

if ! mount | grep -q " on /var/log/gitlab "; then
  rsync -aHAX /var/log/gitlab/ "${MNT}/var_log_gitlab/"
  mv /var/log/gitlab /var/log/gitlab.bak || true
  mkdir -p /var/log/gitlab
  echo "${MNT}/var_log_gitlab /var/log/gitlab none bind 0 0" >> /etc/fstab
  mount -a
fi

# -------- 6) Configure HTTPS --------
GITLAB_RB="/etc/gitlab/gitlab.rb"

# Ensure external_url is https
if grep -q "^external_url" "${GITLAB_RB}"; then
  sed -i "s|^external_url .*|external_url 'https://${HOST}'|" "${GITLAB_RB}"
else
  echo "external_url 'https://${HOST}'" >> "${GITLAB_RB}"
fi

if [[ "${TLS_MODE}" == "letsencrypt" ]]; then
  # Append/ensure Let's Encrypt settings
  if ! grep -q "letsencrypt\['enable'\]" "${GITLAB_RB}"; then
    cat <<EOF >> "${GITLAB_RB}"

letsencrypt['enable'] = true
letsencrypt['contact_emails'] = ['${LE_EMAIL}']
letsencrypt['auto_renew'] = true
nginx['redirect_http_to_https'] = true
EOF
  else
    sed -i "s|letsencrypt\['enable'\].*|letsencrypt['enable'] = true|" "${GITLAB_RB}"
    sed -i "s|letsencrypt\['contact_emails'\].*|letsencrypt['contact_emails'] = ['${LE_EMAIL}']|" "${GITLAB_RB}"
    sed -i "s|nginx\['redirect_http_to_https'\].*|nginx['redirect_http_to_https'] = true|" "${GITLAB_RB}"
  fi

elif [[ "${TLS_MODE}" == "selfsigned" ]]; then
  mkdir -p /etc/gitlab/ssl
  chmod 755 /etc/gitlab/ssl
  if [[ ! -f /etc/gitlab/ssl/gitlab.key || ! -f /etc/gitlab/ssl/gitlab.crt ]]; then
    openssl req -newkey rsa:2048 -nodes -keyout /etc/gitlab/ssl/gitlab.key \
      -x509 -days 365 -out /etc/gitlab/ssl/gitlab.crt -subj "/CN=${HOST}"
  fi
  # Disable LE, point nginx to self-signed cert
  if grep -q "letsencrypt\['enable'\]" "${GITLAB_RB}"; then
    sed -i "s|letsencrypt\['enable'\].*|letsencrypt['enable'] = false|" "${GITLAB_RB}"
  else
    echo "letsencrypt['enable'] = false" >> "${GITLAB_RB}"
  fi
  if grep -q "nginx\['redirect_http_to_https'\]" "${GITLAB_RB}"; then
    sed -i "s|nginx\['redirect_http_to_https'\].*|nginx['redirect_http_to_https'] = true|" "${GITLAB_RB}"
  else
    echo "nginx['redirect_http_to_https'] = true" >> "${GITLAB_RB}"
  fi
  if grep -q "nginx\['ssl_certificate'\]" "${GITLAB_RB}"; then
    sed -i "s|nginx\['ssl_certificate'\].*|nginx['ssl_certificate'] = \"/etc/gitlab/ssl/gitlab.crt\"|" "${GITLAB_RB}"
  else
    echo "nginx['ssl_certificate'] = \"/etc/gitlab/ssl/gitlab.crt\"" >> "${GITLAB_RB}"
  fi
  if grep -q "nginx\['ssl_certificate_key'\]" "${GITLAB_RB}"; then
    sed -i "s|nginx\['ssl_certificate_key'\].*|nginx['ssl_certificate_key'] = \"/etc/gitlab/ssl/gitlab.key\"|" "${GITLAB_RB}"
  else
    echo "nginx['ssl_certificate_key'] = \"/etc/gitlab/ssl/gitlab.key\"" >> "${GITLAB_RB}"
  fi
else
  echo "Unknown TLS mode: ${TLS_MODE}"; exit 1
fi

gitlab-ctl reconfigure
gitlab-ctl restart

# -------- (optional) GitLab Runner: shell executor --------
if [[ "${RUNNER_REGISTER}" == "true" ]]; then
  if ! command -v gitlab-runner >/dev/null 2>&1; then
    echo "Installing GitLab Runner..."
    curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
    chmod +x /usr/local/bin/gitlab-runner
    id -u gitlab-runner >/dev/null 2>&1 || useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
    gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
    systemctl enable gitlab-runner
    systemctl start gitlab-runner
  fi

  if [[ -n "${RUNNER_TOKEN}" ]]; then
    echo "Registering Runner (shell executor) against https://${HOST} ..."
    # Check if already registered
    if ! sudo -u gitlab-runner gitlab-runner list 2>/dev/null | grep -qi "${HOST}"; then
      gitlab-runner register \
        --non-interactive \
        --url "https://${HOST}" \
        --registration-token "${RUNNER_TOKEN}" \
        --executor "shell" \
        --description "vm-shell-runner" \
        --tag-list "${RUNNER_TAGS}" \
        --run-untagged="${RUNNER_UNTAGGED}" \
        --locked="false"
      systemctl restart gitlab-runner
    else
      echo "Runner already registered; skipping."
    fi
  else
    echo "RUNNER_REGISTER=true but no --runner-token provided; skipping registration."
  fi
fi

# -------- Daily backup to GCS (idempotent) --------
if [[ "${ENABLE_GCS_BACKUP}" == "true" ]]; then
  # Derive bucket if not provided (reads project id from metadata)
  if [[ -z "${GCS_BUCKET}" ]]; then
    META="http://metadata.google.internal/computeMetadata/v1/project/project-id"
    PROJECT_ID="$(curl -s -H 'Metadata-Flavor: Google' ${META})"
    GCS_BUCKET="gs://gitlab-backups-${PROJECT_ID}/"
  fi

  cat >/usr/local/bin/gitlab-backup-to-gcs.sh <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
export GITLAB_BACKUP_DIR="/var/opt/gitlab/backups"
# create application + DB backup tar in GITLAB_BACKUP_DIR
gitlab-backup create STRATEGY=copy CRON=1
# sync to bucket
gsutil -m rsync -r "${GITLAB_BACKUP_DIR}" "__GCS_BUCKET__"
EOS
  sed -i "s|__GCS_BUCKET__|${GCS_BUCKET}|g" /usr/local/bin/gitlab-backup-to-gcs.sh
  chmod +x /usr/local/bin/gitlab-backup-to-gcs.sh

  # add nightly cron if not present
  crontab -l 2>/dev/null | grep -q 'gitlab-backup-to-gcs.sh' || \
    ( crontab -l 2>/dev/null; echo "30 2 * * * /usr/local/bin/gitlab-backup-to-gcs.sh >>/var/log/gitlab/backup.log 2>&1" ) | crontab -

  echo "GCS backups enabled to: ${GCS_BUCKET}"
fi

echo
echo "=========================================================="
echo "GitLab CE is configured at: https://${HOST}"
echo "Initial root password file (valid 24h after install):"
echo "  /etc/gitlab/initial_root_password"
echo "Next steps:"
echo "  - Log in as 'root' with the password from that file, then change it."
echo "  - Create a non-root admin user for daily use."
echo "  - Create sample projects and merge requests for demo."
echo "=========================================================="
