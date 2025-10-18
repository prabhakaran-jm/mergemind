# MergeMind Deployment Guide

This guide covers deploying the MergeMind system to production, including infrastructure setup, configuration, monitoring, and maintenance.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Application Deployment](#application-deployment)
4. [Configuration](#configuration)
5. [Monitoring & Observability](#monitoring--observability)
6. [Security](#security)
7. [Scaling & Performance](#scaling--performance)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Services
- **Google Cloud Platform** account with billing enabled
- **GitLab** instance (self-hosted or GitLab.com)
- **Fivetran** account for data ingestion
- **BigQuery** dataset for data storage
- **Vertex AI** access for AI services

### Required Tools
- **Terraform** >= 1.5.0
- **Google Cloud SDK** >= 400.0.0
- **Docker** >= 20.10.0
- **kubectl** >= 1.24.0 (for Kubernetes deployment)
- **Python** >= 3.11
- **Node.js** >= 18.0.0

### Permissions
- GCP Project Owner or Editor
- GitLab Admin access
- Fivetran Admin access
- DNS management access (for custom domains)

## Infrastructure Setup

### 1. GCP Project Setup

```bash
# Create new GCP project
gcloud projects create mergemind-prod --name="MergeMind Production"

# Set project
gcloud config set project mergemind-prod

# Enable required APIs
gcloud services enable \
  compute.googleapis.com \
  container.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  cloudrun.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

### 2. Service Account Setup

```bash
# Create service account
gcloud iam service-accounts create mergemind-api \
  --display-name="MergeMind API Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding mergemind-prod \
  --member="serviceAccount:mergemind-api@mergemind-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding mergemind-prod \
  --member="serviceAccount:mergemind-api@mergemind-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding mergemind-prod \
  --member="serviceAccount:mergemind-api@mergemind-prod.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create mergemind-api-key.json \
  --iam-account=mergemind-api@mergemind-prod.iam.gserviceaccount.com
```

### 3. BigQuery Setup

```bash
# Create datasets
bq mk --location=us-central1 mergemind_raw
bq mk --location=us-central1 mergemind

# Set up table schemas
bq mk --table \
  --schema=schemas/merge_requests.json \
  mergemind_raw:merge_requests

bq mk --table \
  --schema=schemas/mr_notes.json \
  mergemind_raw:mr_notes

bq mk --table \
  --schema=schemas/users.json \
  mergemind_raw:users

bq mk --table \
  --schema=schemas/projects.json \
  mergemind_raw:projects

bq mk --table \
  --schema=schemas/pipelines.json \
  mergemind_raw:pipelines
```

### 4. Vertex AI Setup

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Set up Vertex AI location
gcloud config set ai/region us-central1
```

## Application Deployment

### Option 1: Google Cloud Run (Recommended)

#### 1. Build and Push Docker Image

```bash
# Build API image
cd app/backend/fastapi_app
docker build -t gcr.io/mergemind-prod/mergemind-api:latest .

# Push to registry
docker push gcr.io/mergemind-prod/mergemind-api:latest

# Build UI image
cd ../../frontend/web
docker build -t gcr.io/mergemind-prod/mergemind-ui:latest .

# Push to registry
docker push gcr.io/mergemind-prod/mergemind-ui:latest
```

#### 2. Deploy to Cloud Run

```bash
# Deploy API
gcloud run deploy mergemind-api \
  --image gcr.io/mergemind-prod/mergemind-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars GCP_PROJECT_ID=mergemind-prod

# Deploy UI
gcloud run deploy mergemind-ui \
  --image gcr.io/mergemind-prod/mergemind-ui:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5
```

### Option 2: Kubernetes (Advanced)

#### 1. Create Cluster

```bash
# Create GKE cluster
gcloud container clusters create mergemind-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-standard-4 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade

# Get credentials
gcloud container clusters get-credentials mergemind-cluster --zone us-central1-a
```

#### 2. Deploy with Helm

```bash
# Add Helm repository
helm repo add mergemind https://charts.mergemind.com
helm repo update

# Install application
helm install mergemind mergemind/mergemind \
  --set gcp.projectId=mergemind-prod \
  --set gitlab.baseUrl=https://your-gitlab.com \
  --set vertex.location=us-central1
```

### Option 3: Docker Compose (Development)

```bash
# Create production docker-compose
cat > docker-compose.prod.yml << EOF
version: '3.8'
services:
  api:
    image: gcr.io/mergemind-prod/mergemind-api:latest
    ports:
      - "8080:8080"
    environment:
      - GCP_PROJECT_ID=mergemind-prod
      - BQ_DATASET_RAW=mergemind_raw
      - BQ_DATASET_MODELED=mergemind
      - VERTEX_LOCATION=us-central1
    volumes:
      - ./mergemind-api-key.json:/app/mergemind-api-key.json:ro
    restart: unless-stopped

  ui:
    image: gcr.io/mergemind-prod/mergemind-ui:latest
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=https://api.mergemind.com
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
      - ui
    restart: unless-stopped
EOF

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration

### 1. Environment Variables

Create `.env.prod` file:

```bash
# GCP Configuration
GCP_PROJECT_ID=mergemind-prod
BQ_DATASET_RAW=mergemind_raw
BQ_DATASET_MODELED=mergemind
VERTEX_LOCATION=us-central1

# GitLab Configuration
GITLAB_BASE_URL=https://your-gitlab.com
GITLAB_TOKEN=glpat-your-token


# API Configuration
API_BASE_URL=https://api.mergemind.com
LOG_LEVEL=INFO
ENVIRONMENT=production

# Security
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=api.mergemind.com,mergemind.com

# Performance
MAX_WORKERS=4
WORKER_TIMEOUT=300
```

### 2. Secrets Management

```bash
# Store secrets in Google Secret Manager
gcloud secrets create gitlab-token --data-file=- <<< "glpat-your-token"

# Grant access to service account
gcloud secrets add-iam-policy-binding gitlab-token \
  --member="serviceAccount:mergemind-api@mergemind-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. DNS Configuration

```bash
# Point domain to Cloud Run
# For api.mergemind.com
gcloud run domain-mappings create \
  --service mergemind-api \
  --domain api.mergemind.com \
  --region us-central1

# For mergemind.com
gcloud run domain-mappings create \
  --service mergemind-ui \
  --domain mergemind.com \
  --region us-central1
```

## Monitoring & Observability

### 1. Cloud Monitoring Setup

```bash
# Enable monitoring
gcloud services enable monitoring.googleapis.com

# Create notification channels
gcloud alpha monitoring channels create \
  --display-name="Email Alerts" \
  --type=email \
  --channel-labels=email_address=admin@mergemind.com

# Create alerting policies
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring/alert-policies.yaml
```

### 2. Logging Configuration

```bash
# Set up log sinks
gcloud logging sinks create mergemind-logs \
  bigquery.googleapis.com/projects/mergemind-prod/datasets/mergemind_logs \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="mergemind-api"'
```

### 3. Custom Metrics

```python
# Example custom metrics in application
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter('mergemind_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('mergemind_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('mergemind_active_connections', 'Active connections')

# Business metrics
MR_ANALYSIS_COUNT = Counter('mergemind_mr_analysis_total', 'Total MR analyses')
AI_SUMMARY_COUNT = Counter('mergemind_ai_summary_total', 'Total AI summaries')
REVIEWER_SUGGESTIONS_COUNT = Counter('mergemind_reviewer_suggestions_total', 'Total reviewer suggestions')
```

## Security

### 1. Network Security

```bash
# Create VPC with private subnets
gcloud compute networks create mergemind-vpc \
  --subnet-mode custom

gcloud compute networks subnets create mergemind-private \
  --network mergemind-vpc \
  --range 10.0.1.0/24 \
  --region us-central1 \
  --enable-private-ip-google-access

# Create firewall rules
gcloud compute firewall-rules create allow-internal \
  --network mergemind-vpc \
  --allow tcp,udp,icmp \
  --source-ranges 10.0.0.0/8

gcloud compute firewall-rules create allow-https \
  --network mergemind-vpc \
  --allow tcp:443 \
  --source-ranges 0.0.0.0/0
```

### 2. SSL/TLS Configuration

```bash
# Create SSL certificate
gcloud compute ssl-certificates create mergemind-ssl \
  --domains=mergemind.com,api.mergemind.com \
  --global

# Configure HTTPS load balancer
gcloud compute backend-services create mergemind-backend \
  --global \
  --protocol HTTP \
  --health-checks mergemind-health-check

gcloud compute url-maps create mergemind-url-map \
  --default-service mergemind-backend

gcloud compute target-https-proxies create mergemind-https-proxy \
  --url-map mergemind-url-map \
  --ssl-certificates mergemind-ssl
```

### 3. Access Control

```bash
# Create IAM roles
gcloud iam roles create mergemindViewer \
  --project mergemind-prod \
  --title "MergeMind Viewer" \
  --description "Read-only access to MergeMind data" \
  --permissions bigquery.datasets.get,bigquery.tables.get,bigquery.tables.list

# Create service account for external access
gcloud iam service-accounts create mergemind-external \
  --display-name="MergeMind External Access"

# Grant minimal permissions
gcloud projects add-iam-policy-binding mergemind-prod \
  --member="serviceAccount:mergemind-external@mergemind-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

## Scaling & Performance

### 1. Auto-scaling Configuration

```yaml
# Cloud Run auto-scaling
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mergemind-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "100"
        autoscaling.knative.dev/target: "100"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/mergemind-prod/mergemind-api:latest
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
          requests:
            cpu: "1"
            memory: "1Gi"
```

### 2. Caching Strategy

```python
# Redis caching configuration
import redis
from functools import wraps

redis_client = redis.Redis(
    host='redis.mergemind.com',
    port=6379,
    db=0,
    decode_responses=True
)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage
@cache_result(expiration=600)  # 10 minutes
def get_mr_context(mr_id: int):
    # Expensive operation
    pass
```

### 3. Database Optimization

```sql
-- BigQuery table partitioning
CREATE TABLE `mergemind_raw.merge_requests` (
  mr_id INT64,
  project_id INT64,
  title STRING,
  created_at TIMESTAMP,
  -- other columns
)
PARTITION BY DATE(created_at)
CLUSTER BY project_id, mr_id;

-- Create materialized views for common queries
CREATE MATERIALIZED VIEW `mergemind.mr_activity_view`
PARTITION BY DATE(created_at)
CLUSTER BY project_id, mr_id
AS
SELECT
  mr_id,
  project_id,
  title,
  author_id,
  created_at,
  state,
  age_hours,
  notes_count_24h,
  approvals_left,
  additions,
  deletions
FROM `mergemind_raw.merge_requests`
WHERE state = 'opened';
```

## Maintenance

### 1. Backup Strategy

```bash
# BigQuery table backups
bq cp mergemind_raw:merge_requests mergemind_backup:merge_requests_$(date +%Y%m%d)

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
TABLES=("merge_requests" "mr_notes" "users" "projects" "pipelines")

for table in "${TABLES[@]}"; do
  bq cp "mergemind_raw:${table}" "mergemind_backup:${table}_${DATE}"
done

# Schedule with cron
# 0 2 * * * /path/to/backup_script.sh
```

### 2. Health Checks

```python
# Comprehensive health check endpoint
@app.get("/api/v1/health/detailed")
async def detailed_health():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "metrics": {}
    }
    
    # Check BigQuery
    try:
        bq_healthy = bigquery_client.test_connection()
        health_status["services"]["bigquery"] = {
            "status": "healthy" if bq_healthy else "unhealthy",
            "response_time_ms": 0
        }
    except Exception as e:
        health_status["services"]["bigquery"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check GitLab
    try:
        gitlab_healthy = gitlab_client.test_connection()
        health_status["services"]["gitlab"] = {
            "status": "healthy" if gitlab_healthy else "unhealthy",
            "response_time_ms": 0
        }
    except Exception as e:
        health_status["services"]["gitlab"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Vertex AI
    try:
        vertex_healthy = vertex_client.test_connection()
        health_status["services"]["vertex"] = {
            "status": "healthy" if vertex_healthy else "unhealthy",
            "response_time_ms": 0
        }
    except Exception as e:
        health_status["services"]["vertex"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Get metrics
    health_status["metrics"] = metrics_service.get_summary()
    
    # Determine overall status
    unhealthy_services = [
        service for service, status in health_status["services"].items()
        if status["status"] == "unhealthy"
    ]
    
    if unhealthy_services:
        health_status["status"] = "degraded"
        health_status["unhealthy_services"] = unhealthy_services
    
    return health_status
```

### 3. Update Procedures

```bash
# Rolling update script
#!/bin/bash
set -e

NEW_VERSION=$1
if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "Deploying version $NEW_VERSION"

# Build new image
docker build -t gcr.io/mergemind-prod/mergemind-api:$NEW_VERSION .
docker push gcr.io/mergemind-prod/mergemind-api:$NEW_VERSION

# Update Cloud Run service
gcloud run services update mergemind-api \
  --image gcr.io/mergemind-prod/mergemind-api:$NEW_VERSION \
  --region us-central1

# Wait for deployment
echo "Waiting for deployment to complete..."
sleep 30

# Health check
curl -f https://api.mergemind.com/api/v1/healthz || {
    echo "Health check failed, rolling back..."
    gcloud run services update mergemind-api \
      --image gcr.io/mergemind-prod/mergemind-api:previous \
      --region us-central1
    exit 1
}

echo "Deployment successful!"
```

## Troubleshooting

### Common Issues

#### 1. BigQuery Connection Issues

```bash
# Check service account permissions
gcloud projects get-iam-policy mergemind-prod \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:mergemind-api@mergemind-prod.iam.gserviceaccount.com"

# Test BigQuery access
bq query --use_legacy_sql=false "SELECT 1 as test"
```

#### 2. GitLab API Issues

```bash
# Test GitLab API access
curl -H "Authorization: Bearer $GITLAB_TOKEN" \
  "https://your-gitlab.com/api/v4/user"

# Check rate limits
curl -I -H "Authorization: Bearer $GITLAB_TOKEN" \
  "https://your-gitlab.com/api/v4/user"
```

#### 3. Vertex AI Issues

```bash
# Check Vertex AI access
gcloud ai models list --region=us-central1

# Test text generation
gcloud ai models predict gemini-2.5-flash-lite \
  --region=us-central1 \
  --json-request='{"instances": [{"prompt": "Hello world"}]}'
```

### Monitoring Commands

```bash
# Check Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=mergemind-api" \
  --limit=50 --format="table(timestamp,severity,textPayload)"

# Check BigQuery usage
bq query --use_legacy_sql=false "
SELECT
  job_id,
  creation_time,
  total_bytes_processed,
  total_slot_ms
FROM \`mergemind-prod.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT\`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY creation_time DESC
"

# Check Vertex AI usage
gcloud logging read "resource.type=aiplatform.googleapis.com/Endpoint" \
  --limit=20 --format="table(timestamp,severity,textPayload)"
```

### Performance Tuning

```python
# Connection pooling for BigQuery
from google.cloud import bigquery
from concurrent.futures import ThreadPoolExecutor

class OptimizedBigQueryClient:
    def __init__(self, max_workers=10):
        self.client = bigquery.Client()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def query_async(self, sql, **params):
        return self.executor.submit(self._execute_query, sql, params)
    
    def _execute_query(self, sql, params):
        # Optimized query execution
        pass

# Caching frequently accessed data
@cache_result(expiration=3600)  # 1 hour
def get_user_info(user_id: int):
    # Expensive user lookup
    pass

# Batch processing for multiple MRs
def batch_analyze_mrs(mr_ids: List[int]):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(analyze_mr, mr_id) for mr_id in mr_ids]
        results = [future.result() for future in futures]
    return results
```

## Cost Optimization

### 1. Resource Optimization

```yaml
# Optimized Cloud Run configuration
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mergemind-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"  # Scale to zero when idle
        autoscaling.knative.dev/maxScale: "20"  # Limit max instances
        autoscaling.knative.dev/target: "80"   # Scale at 80% utilization
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/mergemind-prod/mergemind-api:latest
        resources:
          limits:
            cpu: "1"      # Reduced from 2
            memory: "1Gi" # Reduced from 2Gi
          requests:
            cpu: "0.5"    # Reduced from 1
            memory: "512Mi" # Reduced from 1Gi
```

### 2. BigQuery Cost Optimization

```sql
-- Use partitioned tables
CREATE TABLE `mergemind_raw.merge_requests` (
  mr_id INT64,
  project_id INT64,
  title STRING,
  created_at TIMESTAMP
)
PARTITION BY DATE(created_at)
CLUSTER BY project_id, mr_id;

-- Use materialized views for common queries
CREATE MATERIALIZED VIEW `mergemind.mr_summary_view`
PARTITION BY DATE(created_at)
AS
SELECT
  mr_id,
  project_id,
  title,
  state,
  created_at,
  age_hours,
  approvals_left
FROM `mergemind_raw.merge_requests`
WHERE state = 'opened';

-- Set up automatic table expiration
ALTER TABLE `mergemind_raw.merge_requests`
SET OPTIONS (
  partition_expiration_days=90,
  description="Merge requests with 90-day partition expiration"
);
```

### 3. Monitoring Costs

```bash
# Set up billing alerts
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="MergeMind Budget" \
  --budget-amount=1000 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100

# Monitor BigQuery costs
bq query --use_legacy_sql=false "
SELECT
  project_id,
  SUM(total_bytes_processed) as total_bytes,
  SUM(total_bytes_processed) / 1024 / 1024 / 1024 * 5 as estimated_cost_usd
FROM \`mergemind-prod.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT\`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY project_id
ORDER BY estimated_cost_usd DESC
"
```

This deployment guide provides comprehensive instructions for deploying MergeMind to production with proper monitoring, security, and cost optimization.
