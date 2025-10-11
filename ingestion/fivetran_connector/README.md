# GitLab Fivetran Connector

A production-ready custom Fivetran connector that extracts data from GitLab API and syncs it to BigQuery with incremental sync support.

## Features

- **Incremental Syncs**: Only fetches changed data using `last_sync_time`
- **Batch Processing**: Eliminates N+1 API calls with batch user fetching
- **Configurable Tables**: Enable/disable specific tables (projects, merge_requests, users)
- **Start Date Limiting**: Control historical data fetch on first sync
- **Checkpointing**: Resilient to failures with progress saving
- **Error Handling**: Comprehensive error handling with specific HTTP status codes

## Files

- `connector.py` - Main connector code with incremental sync support
- `requirements.txt` - Python dependencies (minimal)
- `config.env.example` - Environment variables template
- `configuration_example.json` - Configuration template

## Quick Start

1. **Setup Configuration:**
   ```bash
   # Copy example configuration
   cp configuration_example.json configuration.json
   
   # Update with your values
   # - gitlab_token: Your GitLab Personal Access Token
   # - gitlab_base_url: Your GitLab instance URL
   # - gitlab_project_ids: Comma-separated project IDs
   ```

2. **Test Locally:**
   ```bash
   fivetran debug --configuration configuration.json
   ```

3. **Deploy to Fivetran:**
   ```bash
   fivetran deploy --api-key YOUR_API_KEY --destination YOUR_DESTINATION --connection gitlab_connector --configuration configuration.json
   ```

## Configuration Options

### Required
- `gitlab_token` - GitLab Personal Access Token
- `gitlab_base_url` - GitLab instance URL
- `gitlab_project_ids` - Comma-separated project IDs

### Optional
- `start_date` - Limit historical data (ISO format: "2025-01-01T00:00:00Z")
- `sync_projects_table` - Enable projects sync ("true"/"false")
- `sync_merge_requests_table` - Enable merge requests sync ("true"/"false")
- `sync_users_table` - Enable users sync ("true"/"false")
- `max_records_per_sync` - Maximum records per sync ("10000")
- `sync_interval_hours` - Sync interval in hours ("1")

## Data Schema

The connector creates three tables:

### projects
- `id`, `name`, `description`, `web_url`
- `created_at`, `updated_at`, `visibility`, `default_branch`

### merge_requests
- `id`, `project_id`, `title`, `description`, `state`
- `author_id`, `assignee_id`, `created_at`, `updated_at`
- `merged_at`, `closed_at`, `source_branch`, `target_branch`, `web_url`

### users
- `id`, `username`, `name`, `email`, `state`
- `created_at`, `last_activity_on`

## Performance Features

- **Incremental Syncs**: Only fetches data updated since last sync
- **Batch User Fetching**: Single API call for multiple users
- **Start Date Limiting**: Prevents full historical data fetch
- **Checkpointing**: Saves progress between table processing

## Security

- All sensitive configuration is excluded from version control
- Uses Fivetran's encrypted secrets management
- No hardcoded credentials in source code

## Current Status

✅ **Production Ready**: Fully functional with incremental syncs  
✅ **Tested**: Successfully tested with GitLab API  
✅ **Scalable**: Handles large datasets efficiently  
✅ **Secure**: No sensitive data in repository  

## Next Steps

1. Deploy to Fivetran
2. Link to BigQuery destination
3. Monitor sync performance
4. Scale to additional projects