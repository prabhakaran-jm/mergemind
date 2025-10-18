# MergeMind GCP Infrastructure

This Terraform configuration sets up the required GCP APIs and resources for the MergeMind application.

## Overview

The infrastructure includes:
- **GCP APIs**: Vertex AI, BigQuery, Cloud Storage, IAM, and more
- **BigQuery Datasets**: For MergeMind data, GitLab connector data, and Fivetran data
- **Service Accounts**: For API operations and Vertex AI access
- **Cloud Storage**: For Terraform state and application data
- **VPC Networking**: For secure communication
- **Secret Manager**: For storing sensitive credentials
- **IAM Roles**: For proper access control

## Prerequisites

1. **GCP Project**: Ensure you have a GCP project with billing enabled
2. **Terraform**: Install Terraform >= 1.0
3. **gcloud CLI**: Install and authenticate with GCP
4. **Permissions**: Ensure you have the following roles:
   - Project Editor or Owner
   - Service Account Admin
   - IAM Admin
   - BigQuery Admin
   - Storage Admin

## Quick Start

### Option 1: Automated Setup (Recommended)

**Bash (Linux/Mac/WSL):**
```bash
cd deploy/terraform
chmod +x setup.sh
chmod +x deploy_function.sh
./setup.sh
```

### Option 2: Manual Setup

1. **Clone and navigate to the terraform directory**:
   ```bash
   cd deploy/terraform
   ```

2. **Copy the example variables file**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit terraform.tfvars with your values**:
   ```bash
   # Edit the file with your project details
   nano terraform.tfvars
   ```

4. **Initialize Terraform**:
   ```bash
   terraform init
   ```

5. **Plan the deployment**:
   ```bash
   terraform plan
   ```

6. **Deploy Cloud Function source** (if using event-driven dbt):
   ```bash
   ./deploy_function.sh
   ```

7. **Apply the configuration**:
   ```bash
   terraform apply
   ```

## Configuration

### Required Variables

- `project_id`: Your GCP project ID
- `region`: GCP region for resources
- `environment`: Environment name (dev, staging, prod)

### Optional Variables

- `bigquery_location`: BigQuery dataset location (default: US)
- `vertex_ai_location`: Vertex AI location (default: us-central1)
- `vertex_ai_model`: Vertex AI model to use (default: gemini-1.5-pro)
- `enable_*`: Feature flags to enable/disable specific resources

## Resources Created

### GCP APIs Enabled
- Vertex AI (`aiplatform.googleapis.com`)
- BigQuery (`bigquery.googleapis.com`)
- Cloud Storage (`storage.googleapis.com`)
- IAM (`iam.googleapis.com`)
- Secret Manager (`secretmanager.googleapis.com`)
- And many more...

### BigQuery Datasets
- `mergemind`: Main application dataset
- `mergemind_raw`: Raw GitLab data from Fivetran
- `fivetran_data`: Fivetran connector data

### Service Accounts
- `mergemind-api`: For API operations
- `vertex-ai-mergemind`: For Vertex AI operations

### Cloud Storage Buckets
- `{project-id}-terraform-state`: For Terraform state
- `{project-id}-mergemind-data`: For application data

### Networking
- VPC network: `mergemind-vpc`
- Subnet: `mergemind-subnet` (10.0.1.0/24)
- Firewall rules for API access

### Secrets
- `gitlab-token`: GitLab API token
- `vertex-ai-key`: Vertex AI API key

## Usage

### Setting up Secrets

After deployment, you need to add your secrets:

1. **GitLab Token**:
   ```bash
   echo "your-gitlab-token" | gcloud secrets versions add gitlab-token --data-file=-
   ```

2. **Vertex AI Key** (if needed):
   ```bash
   echo "your-vertex-ai-key" | gcloud secrets versions add vertex-ai-key --data-file=-
   ```

### Accessing Resources

The Terraform outputs provide all the necessary information:

```bash
# View all outputs
terraform output

# View specific output
terraform output mergemind_dataset_id
terraform output mergemind_api_service_account
```

## Environment Variables

After deployment, set these environment variables:

```bash
export GCP_PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
export GITLAB_TOKEN="$(gcloud secrets versions access latest --secret=gitlab-token)"
export VERTEX_AI_LOCATION="us-central1"
```

## Cost Optimization

### BigQuery
- Use `bigquery_slot_capacity` to control slot usage
- Set appropriate `retention_days` for data lifecycle
- Use `bigquery_location` to optimize costs

### Storage
- Use `storage_class` to choose cost-effective storage
- Set `retention_days` for automatic cleanup
- Enable versioning only when needed

### Vertex AI
- Use `vertex_ai_model` to choose appropriate model
- Set `vertex_ai_location` for optimal performance/cost

## Security

### IAM Roles
- Minimal permissions principle
- Service accounts with specific roles
- No broad access grants

### Secrets Management
- All sensitive data in Secret Manager
- Automatic rotation support
- Audit logging enabled

### Networking
- VPC isolation
- Firewall rules for specific ports
- No public IPs by default

## Monitoring

### Logging
- Structured logging enabled
- Cloud Logging integration
- Log retention policies

### Monitoring
- Cloud Monitoring enabled
- Custom metrics support
- Alerting capabilities

## Troubleshooting

### Common Issues

1. **API not enabled**:
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=your-project
   ```

2. **Permission denied**:
   - Check IAM roles
   - Verify service account permissions
   - Check project-level permissions

3. **Resource conflicts**:
   - Check for existing resources
   - Use `terraform import` if needed
   - Verify naming conventions

### Debugging

1. **Enable debug logging**:
   ```bash
   export TF_LOG=DEBUG
   terraform plan
   ```

2. **Check resource state**:
   ```bash
   terraform state list
   terraform state show resource_name
   ```

3. **Validate configuration**:
   ```bash
   terraform validate
   terraform fmt
   ```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all data and resources. Make sure to backup important data first.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Terraform documentation
3. Check GCP documentation
4. Open an issue in the repository

## Contributing

1. Follow Terraform best practices
2. Use meaningful variable names
3. Add appropriate descriptions
4. Test changes in dev environment first
5. Update documentation as needed
