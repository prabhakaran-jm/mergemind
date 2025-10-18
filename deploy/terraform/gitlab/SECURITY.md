# GitLab Demo Resources - Security Guidelines

## 🔒 **Security Best Practices**

### ✅ **What We've Fixed**

1. **Removed Hardcoded IPs**: No more `35.202.37.189.sslip.io` in code
2. **Removed Hardcoded Tokens**: No more `glpat-xxxxxxxxxxxxxxxxxxxx` in code
3. **Removed Hardcoded Emails**: No more `demo@mergemind.com` in code
4. **Added Variable References**: Using Terraform variables for all sensitive data
5. **Updated .gitignore**: Properly excludes sensitive files

### 🛡️ **Security Checklist**

Before committing any changes, ensure:

- [ ] No hardcoded IP addresses in code
- [ ] No hardcoded tokens or passwords
- [ ] No hardcoded email addresses
- [ ] All sensitive data uses variables
- [ ] `.gitignore` excludes sensitive files
- [ ] Example files use placeholder values

### 📁 **Files That Should NEVER Be Committed**

```
infra/gitlab/terraform/terraform.tfvars          # Contains real tokens
infra/gitlab/terraform/demo-resources.tfplan     # Contains sensitive data
infra/gitlab/terraform/*.tfplan                  # Any Terraform plan files
```

### 🔧 **Safe Configuration Process**

1. **Copy Example Files**:
   ```bash
   cp demo-terraform.tfvars.example terraform.tfvars
   ```

2. **Edit with Real Values**:
   ```bash
   # Edit terraform.tfvars with your actual values
   gitlab_token = "glpat-your-actual-token-here"
   gitlab_base_url = "https://your-actual-gitlab-domain.com/api/v4/"
   ```

3. **Verify .gitignore**:
   ```bash
   git status  # Should NOT show terraform.tfvars
   ```

### 🚨 **If You Accidentally Commit Sensitive Data**

1. **Remove from Git History**:
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch infra/gitlab/terraform/terraform.tfvars' \
     --prune-empty --tag-name-filter cat -- --all
   ```

2. **Force Push** (if already pushed):
   ```bash
   git push origin --force --all
   ```

3. **Rotate Credentials**:
   - Generate new GitLab tokens
   - Update all configurations
   - Revoke old tokens

### 🔍 **Security Validation Commands**

```bash
# Check for hardcoded IPs
grep -r "35\.202\.37\.189" infra/gitlab/terraform/

# Check for hardcoded tokens
grep -r "glpat-" infra/gitlab/terraform/ --exclude="*.example"

# Check for hardcoded emails
grep -r "demo@mergemind" infra/gitlab/terraform/

# Verify .gitignore is working
git status --ignored
```

### 📝 **Example File Standards**

All example files should use:
- `your-gitlab-domain.com` instead of real domains
- `glpat-xxxxxxxxxxxxxxxxxxxx` instead of real tokens
- `demo@example.com` instead of real emails
- `your-actual-value-here` for placeholders

### 🎯 **Environment-Specific Configuration**

Use environment variables when possible:

```bash
# In scripts
export GITLAB_TOKEN="glpat-your-token"
export GITLAB_BASE_URL="https://your-domain.com"

# In Terraform
variable "gitlab_token" {
  description = "GitLab token from environment"
  type        = string
  default     = var.gitlab_token != "" ? var.gitlab_token : ""
}
```

### 🔐 **Token Management**

1. **Create Tokens with Minimal Scope**:
   - `api` - For API access
   - `read_user` - For user information
   - `read_repository` - For repository data

2. **Set Expiration Dates**:
   - 30 days for development
   - 1 year for production (with rotation)

3. **Rotate Regularly**:
   - Monthly for development tokens
   - Quarterly for production tokens

### 🚫 **Never Do These**

- ❌ Commit real tokens to version control
- ❌ Share tokens in chat/email
- ❌ Use production tokens for development
- ❌ Hardcode sensitive data in code
- ❌ Ignore .gitignore warnings

### ✅ **Always Do These**

- ✅ Use environment variables for secrets
- ✅ Use placeholder values in examples
- ✅ Rotate tokens regularly
- ✅ Use minimal required permissions
- ✅ Review commits before pushing
- ✅ Use `.gitignore` properly

## 🆘 **Security Incident Response**

If you suspect a security breach:

1. **Immediately rotate all tokens**
2. **Check Git history for exposed secrets**
3. **Review access logs**
4. **Update all configurations**
5. **Document the incident**

## 📞 **Contact**

For security concerns, contact the project maintainers immediately.
