# MergeMind API Reference

Complete reference documentation for the MergeMind API endpoints, including request/response schemas, error codes, and examples.

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Endpoints](#endpoints)
6. [Event-Driven Pipeline](#event-driven-pipeline)
7. [Data Models](#data-models)
8. [Examples](#examples)
9. [SDKs](#sdks)

## Authentication

Currently, the MergeMind API does not require authentication for MVP. Future versions will support:

- **API Key Authentication**: Include `X-API-Key` header
- **OAuth 2.0**: Bearer token authentication
- **JWT Tokens**: For user-specific operations

### Example with API Key (Future)
```bash
curl -H "X-API-Key: your-api-key" \
  "https://api.mergemind.com/api/v1/mrs"
```

## Base URL

- **Development**: `http://localhost:8080/api/v1`
- **Staging**: `https://staging-api.mergemind.com/api/v1`
- **Production**: `https://api.mergemind.com/api/v1`

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Limit**: 100 requests per minute per IP address
- **Headers**: Rate limit information included in responses
- **Exceeded**: Returns HTTP 429 with retry information

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

All errors return JSON with the following structure:

```json
{
  "error": "Error message",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

### Error Codes

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | MR not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | External service down |

## Endpoints

## Event-Driven Pipeline

The MergeMind platform includes an event-driven data pipeline that automatically processes GitLab data. The pipeline is triggered by Fivetran connector syncs and runs dbt transformations.

### Cloud Function Endpoint

#### POST /dbt-trigger-function
Triggers dbt transformations when called by Fivetran connector.

**Authentication:** Bearer token required
**Content-Type:** application/json

**Request Body:**
```json
{
  "source": "fivetran_connector",
  "action": "run_dbt",
  "sync_info": {
    "sync_time": "2024-01-01T12:00:00Z",
    "project_count": 12,
    "sync_interval_hours": 1
  }
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "dbt run completed successfully",
  "source": "fivetran_connector",
  "sync_info": {
    "sync_time": "2024-01-01T12:00:00Z",
    "project_count": 12,
    "sync_interval_hours": 1
  },
  "timestamp": "2024-01-01T12:05:00Z"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "dbt run failed",
  "source": "fivetran_connector",
  "sync_info": {
    "sync_time": "2024-01-01T12:00:00Z",
    "project_count": 12,
    "sync_interval_hours": 1
  },
  "timestamp": "2024-01-01T12:05:00Z"
}
```

**Error Codes:**
- `401`: Unauthorized (invalid or missing Bearer token)
- `500`: Internal server error (dbt execution failed)
- `503`: Service unavailable (dependencies not available)

### Pipeline Status Endpoint

#### GET /pipeline/status
Get current status of the event-driven pipeline.

**Response:**
```json
{
  "status": "healthy",
  "last_sync": "2024-01-01T12:00:00Z",
  "last_dbt_run": "2024-01-01T12:05:00Z",
  "sync_frequency_hours": 1,
  "components": {
    "fivetran_connector": "healthy",
    "cloud_function": "healthy",
    "dbt_models": "healthy",
    "bigquery": "healthy"
  },
  "metrics": {
    "total_syncs_today": 24,
    "successful_dbt_runs": 23,
    "failed_dbt_runs": 1,
    "average_dbt_duration_seconds": 45
  }
}
```

### Pipeline Metrics Endpoint

#### GET /pipeline/metrics
Get detailed metrics about pipeline performance.

**Query Parameters:**
- `time_range` (optional): Time range for metrics (`1h`, `24h`, `7d`, `30d`)
- `component` (optional): Filter by component (`fivetran`, `dbt`, `bigquery`)

**Response:**
```json
{
  "time_range": "24h",
  "timestamp": "2024-01-01T12:00:00Z",
  "metrics": {
    "sync_metrics": {
      "total_syncs": 24,
      "successful_syncs": 23,
      "failed_syncs": 1,
      "average_sync_duration_seconds": 120
    },
    "dbt_metrics": {
      "total_runs": 23,
      "successful_runs": 22,
      "failed_runs": 1,
      "average_duration_seconds": 45,
      "models_processed": 4
    },
    "data_metrics": {
      "records_processed": 1500,
      "tables_updated": 3,
      "data_freshness_minutes": 5
    }
  }
}
```

### Health Check

#### GET /healthz
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET /ready
Readiness check with dependency validation.

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "bigquery": "healthy",
    "gitlab": "healthy",
    "vertex": "healthy"
  }
}
```

#### GET /health/detailed
Comprehensive health check with metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "bigquery": {
      "status": "healthy",
      "response_time_ms": 45
    },
    "gitlab": {
      "status": "healthy",
      "response_time_ms": 120
    },
    "vertex": {
      "status": "healthy",
      "response_time_ms": 890
    }
  },
  "metrics": {
    "uptime_seconds": 86400,
    "request_count": 1500,
    "error_count": 5,
    "error_rate": 0.003
  }
}
```

### Merge Requests List

#### GET /mrs
List merge requests with risk analysis.

**Query Parameters:**
- `state` (optional): Filter by state (`open`, `merged`, `closed`)
- `project_id` (optional): Filter by project ID
- `risk_band` (optional): Filter by risk band (`Low`, `Medium`, `High`)
- `limit` (optional): Maximum results (default: 50, max: 200)
- `cursor` (optional): Pagination cursor

**Response:**
```json
{
  "mrs": [
    {
      "mr_id": 123,
      "project_id": 456,
      "title": "Add user authentication",
      "author": "john.doe",
      "age_hours": 24.5,
      "risk_band": "Medium",
      "risk_score": 45,
      "pipeline_status": "success",
      "approvals_left": 1,
      "notes_count_24h": 3,
      "additions": 150,
      "deletions": 20
    }
  ],
  "pagination": {
    "next_cursor": "eyJtcl9pZCI6MTI0fQ==",
    "has_more": true
  }
}
```

#### GET /blockers/top
Get top blocking merge requests.

**Query Parameters:**
- `limit` (optional): Maximum results (default: 10, max: 50)

**Response:**
```json
{
  "blockers": [
    {
      "mr_id": 123,
      "project_id": 456,
      "title": "Critical security fix",
      "author": "jane.smith",
      "age_hours": 72.0,
      "risk_band": "High",
      "risk_score": 85,
      "pipeline_status": "failed",
      "approvals_left": 2,
      "notes_count_24h": 8,
      "additions": 500,
      "deletions": 100,
      "blocking_reason": "Failed pipeline blocking other MRs"
    }
  ]
}
```

### Individual Merge Request

#### GET /mr/{id}/context
Get comprehensive MR context and analysis.

**Path Parameters:**
- `id` (required): Merge request ID

**Response:**
```json
{
  "mr_id": 123,
  "project_id": 456,
  "title": "Add user authentication",
  "author": {
    "user_id": 789,
    "name": "john.doe",
    "email": "john.doe@company.com"
  },
  "state": "opened",
  "age_hours": 24.5,
  "risk": {
    "score": 45,
    "band": "Medium",
    "reasons": [
      "2 approvals remaining",
      "MR age: 24.5 hours",
      "Medium size change"
    ]
  },
  "last_pipeline": {
    "status": "success",
    "age_min": 30,
    "web_url": "https://gitlab.com/project/-/pipelines/12345"
  },
  "approvals_left": 1,
  "notes_recent": 3,
  "size": {
    "additions": 150,
    "deletions": 20,
    "files_changed": 8
  },
  "labels": ["frontend", "security"],
  "web_url": "https://gitlab.com/project/merge_requests/123",
  "source_branch": "feature/auth",
  "target_branch": "main",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T11:30:00Z"
}
```

#### POST /mr/{id}/summary
Generate AI-powered summary of the merge request.

**Path Parameters:**
- `id` (required): Merge request ID

**Response:**
```json
{
  "summary": [
    "Refactors user authentication to use JWT tokens",
    "Adds input validation for email and password fields",
    "Updates API endpoints to return consistent error responses"
  ],
  "risks": [
    "JWT token expiration handling may cause user session issues",
    "Input validation bypass could allow SQL injection",
    "Missing error handling in edge cases"
  ],
  "tests": [
    "Verify JWT token generation and validation",
    "Test input validation with malicious payloads",
    "Validate API error response format consistency",
    "Test session timeout scenarios"
  ],
  "generated_at": "2024-01-01T12:00:00Z",
  "model_version": "gemini-1.5-pro"
}
```

#### GET /mr/{id}/reviewers
Get AI-suggested reviewers for the merge request.

**Path Parameters:**
- `id` (required): Merge request ID

**Response:**
```json
{
  "reviewers": [
    {
      "user_id": 101,
      "name": "jane.smith",
      "email": "jane.smith@company.com",
      "score": 0.85,
      "reason": "Has approved 5 of your MRs, 12 total interactions",
      "expertise": ["backend", "security"],
      "availability": "available"
    },
    {
      "user_id": 102,
      "name": "mike.johnson",
      "email": "mike.johnson@company.com",
      "score": 0.72,
      "reason": "Backend expert who specializes in API design",
      "expertise": ["backend", "api"],
      "availability": "busy"
    }
  ],
  "suggested_at": "2024-01-01T12:00:00Z"
}
```

#### GET /mr/{id}/risk
Get detailed risk analysis for the merge request.

**Path Parameters:**
- `id` (required): Merge request ID

**Response:**
```json
{
  "score": 45,
  "band": "Medium",
  "reasons": [
    "2 approvals remaining",
    "MR age: 24.5 hours",
    "Medium size change"
  ],
  "features": {
    "age_hours": 24.5,
    "notes_count_24h": 3,
    "last_pipeline_status_is_fail": false,
    "approvals_left": 1,
    "change_size_bucket": "M",
    "work_in_progress": false,
    "labels_sensitive": false
  },
  "calculated_at": "2024-01-01T12:00:00Z"
}
```

#### GET /mr/{id}/stats
Get detailed statistics for the merge request.

**Path Parameters:**
- `id` (required): Merge request ID

**Response:**
```json
{
  "mr_id": 123,
  "total_notes": 15,
  "total_approvals": 2,
  "total_reviews": 8,
  "total_comments": 5,
  "cycle_time_hours": 48.5,
  "last_activity": "2024-01-01T11:30:00Z",
  "activity_breakdown": {
    "notes_24h": 3,
    "notes_7d": 12,
    "notes_30d": 15
  },
  "approval_history": [
    {
      "user_id": 101,
      "name": "jane.smith",
      "approved_at": "2024-01-01T10:00:00Z"
    }
  ],
  "review_history": [
    {
      "user_id": 102,
      "name": "mike.johnson",
      "reviewed_at": "2024-01-01T09:00:00Z",
      "note_type": "review"
    }
  ]
}
```

### Metrics and Monitoring

#### GET /metrics
Get application metrics and performance data.

**Response:**
```json
{
  "uptime_seconds": 86400,
  "request_count": 1500,
  "error_count": 5,
  "error_rate": 0.003,
  "request_rate_per_second": 0.017,
  "avg_duration_ms": 250.5,
  "p50_duration_ms": 180.0,
  "p95_duration_ms": 800.0,
  "p99_duration_ms": 1500.0,
  "top_endpoints": [
    {
      "endpoint": "GET /mrs",
      "count": 450,
      "errors": 2,
      "avg_duration_ms": 200.0
    }
  ],
  "top_errors": [
    {
      "error_type": "ValidationError",
      "count": 3
    }
  ]
}
```

#### GET /metrics/slo
Get SLO (Service Level Objective) status and violations.

**Response:**
```json
{
  "status": "healthy",
  "violations": [],
  "summary": {
    "error_rate": 0.003,
    "p95_latency_ms": 800.0,
    "p99_latency_ms": 1500.0
  },
  "slo_targets": {
    "error_rate": 0.01,
    "p95_latency_ms": 2000.0,
    "p99_latency_ms": 5000.0
  }
}
```

#### POST /metrics/reset
Reset application metrics (admin only).

**Response:**
```json
{
  "message": "Metrics reset successfully",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Data Models

### MRListItem
```json
{
  "mr_id": 123,
  "project_id": 456,
  "title": "Add user authentication",
  "author": "john.doe",
  "age_hours": 24.5,
  "risk_band": "Medium",
  "risk_score": 45,
  "pipeline_status": "success",
  "approvals_left": 1,
  "notes_count_24h": 3,
  "additions": 150,
  "deletions": 20
}
```

### MRContext
```json
{
  "mr_id": 123,
  "project_id": 456,
  "title": "Add user authentication",
  "author": {
    "user_id": 789,
    "name": "john.doe",
    "email": "john.doe@company.com"
  },
  "state": "opened",
  "age_hours": 24.5,
  "risk": {
    "score": 45,
    "band": "Medium",
    "reasons": ["2 approvals remaining", "MR age: 24.5 hours"]
  },
  "last_pipeline": {
    "status": "success",
    "age_min": 30,
    "web_url": "https://gitlab.com/project/-/pipelines/12345"
  },
  "approvals_left": 1,
  "notes_recent": 3,
  "size": {
    "additions": 150,
    "deletions": 20,
    "files_changed": 8
  },
  "labels": ["frontend", "security"],
  "web_url": "https://gitlab.com/project/merge_requests/123",
  "source_branch": "feature/auth",
  "target_branch": "main",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T11:30:00Z"
}
```

### MRSummary
```json
{
  "summary": [
    "Refactors user authentication to use JWT tokens",
    "Adds input validation for email and password fields",
    "Updates API endpoints to return consistent error responses"
  ],
  "risks": [
    "JWT token expiration handling may cause user session issues",
    "Input validation bypass could allow SQL injection"
  ],
  "tests": [
    "Verify JWT token generation and validation",
    "Test input validation with malicious payloads",
    "Validate API error response format consistency"
  ],
  "generated_at": "2024-01-01T12:00:00Z",
  "model_version": "gemini-1.5-pro"
}
```

### Reviewer
```json
{
  "user_id": 101,
  "name": "jane.smith",
  "email": "jane.smith@company.com",
  "score": 0.85,
  "reason": "Has approved 5 of your MRs, 12 total interactions",
  "expertise": ["backend", "security"],
  "availability": "available"
}
```

### RiskAnalysis
```json
{
  "score": 45,
  "band": "Medium",
  "reasons": [
    "2 approvals remaining",
    "MR age: 24.5 hours",
    "Medium size change"
  ],
  "features": {
    "age_hours": 24.5,
    "notes_count_24h": 3,
    "last_pipeline_status_is_fail": false,
    "approvals_left": 1,
    "change_size_bucket": "M",
    "work_in_progress": false,
    "labels_sensitive": false
  },
  "calculated_at": "2024-01-01T12:00:00Z"
}
```

## Examples

### List Open Merge Requests
```bash
curl "https://api.mergemind.com/api/v1/mrs?state=open&limit=20" \
  -H "Accept: application/json"
```

### Get MR Context
```bash
curl "https://api.mergemind.com/api/v1/mr/123/context" \
  -H "Accept: application/json"
```

### Generate AI Summary
```bash
curl -X POST "https://api.mergemind.com/api/v1/mr/123/summary" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json"
```

### Get Reviewer Suggestions
```bash
curl "https://api.mergemind.com/api/v1/mr/123/reviewers" \
  -H "Accept: application/json"
```

### Get Risk Analysis
```bash
curl "https://api.mergemind.com/api/v1/mr/123/risk" \
  -H "Accept: application/json"
```

### Get Top Blockers
```bash
curl "https://api.mergemind.com/api/v1/blockers/top?limit=5" \
  -H "Accept: application/json"
```

### Check Health
```bash
curl "https://api.mergemind.com/api/v1/healthz" \
  -H "Accept: application/json"
```

### Get Metrics
```bash
curl "https://api.mergemind.com/api/v1/metrics" \
  -H "Accept: application/json"
```

## SDKs

### Python SDK
```python
from mergemind import MergeMindClient

client = MergeMindClient(api_key="your-api-key")

# List MRs
mrs = client.mrs.list(state="open", limit=20)

# Get MR context
context = client.mrs.get_context(123)

# Generate summary
summary = client.mrs.generate_summary(123)

# Get reviewers
reviewers = client.mrs.get_reviewers(123)

# Get risk analysis
risk = client.mrs.get_risk(123)
```

### JavaScript SDK
```javascript
import { MergeMindClient } from '@mergemind/sdk';

const client = new MergeMindClient({ apiKey: 'your-api-key' });

// List MRs
const mrs = await client.mrs.list({ state: 'open', limit: 20 });

// Get MR context
const context = await client.mrs.getContext(123);

// Generate summary
const summary = await client.mrs.generateSummary(123);

// Get reviewers
const reviewers = await client.mrs.getReviewers(123);

// Get risk analysis
const risk = await client.mrs.getRisk(123);
```

### Go SDK
```go
package main

import (
    "fmt"
    "github.com/mergemind/go-sdk"
)

func main() {
    client := mergemind.NewClient("your-api-key")
    
    // List MRs
    mrs, err := client.MRs.List(&mergemind.MRListOptions{
        State: "open",
        Limit: 20,
    })
    if err != nil {
        panic(err)
    }
    
    // Get MR context
    context, err := client.MRs.GetContext(123)
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("MR: %s\n", context.Title)
}
```

## Webhooks (Future)

Webhook support will be added in future versions for real-time updates:

```json
{
  "event": "mr.updated",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "mr_id": 123,
    "project_id": 456,
    "changes": {
      "state": {
        "old": "opened",
        "new": "merged"
      }
    }
  }
}
```

## Changelog

### v1.0.0 (2024-01-01)
- Initial API release
- Basic MR analysis endpoints
- AI-powered summaries and reviewer suggestions
- Risk scoring and analysis
- Health check and metrics endpoints

### v1.1.0 (Planned)
- Authentication support
- Webhook notifications
- Bulk operations
- Advanced filtering and search
- Real-time updates

This API reference provides comprehensive documentation for all MergeMind API endpoints with detailed examples and SDK usage.
