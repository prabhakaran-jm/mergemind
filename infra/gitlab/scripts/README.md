# GitLab Scripts

This directory contains consolidated scripts for managing GitLab projects, merge requests, and content for AI testing.

## Files

- `gitlab_manager.py` - Main consolidated script for all GitLab operations
- `config.env` - Environment configuration
- `config.env.example` - Example configuration file
- `bootstrap-gitlab.sh` - Bootstrap script for GitLab setup

## Usage

### Create Projects and Content

```bash
# Run the consolidated GitLab manager
python gitlab_manager.py
```

This will:
- Create 3 new GitLab projects with diverse code content
- Add realistic files (README, package.json, server.js, etc.)
- Create feature branches
- Create merge requests with detailed descriptions
- Set up projects for AI analysis

### Configuration

Create a `config.env` file from the example:

```bash
# Copy the example file
cp config.env.example config.env

# Edit with your actual values
GITLAB_BASE_URL=https://your-gitlab-instance.sslip.io
GITLAB_TOKEN=glpat-your-token-here
GITLAB_PROJECT_IDS=4,5,6,7,8,9
```

## Projects Created

The script creates these projects with realistic content:

1. **mergemind-database-service** - Database service with PostgreSQL and Redis
2. **mergemind-notification-service** - Notification service with email, SMS, and push
3. **mergemind-analytics-service** - Analytics service with Elasticsearch and data visualization

Each project includes:
- Complete README with features and setup instructions
- package.json with realistic dependencies
- Server code with health checks and API endpoints
- Feature branches with meaningful names
- Merge requests with detailed descriptions and testing checklists

## Integration with MergeMind

After running the script:

1. **Update Fivetran Connector**: The new project IDs (7,8,9) will be automatically discovered by the dynamic connector
2. **Wait for Data Sync**: Fivetran will sync the new projects to BigQuery
3. **Test AI Analysis**: The MergeMind UI will now have diverse merge requests for AI analysis

## Benefits

- **Consolidated**: Single script handles all GitLab operations
- **Realistic**: Creates actual code files with proper structure
- **Diverse**: Different types of changes for comprehensive AI testing
- **Automated**: No manual intervention required
- **Scalable**: Easy to add more projects or modify existing ones
