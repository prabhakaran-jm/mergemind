# GitLab Infrastructure Setup

This directory contains infrastructure-as-code for setting up a self-hosted GitLab instance on Google Cloud Platform for the MergeMind hackathon project.

## 🏗️ Architecture

- **Terraform**: Infrastructure provisioning on GCP with remote state
- **GCS Backend**: Remote state storage with versioning and locking
- **Bootstrap Script**: Automated GitLab installation and configuration
- **Docker Compose**: Local development environment
- **GCS Backups**: Automated daily backups to Google Cloud Storage

## 📋 Prerequisites

- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed and authenticated
- `terraform` installed (>= 1.5.0)
- Domain name (optional, can use sslip.io)

## 🚀 Quick Start

### 1. Deploy Infrastructure (Recommended)

```bash
cd infra/gitlab
./setup.sh
```

This will automatically:
- Set up Terraform GCS backend
- Create state bucket with versioning
- Configure terraform.tfvars and backend.tf
- Initialize Terraform
- Deploy infrastructure
- Create demo GitLab projects

### 2. Manual Setup (Alternative)

```bash
cd infra/gitlab/terraform

# Setup backend
./setup-backend.sh

# Configure variables
cp terraform.tfvars.example terraform.tfvars
cp backend.tf.example backend.tf
# Edit files with your GCP project ID

# Deploy
terraform init
terraform plan
terraform apply
```

### 3. Get Outputs

```bash
terraform output
# Note the IP address and suggested hostname
```

### 4. Bootstrap GitLab

```bash
# Get values from terraform output
IP=$(terraform output -raw gitlab_external_ip)
HOST=$(terraform output -raw suggested_gitlab_host)

# Copy bootstrap script to VM
gcloud compute scp ../scripts/bootstrap-gitlab.sh gitlab-ce:~/

# Run bootstrap with Let's Encrypt
gcloud compute ssh gitlab-ce --command "chmod +x ~/bootstrap-gitlab.sh && sudo ./bootstrap-gitlab.sh --host '${HOST}' --tls letsencrypt --email 'your-email@example.com'"
```

### 5. Access GitLab

```bash
# Get initial root password
gcloud compute ssh gitlab-ce --command "sudo cat /etc/gitlab/initial_root_password"

# Open GitLab in browser
echo "https://${HOST}"
```

### 6. Populate Demo Projects

After GitLab is running and you have created a Personal Access Token:

```bash
cd infra/gitlab/scripts

# Copy and configure environment
cp config.env.example config.env
# Edit config.env with your GitLab URL and token

# Install Python dependencies
pip install requests python-dotenv

# Populate projects with sample content
python populate_gitlab_projects.py
```

This will add:
- Sample files (README, package.json, source code)
- Feature branches
- Merge requests with detailed descriptions
- Issues with labels

## 🔧 Configuration Options

### Bootstrap Script Options

```bash
./bootstrap-gitlab.sh \
  --host "gitlab.example.com" \
  --tls "letsencrypt" \
  --email "admin@example.com" \
  --runner-register "true" \
  --runner-token "YOUR_RUNNER_TOKEN" \
  --enable-gcs-backup "true"
```

### TLS Options

- **Let's Encrypt**: Free SSL certificates (recommended)
- **Self-signed**: For testing or internal use

### GitLab Runner

Enable CI/CD by registering a shell runner:

1. In GitLab UI: Admin → CI/CD → Runners → New instance runner
2. Copy the registration token
3. Use `--runner-register true --runner-token TOKEN`

### GCS Backups

Automated daily backups to Google Cloud Storage:

1. Creates backup bucket automatically
2. 7-day retention policy
3. Runs at 2:30 AM daily

## 💰 Cost Optimization

### VM Management

```bash
# Stop VM (saves money)
gcloud compute instances stop gitlab-ce --zone=us-central1-a

# Start VM (when needed)
gcloud compute instances start gitlab-ce --zone=us-central1-a
```

### Estimated Costs

- **Running 24/7**: ~$25/month
- **On-demand only**: ~$5-8/month
- **Storage**: ~$2/month (persistent)

## 🐳 Local Development

For local testing without GCP costs:

```bash
cd infra/gitlab/docker
docker-compose up -d

# Access at http://localhost:8080
# Initial password: docker-compose exec gitlab cat /etc/gitlab/initial_root_password
```

## 📊 Monitoring

### Health Checks

```bash
# Check GitLab status
gcloud compute ssh gitlab-ce --command "sudo gitlab-ctl status"

# View logs
gcloud compute ssh gitlab-ce --command "sudo gitlab-ctl tail"

# Check disk usage
gcloud compute ssh gitlab-ce --command "df -h"
```

### Backup Status

```bash
# Check backup logs
gcloud compute ssh gitlab-ce --command "sudo tail -f /var/log/gitlab/backup.log"

# List backups in GCS
gsutil ls gs://gitlab-backups-$(gcloud config get-value project)/
```

## 🔒 Security

### Firewall Rules

- **SSH (22)**: For administration
- **HTTP (80)**: Redirects to HTTPS
- **HTTPS (443)**: GitLab web interface

### SSL/TLS

- Let's Encrypt certificates auto-renew
- Self-signed certificates for testing
- HSTS enabled for security

### Access Control

- Change default root password immediately
- Create non-root admin user
- Configure 2FA for admin accounts

## 🛠️ Troubleshooting

### Common Issues

1. **VM won't start**: Check quotas and billing
2. **SSL errors**: Verify domain DNS resolution
3. **Backup failures**: Check GCS permissions
4. **High memory usage**: Adjust GitLab configuration

### Logs

```bash
# GitLab logs
sudo gitlab-ctl tail

# System logs
sudo journalctl -u gitlab-runsvdir

# Nginx logs
sudo tail -f /var/log/gitlab/nginx/error.log
```

### Performance Tuning

For better performance on e2-medium:

```bash
# Edit GitLab configuration
sudo nano /etc/gitlab/gitlab.rb

# Reduce worker processes
puma['worker_processes'] = 2
sidekiq['max_concurrency'] = 5

# Apply changes
sudo gitlab-ctl reconfigure
```

## 📚 Resources

- [GitLab CE Documentation](https://docs.gitlab.com/ee/install/)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest)
- [Let's Encrypt](https://letsencrypt.org/)
- [sslip.io](https://sslip.io/) - Dynamic DNS for testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test changes locally
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
