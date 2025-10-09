# GitLab Fivetran Connector

A production-ready Fivetran connector for extracting GitLab merge request data and related information.

## Overview

This connector extracts comprehensive data from GitLab projects including:
- Merge requests with metadata and status
- Comments, reviews, and approvals
- CI/CD pipeline runs
- Project information
- User profiles and activity

## Features

- **Incremental Sync**: Only syncs data changed since last run
- **Comprehensive Data**: Covers all aspects of MR lifecycle
- **Error Handling**: Robust retry logic and error recovery
- **Schema Management**: Automatic schema detection and updates
- **Performance**: Optimized for large GitLab instances

## Tables

### merge_requests
Core merge request data including titles, descriptions, status, and metadata.

### mr_notes
Comments, reviews, and approvals on merge requests with classification.

### pipelines
CI/CD pipeline runs associated with merge requests.

### projects
GitLab project and repository information.

### users
User profiles and activity data.

## Configuration

### Required Environment Variables

```bash
# GitLab API access
GITLAB_TOKEN=your-gitlab-token
GITLAB_BASE_URL=https://gitlab.com  # Optional, defaults to gitlab.com

# Projects to sync
GITLAB_PROJECT_IDS=100,101,102  # Comma-separated project IDs
```

### Optional Configuration

```bash
# Sync settings
SYNC_INTERVAL_HOURS=1
MAX_RECORDS_PER_SYNC=10000

# Data processing
ENABLE_NOTE_CLASSIFICATION=true
ENABLE_USER_DEDUPLICATION=true
ENABLE_PIPELINE_ANALYSIS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp config.env.example config.env
# Edit config.env with your actual GitLab settings
# Note: config.env is gitignored and should not be committed
```

3. Run the connector:
```bash
python connector.py
```

## Usage

### Basic Usage

```python
from connector import GitLabConnector

# Initialize connector
connector = GitLabConnector()

# Get schema
schema = connector.get_schema()

# Read data
for record in connector.read('merge_requests'):
    print(record)
```

### Fivetran Integration

The connector implements the Fivetran SDK interface:

```python
from fivetran_sdk import Connector

class GitLabConnector(Connector):
    def get_schema(self):
        # Return table definitions
        pass
    
    def read(self, table, last_sync_time=None):
        # Return data iterator
        pass
```

## Data Processing

### Note Classification
Automatically classifies notes as:
- **approval**: Contains approval keywords
- **review**: Contains review-related terms
- **comment**: General comments

### Incremental Sync
- Uses `updated_at` timestamps for incremental updates
- Only processes changed records since last sync
- Handles pagination automatically

### Error Handling
- Automatic retries with exponential backoff
- Graceful handling of API rate limits
- Comprehensive logging for debugging

## Testing

Run the test suite:

```bash
pytest tests/test_connector.py -v
```

## Schema Evolution

The connector handles schema changes automatically:
- New columns are added dynamically
- Data types are inferred from API responses
- Backward compatibility is maintained

## Performance Considerations

- **Pagination**: Handles large datasets efficiently
- **Rate Limiting**: Respects GitLab API limits
- **Memory Usage**: Streams data to avoid memory issues
- **Parallel Processing**: Can be configured for multiple projects

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify `GITLAB_TOKEN` is valid
   - Check token permissions

2. **Rate Limiting**
   - Increase `RETRY_DELAY_SECONDS`
   - Reduce `MAX_RECORDS_PER_SYNC`

3. **Schema Errors**
   - Check API response format
   - Verify column data types

### Debugging

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python connector.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
