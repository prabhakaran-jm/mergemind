# MergeMind

AI-powered GitLab merge request analysis and reviewer suggestions.

## Overview

MergeMind is an intelligent system that analyzes GitLab merge requests to provide risk scoring, AI-generated summaries, reviewer suggestions, and actionable insights. Built with modern cloud technologies and designed for scalability.

## Architecture

```
GitLab → Fivetran → BigQuery → dbt → Vertex AI → FastAPI → React/Slack
```

## Features

- **Risk Scoring**: Deterministic risk analysis based on MR characteristics
- **AI Summaries**: Vertex AI-powered diff analysis with risk identification
- **Reviewer Suggestions**: Co-review graph-based reviewer recommendations
- **Real-time Insights**: Live MR monitoring with blocking issue detection
- **Slack Integration**: Rich slash commands for MR analysis
- **Observability**: Comprehensive logging, metrics, and SLO monitoring

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud SDK
- Docker
- GitLab account with API access

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/prabhakaran-jm/mergemind.git
cd mergemind
```

2. Copy environment configuration:
```bash
cp ops/env/env.example .env
```

3. Configure environment variables in `.env`:
```bash
# Required
GCP_PROJECT_ID=your-project-id
GITLAB_TOKEN=your-gitlab-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Optional
BQ_DATASET_RAW=mergemind_raw
BQ_DATASET_MODELED=mergemind
VERTEX_LOCATION=europe-west2
```

### Development

1. **Seed demo data**:
```bash
make seed
```

2. **Start API server**:
```bash
make dev.api
```

3. **Start UI server** (in another terminal):
```bash
make dev.ui
```

4. **Run dbt models**:
```bash
make dbt.run
make dbt.test
```

### Testing

Test the API endpoints:
```bash
# Health check
curl http://localhost:8080/api/v1/healthz

# List MRs
curl http://localhost:8080/api/v1/mrs

# Get MR context
curl http://localhost:8080/api/v1/mr/1/context

# Generate summary
curl -X POST http://localhost:8080/api/v1/mr/1/summary

# Get reviewers
curl http://localhost:8080/api/v1/mr/1/reviewers
```

## Project Structure

```
mergemind/
├── api/fastapi_app/          # FastAPI application
├── ai/                       # AI services (scoring, reviewers, summarizer)
├── bots/slack/               # Slack bot implementation
├── docs/                     # Documentation and prompts
├── infra/cloudrun/           # Cloud Run configurations
├── ops/                      # Operations scripts and configs
├── ui/web/                   # React frontend
└── warehouse/bigquery/dbt/   # dbt models and configurations
```

## API Endpoints

### Health & Monitoring
- `GET /api/v1/healthz` - Basic health check
- `GET /api/v1/ready` - Readiness check
- `GET /api/v1/health/detailed` - Detailed health with metrics
- `GET /api/v1/metrics` - Application metrics
- `GET /api/v1/metrics/slo` - SLO violation status

### Merge Requests
- `GET /api/v1/mrs` - List MRs with risk badges
- `GET /api/v1/mr/{id}/context` - Get MR context
- `POST /api/v1/mr/{id}/summary` - Generate AI summary
- `GET /api/v1/mr/{id}/reviewers` - Get reviewer suggestions
- `GET /api/v1/mr/{id}/risk` - Get risk analysis
- `GET /api/v1/blockers/top` - Get top blocking MRs

## Slack Commands

- `/mergemind mr <id>` - Get MR insights
- `/mergemind-stats` - View statistics
- `/mergemind-blockers` - List blocking MRs
- `/mergemind-help` - Show help

## Deployment

### Cloud Run Deployment

1. **Deploy API**:
```bash
make deploy.api
```

2. **Deploy UI**:
```bash
make deploy.ui
```

3. **Deploy Slack Bot**:
```bash
make deploy.bot
```

4. **Deploy all services**:
```bash
make deploy.all
```

### Configuration

Update environment variables:
```bash
gcloud run services update mergemind-api --region=europe-west2 --update-env-vars KEY=VALUE
```

Update secrets:
```bash
gcloud run services update mergemind-api --region=europe-west2 --update-secrets KEY=SECRET_NAME:VERSION
```

## Development Commands

```bash
# Development
make dev.api          # Start API server
make dev.ui           # Start UI server

# dbt operations
make dbt.deps         # Install dbt packages
make dbt.run          # Run dbt models
make dbt.test         # Test dbt models
make dbt.compile      # Compile dbt models

# Data operations
make seed             # Seed demo data

# Deployment
make deploy.api       # Deploy API
make deploy.ui        # Deploy UI
make deploy.bot       # Deploy Slack bot
make deploy.all       # Deploy all services

# Cleanup
make clean            # Clean build artifacts
```

## Observability

### Logging
- Structured JSON logging with request IDs
- Request/response timing and status codes
- Error tracking and categorization

### Metrics
- Request count and error rates
- Latency percentiles (P50, P95, P99)
- Endpoint-specific performance metrics
- SLO violation detection

### Health Checks
- Basic health check (`/healthz`)
- Readiness check (`/ready`)
- Detailed health with dependencies (`/health/detailed`)

## SLOs (Service Level Objectives)

- **Error Rate**: < 1%
- **P95 Latency**: < 2 seconds
- **P99 Latency**: < 5 seconds
- **Availability**: > 99.9%

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check the [documentation](docs/)
- Review the [operations guide](docs/ops-observability.md)

## Roadmap

- [ ] Fine-tuned AI models for MR analysis
- [ ] Time-to-merge forecasting
- [ ] Flaky test detection
- [ ] Policy linting and security scanning
- [ ] Advanced analytics and reporting
- [ ] Multi-repository support
- [ ] Custom risk scoring rules
- [ ] Integration with other Git platforms
