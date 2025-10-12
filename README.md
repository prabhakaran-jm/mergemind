# MergeMind

AI-powered merge request analysis and insights platform for GitLab, providing risk scoring, reviewer suggestions, and automated summaries.

## 🚀 Features

- **AI-Powered Analysis**: Automated diff summarization using Vertex AI Gemini 1.5
- **Risk Scoring**: Deterministic risk assessment for merge requests
- **Reviewer Suggestions**: Intelligent reviewer recommendations based on co-review graph
- **Real-time Insights**: Live MR analysis with risk badges and blocking detection
- **Slack Integration**: Interactive Slack bot for MR analysis and notifications
- **Comprehensive API**: RESTful API for all MR analysis features
- **Modern UI**: React-based dashboard for MR management and analytics

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## 🏃‍♂️ Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud Platform account
- GitLab instance (self-hosted or GitLab.com)
- Fivetran account (for data ingestion)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/mergemind/mergemind.git
   cd mergemind
   ```

2. **Set up environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit configuration
   nano .env
   ```

3. **Install dependencies**
   ```bash
   # Install API dependencies
   cd api/fastapi_app
   pip install -r requirements.txt
   
   # Install UI dependencies
   cd ../../ui/react_app
   npm install
   ```

4. **Start services**
   ```bash
   # Start API (terminal 1)
   cd api/fastapi_app
   uvicorn main:app --reload --port 8080
   
   # Start UI (terminal 2)
   cd ui/react_app
   npm run dev
   ```

5. **Access the application**
   - API: http://localhost:8080
   - UI: http://localhost:5173
   - API Docs: http://localhost:8080/docs

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        GL[GitLab API]
        FV[Fivetran Connector]
    end
    
    subgraph "Data Layer"
        BQ[BigQuery]
        dbt[dbt Models]
    end
    
    subgraph "AI Services"
        VAI[Vertex AI]
        RS[Reviewer Service]
        RISK[Risk Service]
        SUM[Summary Service]
    end
    
    subgraph "API Layer"
        API[FastAPI]
        AUTH[Authentication]
        RATE[Rate Limiting]
    end
    
    subgraph "Frontend"
        UI[React App]
        DASH[Dashboard]
        BOT[Slack Bot]
    end
    
    subgraph "Infrastructure"
        GCP[Google Cloud]
        RUN[Cloud Run]
        LB[Load Balancer]
    end
    
    GL --> FV
    FV --> BQ
    BQ --> dbt
    dbt --> API
    API --> VAI
    API --> RS
    API --> RISK
    API --> SUM
    API --> UI
    API --> BOT
    UI --> DASH
    API --> RUN
    RUN --> LB
    LB --> GCP
```

### Core Components

- **Data Ingestion**: Fivetran custom connector for GitLab data
- **Data Warehouse**: BigQuery with dbt for data modeling
- **AI Services**: Vertex AI for diff summarization and analysis
- **API Layer**: FastAPI with comprehensive endpoints
- **Frontend**: React dashboard for MR management
- **Slack Integration**: Interactive bot for team collaboration

## 📦 Installation

### Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/mergemind/mergemind.git
cd mergemind

# Copy environment file
cp .env.example .env

# Edit configuration
nano .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Manual Installation

#### 1. API Setup

```bash
cd api/fastapi_app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python run_tests.py

# Start development server
uvicorn main:app --reload --port 8080
```

#### 2. UI Setup

```bash
cd ui/react_app

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

#### 3. Data Pipeline Setup

```bash
cd warehouse/bigquery/dbt

# Install dbt
pip install dbt-bigquery

# Install dbt packages
dbt deps

# Run models
dbt run

# Run tests
dbt test
```

## ⚙️ Configuration

### Environment Variables

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
BQ_DATASET_RAW=mergemind_raw
BQ_DATASET_MODELED=mergemind
VERTEX_LOCATION=us-central1

# GitLab Configuration
GITLAB_BASE_URL=https://your-gitlab.com
GITLAB_TOKEN=glpat-your-token

# Slack Configuration (Optional)
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_COMMAND=/mergemind

# API Configuration
API_BASE_URL=https://api.mergemind.com
LOG_LEVEL=INFO
ENVIRONMENT=production

# Security
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=api.mergemind.com,mergemind.com
```

### BigQuery Setup

```sql
-- Create datasets
CREATE SCHEMA `mergemind_raw`;
CREATE SCHEMA `mergemind`;

-- Create tables with schemas
CREATE TABLE `mergemind_raw.merge_requests` (
  mr_id INT64,
  project_id INT64,
  title STRING,
  description STRING,
  author_id INT64,
  state STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  additions INT64,
  deletions INT64,
  web_url STRING
);

CREATE TABLE `mergemind_raw.mr_notes` (
  id INT64,
  mr_id INT64,
  author_id INT64,
  note_type STRING,
  body STRING,
  created_at TIMESTAMP
);

CREATE TABLE `mergemind_raw.users` (
  user_id INT64,
  username STRING,
  name STRING,
  email STRING,
  state STRING,
  created_at TIMESTAMP
);

CREATE TABLE `mergemind_raw.projects` (
  project_id INT64,
  name STRING,
  description STRING,
  visibility STRING,
  created_at TIMESTAMP
);

