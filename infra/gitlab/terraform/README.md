# GitLab Demo Resources Setup Guide

This directory contains multiple approaches to create GitLab demo resources programmatically.

## 🎯 **Approaches Available**

### 1. **Terraform Provider (RECOMMENDED)**
- **Files**: `demo-resources.tf`, `demo-variables.tf`, `demo-outputs.tf`
- **Pros**: Infrastructure as Code, version controlled, repeatable
- **Cons**: Requires GitLab Terraform Provider setup

### 2. **GitLab API Script**
- **File**: `create-demo-api.py`
- **Pros**: Direct API control, flexible, no Terraform dependency
- **Cons**: Requires Python, manual script execution

### 3. **Manual Web Interface**
- **Pros**: Visual, easy to understand
- **Cons**: Time-consuming, not repeatable

## 🚀 **Quick Start - Terraform Approach**

### Prerequisites
1. **GitLab Token**: Create a personal access token with `api` scope
2. **Terraform**: Install Terraform CLI
3. **GitLab Access**: Ensure your GitLab instance is running

### Steps

1. **Get GitLab Token**:
   ```bash
   # SSH into GitLab VM
   gcloud compute ssh gitlab-ce --zone=us-central1-a
   
   # Get initial password
   sudo cat /etc/gitlab/initial_root_password
   
   # Login to GitLab web interface
   # Go to: https://your-gitlab-domain.com
   # Username: root
   # Password: (from file above)
   
   # Create token: Profile → Access Tokens
   # Name: MergeMind Demo
   # Scopes: api, read_user, read_repository
   ```

2. **Configure Terraform**:
   ```bash
   cd infra/gitlab/terraform
   
   # Copy example variables
   cp demo-terraform.tfvars.example terraform.tfvars
   
   # Edit terraform.tfvars
   # Set: gitlab_token = "glpat-xxxxxxxxxxxxxxxxxxxx"
   ```

3. **Create Demo Resources**:
   ```bash
   # Run setup script
   bash setup-demo.sh
   
   # Or manually:
   terraform init
   terraform plan
   terraform apply
   ```

4. **Get Project IDs**:
   ```bash
   terraform output project_ids_for_config
   ```

## 🐍 **Alternative - Python API Approach**

1. **Install Python dependencies**:
   ```bash
   pip install requests
   ```

2. **Configure script**:
   ```bash
   # Edit create-demo-api.py
   # Set: GITLAB_TOKEN = "glpat-xxxxxxxxxxxxxxxxxxxx"
   ```

3. **Run script**:
   ```bash
   python create-demo-api.py
   ```

## 📊 **What Gets Created**

### Projects
- `mergemind-demo-frontend` - React frontend with auth component
- `mergemind-demo-backend` - Node.js backend with JWT service
- `mergemind-demo-api` - Express API with auth endpoints

### Branches & Files
- `feature/user-auth` - Frontend authentication component
- `feature/jwt-auth` - Backend JWT authentication service
- `feature/auth-endpoints` - API authentication endpoints

### Merge Requests
- Each feature branch has a corresponding MR with:
  - Detailed descriptions
  - Code examples
  - Testing checklists
  - Screenshots placeholders

### Issues
- Enhancement issues for each project
- Properly labeled and assigned

## 🔧 **Configuration for Fivetran**

After running either approach, you'll get project IDs like:
```
Project IDs for Fivetran: 123, 456, 789
```

Update your `config.env`:
```bash
GITLAB_BASE_URL=https://your-gitlab-domain.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
GITLAB_PROJECT_IDS=123,456,789
```

## 🧪 **Testing the Setup**

1. **Verify Projects**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        "https://your-gitlab-domain.com/api/v4/projects"
   ```

2. **Check Merge Requests**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        "https://your-gitlab-domain.com/api/v4/projects/PROJECT_ID/merge_requests"
   ```

3. **Test Fivetran Connector**:
   ```bash
   cd ingestion/fivetran_connector
   python connector.py
   ```

## 🎯 **Recommended Workflow**

1. **Use Terraform approach** for initial setup
2. **Use Python script** for quick iterations
3. **Use web interface** for manual testing/debugging

## 🔍 **Troubleshooting**

### Common Issues

1. **Token Permissions**:
   - Ensure token has `api` scope
   - Check token hasn't expired

2. **GitLab API Rate Limits**:
   - Add delays between requests
   - Use batch operations when possible

3. **Terraform Provider Issues**:
   - Check GitLab provider version compatibility
   - Verify GitLab instance version

### Debug Commands

```bash
# Test API access
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://your-gitlab-domain.com/api/v4/user"

# Check project access
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://your-gitlab-domain.com/api/v4/projects"

# Verify merge requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://your-gitlab-domain.com/api/v4/projects/PROJECT_ID/merge_requests"
```

## 📝 **Next Steps**

After creating demo resources:

1. **Test Fivetran Connector** with the project IDs
2. **Run MergeMind API** to see demo data
3. **Test Slack Bot** with demo merge requests
4. **Verify BigQuery** data pipeline

## 🔗 **Useful Links**

- [GitLab Terraform Provider](https://registry.terraform.io/providers/gitlabhq/gitlab/latest)
- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)
- [GitLab Personal Access Tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)
