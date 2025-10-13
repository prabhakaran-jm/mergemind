# Production Configuration Guide

## Environment Variables

Create a `.env.production` file with the following configuration:

```bash
# Application
ENVIRONMENT=production
API_PORT=8080
UI_PORT=5173

# Google Cloud Platform
GCP_PROJECT_ID=ai-accelerate-mergemind
BQ_DATASET_RAW=gitlab_connector_v1
BQ_DATASET_MODELED=mergemind
VERTEX_LOCATION=us-central1

# GitLab Configuration
GITLAB_BASE_URL=https://35.202.37.189.sslip.io
# GITLAB_TOKEN should be set from GCP Secret Manager in production

# API Configuration
API_BASE_URL=https://your-domain.com
VITE_API_BASE_URL=https://your-domain.com

# Optional Services
LOG_LEVEL=INFO

# Security (set these in production)
# SENTRY_DSN=your-sentry-dsn
# REDIS_URL=your-redis-url
# DATABASE_URL=your-database-url
```

## GitLab Configuration

The GitLab base URL is now configured to point to your self-hosted instance:
- **URL**: `https://35.202.37.189.sslip.io`
- **Token**: Retrieved from GCP Secret Manager
- **API Version**: v4

## Deployment Steps

1. **Set environment variables** in your deployment environment
2. **Configure GCP Secret Manager** with GitLab token
3. **Deploy the application** with the updated configuration
4. **Test connectivity** to your GitLab instance

## Testing

Use the validation scripts to test the configuration:

```bash
# Test GitLab connectivity
python validation_scripts/test_gitlab_connectivity.py

# Test complete AI pipeline
python validation_scripts/test_complete_ai_pipeline.py
```
