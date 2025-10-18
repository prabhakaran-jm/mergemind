# Event-Driven Pipeline Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the MergeMind event-driven data pipeline, including infrastructure setup, Fivetran connector configuration, and testing procedures.

## Prerequisites

### Required Accounts
- Google Cloud Platform account with billing enabled
- Fivetran account (free tier available)
- GitLab instance access (self-hosted or GitLab.com)

### Required Tools
- Terraform >= 1.0
- Google Cloud SDK (gcloud)
- Git
- Python 3.11+
- Node.js 18+

### Required Permissions
- GCP Project Owner or Editor
- Fivetran Admin access
- GitLab API token with read permissions

## Step 1: Infrastructure Deployment

### 1.1 Clone Repository
```bash
git clone https://github.com/mergemind/mergemind.git
cd mergemind
```

### 1.2 Configure Terraform Variables
```bash
cd infra/gcp/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_id = "your-gcp-project-id"
region = "us-central1"
environment = "dev"

# Generate a secure token for Cloud Function authentication
dbt_trigger_auth_token = "your-secure-token-here"
```

### 1.3 Deploy Infrastructure
```bash
# Initialize Terraform
terraform init

# Review deployment plan
terraform plan

# Deploy infrastructure
terraform apply
```

### 1.4 Verify Deployment
```bash
# Check Cloud Function
gcloud functions describe dbt-trigger-function --region=us-central1

# Check BigQuery datasets
bq ls --project_id=your-project-id

# Get Cloud Function URL
terraform output dbt_trigger_function_url
```

## Step 2: Fivetran Connector Setup

### 2.1 Configure Connector
```bash
cd ingestion/fivetran_connector
```

Edit `fivetran_config.json`:
```json
{
  "gitlab_token": "glpat-your-gitlab-token",
  "gitlab_base_url": "https://your-gitlab.com",
  "dbt_trigger_url": "https://dbt-trigger-function-xxx-uc.a.run.app",
  "dbt_trigger_auth_token": "your-secure-token-here",
  "sync_interval_hours": "1",
  "auto_discover_projects": "true",
  "max_projects_to_sync": "100"
}
```

### 2.2 Deploy to Fivetran
1. Log into Fivetran dashboard
2. Create new connector
3. Upload connector code (ZIP file)
4. Configure connector settings
5. Test connection
6. Start sync

### 2.3 Verify Connector
```bash
# Test connector locally
python connector.py --config fivetran_config.json --test

# Check Fivetran logs for successful sync
# Look for: "Successfully triggered dbt run"
```

## Step 3: dbt Models Setup

### 3.1 Deploy dbt Models
```bash
cd warehouse/bigquery/dbt

# Install dbt
pip install dbt-bigquery

# Install dependencies
dbt deps

# Run models
dbt run

# Run tests
dbt test
```

### 3.2 Verify Models
```sql
-- Check raw data
SELECT COUNT(*) FROM `your-project.mergemind_raw.merge_requests`;

-- Check transformed data
SELECT COUNT(*) FROM `your-project.mergemind.dim_merge_requests`;
```

## Step 4: Testing the Pipeline

### 4.1 Create Test Data
```bash
# Create a test merge request via GitLab API
curl -X POST "https://your-gitlab.com/api/v4/projects/PROJECT_ID/merge_requests" \
  -H "PRIVATE-TOKEN: glpat-your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "source_branch": "feature/test-pipeline",
    "target_branch": "main",
    "title": "Test Event-Driven Pipeline",
    "description": "Testing the complete pipeline flow"
  }'
```

### 4.2 Monitor Pipeline
```bash
# Check Fivetran sync logs
# Look for: "Successfully triggered dbt run"

# Check Cloud Function logs
gcloud functions logs read dbt-trigger-function --region=us-central1 --limit=10

# Check BigQuery data
bq query --use_legacy_sql=false "
SELECT id, title, created_at 
FROM \`your-project.mergemind_raw.merge_requests\`
ORDER BY created_at DESC
LIMIT 5
"
```