CREATE TABLE `mergemind_raw.pipelines` (
  pipeline_id INT64,
  project_id INT64,
  status STRING,
  ref STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### dbt Models

```bash
cd warehouse/bigquery/dbt

# Install packages
dbt deps

# Run models
dbt run

# Test models
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

## 📚 API Documentation

### Base URL
- **Development**: `http://localhost:8080/api/v1`
- **Production**: `https://api.mergemind.com/api/v1`

### Authentication
Currently no authentication required for MVP. Future versions will support API keys and OAuth.

### Endpoints

#### Health Check
- `GET /healthz` - Basic health check
- `GET /ready` - Readiness check with dependency validation
- `GET /health/detailed` - Comprehensive health check with metrics

#### Merge Requests
- `GET /mrs` - List merge requests with risk analysis
- `GET /blockers/top` - Get top blocking merge requests

#### Individual MR
- `GET /mr/{id}/context` - Get comprehensive MR context
- `POST /mr/{id}/summary` - Generate AI summary
- `GET /mr/{id}/reviewers` - Get suggested reviewers
- `GET /mr/{id}/risk` - Get risk analysis
- `GET /mr/{id}/stats` - Get MR statistics

#### Metrics
- `GET /metrics` - Get application metrics
- `GET /metrics/slo` - Get SLO status and violations
- `POST /metrics/reset` - Reset metrics (admin only)

### Example Usage

```bash
# List open merge requests
curl "https://api.mergemind.com/api/v1/mrs?state=open&limit=20"

# Get MR context
curl "https://api.mergemind.com/api/v1/mr/123/context"

# Generate AI summary
curl -X POST "https://api.mergemind.com/api/v1/mr/123/summary"

# Get reviewer suggestions
curl "https://api.mergemind.com/api/v1/mr/123/reviewers"

# Get risk analysis
curl "https://api.mergemind.com/api/v1/mr/123/risk"
```

For complete API documentation, see [API Reference](docs/API_REFERENCE.md).

## 🚀 Deployment

### Google Cloud Run (Recommended)

```bash
# Build and push Docker images
docker build -t gcr.io/your-project/mergemind-api:latest api/fastapi_app/
docker push gcr.io/your-project/mergemind-api:latest

docker build -t gcr.io/your-project/mergemind-ui:latest ui/react_app/
docker push gcr.io/your-project/mergemind-ui:latest

# Deploy to Cloud Run
gcloud run deploy mergemind-api \
  --image gcr.io/your-project/mergemind-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10

gcloud run deploy mergemind-ui \
  --image gcr.io/your-project/mergemind-ui:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5
```

### Kubernetes

```bash
# Create cluster
gcloud container clusters create mergemind-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-standard-4

# Deploy with Helm
helm install mergemind ./helm/mergemind \
  --set gcp.projectId=your-project-id \
  --set gitlab.baseUrl=https://your-gitlab.com
```

For detailed deployment instructions, see [Deployment Guide](docs/DEPLOYMENT.md).

## 📊 Monitoring

### Health Checks

```bash
# Basic health check
curl "https://api.mergemind.com/api/v1/healthz"

# Detailed health check
curl "https://api.mergemind.com/api/v1/health/detailed"

# SLO status
curl "https://api.mergemind.com/api/v1/metrics/slo"
```

### Metrics

The application exposes Prometheus-compatible metrics:

- Request count and duration
- Error rates and types
- Business metrics (MR analysis, AI summaries)
- External service health

### Alerting

Configure alerts for:
- High error rates (>1%)
- High latency (P95 > 2s)
- Service downtime
- BigQuery quota exceeded
- AI service failures

For comprehensive monitoring setup, see [Monitoring Guide](docs/MONITORING.md).

## 🔒 Security

### Security Features

- Input validation and sanitization
- Rate limiting and DDoS protection
- HTTPS enforcement
- Security headers
- Data encryption at rest and in transit
- Access logging and audit trails

### Compliance

- GDPR compliance for data protection
- SOC 2 Type II compliance
- Security incident response plan
- Regular security audits

For detailed security information, see [Security Guide](docs/SECURITY.md).

## 🧪 Testing

### Run Tests

```bash
# API tests
cd api/fastapi_app
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration

# Run with coverage
python run_tests.py --coverage

# UI tests
cd ui/react_app
npm test
npm run test:coverage
```

### Test Coverage

- **Unit Tests**: Service layer components
- **Integration Tests**: End-to-end workflows
- **API Tests**: Endpoint functionality
- **Performance Tests**: Load and stress testing

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style

- Python: Black, isort, flake8
- JavaScript: Prettier, ESLint
- TypeScript: Strict mode enabled

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/mergemind/mergemind/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mergemind/mergemind/discussions)
- **Email**: support@mergemind.com

## 🗺️ Roadmap

### v1.1.0 (Q2 2024)
- Authentication and authorization
- Webhook notifications
- Bulk operations
- Advanced filtering and search

### v1.2.0 (Q3 2024)
- Real-time updates
- Advanced analytics
- Custom risk rules
- Team collaboration features

### v2.0.0 (Q4 2024)
- Multi-repository support
- Advanced AI models
- Enterprise features
- Self-hosted deployment

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [React](https://reactjs.org/) for the frontend framework
- [BigQuery](https://cloud.google.com/bigquery) for data warehousing
- [Vertex AI](https://cloud.google.com/vertex-ai) for AI services
- [Fivetran](https://fivetran.com/) for data ingestion

---

**MergeMind** - Making merge request analysis intelligent and efficient. 🚀