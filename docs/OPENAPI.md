# MergeMind API OpenAPI Specification

## Overview
The MergeMind API provides AI-powered analysis and insights for GitLab merge requests, including risk scoring, reviewer suggestions, and automated summaries.

## Base URL
- Development: `http://localhost:8080/api/v1`
- Production: `https://api.mergemind.com/api/v1`

## Authentication
Currently no authentication required for MVP. Future versions will support API keys and OAuth.

## Rate Limiting
- 10 requests per minute per IP address
- Rate limit headers included in responses

## Error Handling
All errors return JSON with the following structure:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Endpoints

### Health Check
- **GET** `/healthz` - Basic health check
- **GET** `/ready` - Readiness check with dependency validation

### Merge Requests List
- **GET** `/mrs` - List merge requests with risk badges
- **GET** `/blockers/top` - Get top blocking merge requests

### Individual Merge Request
- **GET** `/mr/{id}/context` - Get comprehensive MR context
- **POST** `/mr/{id}/summary` - Generate AI summary
- **GET** `/mr/{id}/reviewers` - Get suggested reviewers
- **GET** `/mr/{id}/risk` - Get risk analysis
- **GET** `/mr/{id}/stats` - Get MR statistics

## Response Schemas

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
    "name": "john.doe"
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
    "age_min": 30
  },
  "approvals_left": 1,
  "notes_recent": 3,
  "size": {
    "additions": 150,
    "deletions": 20
  },
  "labels": ["frontend", "security"],
  "web_url": "https://gitlab.com/project/merge_requests/123",
  "source_branch": "feature/auth",
  "target_branch": "main"
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
  ]
}
```

### Reviewers
```json
{
  "reviewers": [
    {
      "user_id": 101,
      "name": "jane.smith",
      "score": 0.85,
      "reason": "Has approved 5 of your MRs, 12 total interactions"
    },
    {
      "user_id": 102,
      "name": "mike.johnson",
      "score": 0.72,
      "reason": "Backend expert who specializes in API design"
    }
  ]
}
```

## Query Parameters

### List Merge Requests
- `state` (optional): Filter by state (`open`, `merged`, `closed`)
- `project_id` (optional): Filter by project ID
- `limit` (optional): Maximum results (default: 50, max: 200)
- `cursor` (optional): Pagination cursor

### Top Blockers
- `limit` (optional): Maximum results (default: 10, max: 50)

## Status Codes
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

## Examples

### List Open Merge Requests
```bash
curl "http://localhost:8080/api/v1/mrs?state=open&limit=20"
```

### Get MR Context
```bash
curl "http://localhost:8080/api/v1/mr/123/context"
```

### Generate Summary
```bash
curl -X POST "http://localhost:8080/api/v1/mr/123/summary"
```

### Get Reviewers
```bash
curl "http://localhost:8080/api/v1/mr/123/reviewers"
```

## Future Enhancements
- Authentication and authorization
- Webhook support for real-time updates
- Bulk operations
- Advanced filtering and search
- Metrics and analytics endpoints