### 4.3 Verify End-to-End Flow
1. **GitLab**: MR created ✅
2. **Fivetran**: Data synced to BigQuery ✅
3. **Cloud Function**: dbt triggered ✅
4. **dbt**: Transformations completed ✅
5. **BigQuery**: Modeled data available ✅

## Step 5: Production Configuration

### 5.1 Security Hardening
```bash
# Rotate authentication tokens
# Update dbt_trigger_auth_token in terraform.tfvars
terraform apply

# Update Fivetran connector configuration
# Redeploy connector with new token
```

### 5.2 Monitoring Setup
```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Set up alerts for Cloud Function errors
# Configure BigQuery usage alerts
# Set up Fivetran sync failure notifications
```

### 5.3 Backup and Recovery
```bash
# Enable BigQuery table snapshots
# Configure automated backups
# Test disaster recovery procedures
```

## Troubleshooting

### Common Issues

#### 1. Cloud Function Deployment Fails
```bash
# Check Terraform logs
terraform apply -debug

# Verify ZIP file exists
ls -la infra/gcp/terraform/cloud_function/dbt-trigger-function.zip

# Check Cloud Storage bucket
gsutil ls gs://your-project-dbt-function-source/
```

#### 2. Fivetran Connector Errors
```bash
# Check connector logs in Fivetran dashboard
# Verify GitLab API access
curl -H "PRIVATE-TOKEN: glpat-your-token" \
  "https://your-gitlab.com/api/v4/projects"

# Test Cloud Function URL
curl -X POST "https://dbt-trigger-function-xxx-uc.a.run.app" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"source": "test"}'
```

#### 3. dbt Execution Failures
```bash
# Check Cloud Function logs
gcloud functions logs read dbt-trigger-function --region=us-central1

# Verify dbt models
cd warehouse/bigquery/dbt
dbt debug
dbt run --models dim_merge_requests
```

#### 4. BigQuery Access Issues
```bash
# Check service account permissions
gcloud projects get-iam-policy your-project-id

# Verify BigQuery datasets exist
bq ls --project_id=your-project-id
```

### Debug Commands

```bash
# Test complete pipeline
./scripts/test_event_driven_pipeline.sh

# Check all components
./scripts/validate_deployment.sh

# Monitor real-time logs
gcloud functions logs tail dbt-trigger-function --region=us-central1
```

## Maintenance

### Regular Tasks

#### Weekly
- Review Fivetran sync logs
- Check Cloud Function error rates
- Monitor BigQuery costs
- Verify data freshness

#### Monthly
- Rotate authentication tokens
- Update dbt models and dependencies
- Review and optimize queries
- Check security configurations

#### Quarterly
- Review and update documentation
- Performance optimization
- Cost analysis and optimization
- Security audit

### Updates and Upgrades

#### Infrastructure Updates
```bash
cd infra/gcp/terraform
terraform plan
terraform apply
```

#### Connector Updates
```bash
cd ingestion/fivetran_connector
# Update connector code
# Redeploy to Fivetran
```

#### dbt Model Updates
```bash
cd warehouse/bigquery/dbt
# Update models
dbt run
dbt test
```

## Support and Resources

### Documentation
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API_REFERENCE.md)
- [Monitoring Guide](MONITORING.md)

### Community
- GitHub Issues: https://github.com/mergemind/mergemind/issues
- Discussions: https://github.com/mergemind/mergemind/discussions

### Professional Support
- Enterprise support available
- Custom deployment assistance
- Training and consulting services

## Changelog

### v1.0.0
- Initial deployment guide
- Complete step-by-step instructions
- Troubleshooting section
- Maintenance procedures

### Planned Updates
- Automated deployment scripts
- CI/CD integration
- Advanced monitoring setup
- Multi-region deployment
