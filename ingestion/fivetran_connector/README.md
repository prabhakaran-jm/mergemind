# GitLab Fivetran Connector

A production-ready custom Fivetran connector that extracts data from GitLab API and syncs it to BigQuery with incremental sync support and **automatic project discovery**.

## Features

- **Dynamic Project Discovery**: Automatically discovers projects based on patterns (no more manual project ID updates!)
- **Incremental Syncs**: Only fetches changed data using `last_sync_time`
- **Batch Processing**: Eliminates N+1 API calls with batch user fetching
- **Configurable Tables**: Enable/disable specific tables (projects, merge_requests, users)
- **Start Date Limiting**: Control historical data fetch on first sync
- **Checkpointing**: Resilient to failures with progress saving
- **Error Handling**: Comprehensive error handling with specific HTTP status codes
- **Pattern Matching**: Flexible project name filtering with wildcard support

## Files

- `connector.py` - Main connector code with incremental sync support
- `requirements.txt` - Python dependencies (minimal)
- `config.env.example` - Environment variables template
- `configuration_example.json` - Configuration template

## Quick Start

### Option 1: Dynamic Discovery (Recommended)

1. **Setup Configuration:**
   ```json
   {
     "gitlab_token": "your-gitlab-token",
     "gitlab_base_url": "https://your-gitlab-instance.com",
     "auto_discover_projects": true,
     "project_name_pattern": "*",
     "include_private_projects": true,
     "max_projects_to_sync": 100
   }
   ```

2. **Test Locally:**
   ```bash
   python test_updated_connector.py
   ```

3. **Deploy to Fivetran:**
   ```bash
   fivetran deploy --api-key YOUR_API_KEY --destination YOUR_DESTINATION --connection gitlab_connector --configuration configuration.json
   ```

### Option 2: Static Project IDs (Legacy)

1. **Setup Configuration:**
   ```json
   {
     "gitlab_token": "your-gitlab-token",
     "gitlab_base_url": "https://your-gitlab-instance.com",
     "gitlab_project_ids": "4,5,6,7,8,9",
     "auto_discover_projects": false
   }
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

### Dynamic Discovery (Recommended)
- `auto_discover_projects` - Enable automatic project discovery ("true"/"false")
- `project_name_pattern` - Pattern to match project names ("*", "mergemind-*", "*-demo-*")
- `include_private_projects` - Include private projects ("true"/"false")
- `max_projects_to_sync` - Maximum projects to sync ("100")

### Static Project IDs (Legacy)
- `gitlab_project_ids` - Comma-separated project IDs ("4,5,6,7,8,9")

### Optional
- `start_date` - Limit historical data (ISO format: "2025-01-01T00:00:00Z")
- `sync_projects_table` - Enable projects sync ("true"/"false")
- `sync_merge_requests_table` - Enable merge requests sync ("true"/"false")
- `sync_users_table` - Enable users sync ("true"/"false")
- `max_records_per_sync` - Maximum records per sync ("10000")
- `sync_interval_hours` - Sync interval in hours ("1")

## Dynamic Discovery Examples

### Sync All Projects
```json
{
  "auto_discover_projects": true,
  "project_name_pattern": "*"
}
```

### Sync Only MergeMind Projects
```json
{
  "auto_discover_projects": true,
  "project_name_pattern": "mergemind-*"
}
```

### Sync Only Demo Projects
```json
{
  "auto_discover_projects": true,
  "project_name_pattern": "*-demo-*"
}
```

### Sync Specific Project Types
```json
{
  "auto_discover_projects": true,
  "project_name_pattern": "mergemind-*-service"
}
```

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

- **Dynamic Project Discovery**: Automatically discovers projects without manual configuration updates
- **Pattern-Based Filtering**: Efficiently filter projects using wildcard patterns
- **Cached Discovery**: Project discovery results cached for 1 hour to reduce API calls
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
✅ **Dynamic Discovery**: Automatically discovers projects based on patterns  
✅ **Tested**: Successfully tested with GitLab API and pattern matching  
✅ **Scalable**: Handles large datasets efficiently  
✅ **Secure**: No sensitive data in repository  
✅ **Backward Compatible**: Existing configurations continue to work  

## Next Steps

1. **Deploy to Fivetran** with dynamic discovery enabled
2. **Link to BigQuery destination**
3. **Monitor sync performance** and project discovery
4. **Create new projects** - they'll be automatically discovered!
5. **Scale to additional projects** without configuration changes