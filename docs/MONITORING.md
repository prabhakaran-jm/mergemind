# MergeMind Monitoring & Alerting Guide

Comprehensive guide for monitoring the MergeMind system in production, including metrics collection, alerting, and observability best practices.

## Table of Contents

1. [Overview](#overview)
2. [Metrics Collection](#metrics-collection)
3. [Health Checks](#health-checks)
4. [Alerting](#alerting)
5. [Logging](#logging)
6. [Dashboards](#dashboards)
7. [SLO Monitoring](#slo-monitoring)
8. [Troubleshooting](#troubleshooting)

## Overview

MergeMind implements comprehensive monitoring across multiple layers:

- **Application Metrics**: Request rates, error rates, latency percentiles
- **Business Metrics**: MR analysis counts, AI summary generation, reviewer suggestions
- **Infrastructure Metrics**: CPU, memory, disk usage
- **External Dependencies**: BigQuery, GitLab, Vertex AI health
- **Event-Driven Pipeline**: Fivetran syncs, dbt runs, data freshness
- **SLO Monitoring**: Service level objectives and violations

## Metrics Collection

### Event-Driven Pipeline Metrics

The event-driven pipeline requires specific monitoring to ensure data freshness and transformation reliability:

```python
# Pipeline metrics
PIPELINE_SYNC_COUNT = Counter(
    'mergemind_pipeline_syncs_total',
    'Total Fivetran syncs',
    ['status', 'project_count']
)

DBT_RUN_COUNT = Counter(
    'mergemind_dbt_runs_total',
    'Total dbt runs',
    ['status', 'models_processed']
)

DBT_RUN_DURATION = Histogram(
    'mergemind_dbt_run_duration_seconds',
    'dbt run duration',
    ['status']
)

DATA_FRESHNESS = Gauge(
    'mergemind_data_freshness_minutes',
    'Data freshness in minutes',
    ['dataset', 'table']
)
```

#### Key Pipeline Metrics

- **Sync Frequency**: Monitor Fivetran sync intervals
- **dbt Run Success Rate**: Track successful vs failed transformations
- **Data Freshness**: Monitor time since last data update
- **Pipeline Latency**: End-to-end processing time
- **Error Rates**: Track failures in each pipeline component

### Application Metrics

The application exposes Prometheus-compatible metrics:

```python
# Request metrics
REQUEST_COUNT = Counter(
    'mergemind_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'mergemind_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

# Error metrics
ERROR_COUNT = Counter(
    'mergemind_errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Business metrics
MR_ANALYSIS_COUNT = Counter(
    'mergemind_mr_analysis_total',
    'Total MR analyses',
    ['analysis_type']
)

AI_SUMMARY_COUNT = Counter(
    'mergemind_ai_summary_total',
    'Total AI summaries generated'
)

REVIEWER_SUGGESTIONS_COUNT = Counter(
    'mergemind_reviewer_suggestions_total',
    'Total reviewer suggestions'
)

# External service metrics
BIGQUERY_QUERY_DURATION = Histogram(
    'mergemind_bigquery_query_duration_seconds',
    'BigQuery query duration'
)

GITLAB_API_DURATION = Histogram(
    'mergemind_gitlab_api_duration_seconds',
    'GitLab API call duration'
)

VERTEX_AI_DURATION = Histogram(
    'mergemind_vertex_ai_duration_seconds',
    'Vertex AI call duration'
)
```

### Infrastructure Metrics

Cloud Run automatically collects:
- CPU utilization
- Memory usage
- Request count
- Request latency
- Error rate

BigQuery metrics:
- Query execution time
- Bytes processed
- Slot usage
- Job failures

### Custom Business Metrics

```python
# MR analysis metrics
mr_analysis_duration = Histogram(
    'mergemind_mr_analysis_duration_seconds',
    'MR analysis duration',
    ['analysis_type']
)

# AI service metrics
ai_summary_tokens = Histogram(
    'mergemind_ai_summary_tokens',
    'AI summary token count'
)

# Reviewer suggestion metrics
reviewer_suggestion_score = Histogram(
    'mergemind_reviewer_suggestion_score',
    'Reviewer suggestion confidence score'
)

# Risk analysis metrics
risk_score_distribution = Histogram(
    'mergemind_risk_score',
    'Risk score distribution',
    ['risk_band']
)
```

## Health Checks

### Basic Health Check

```python
@app.get("/api/v1/healthz")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Readiness Check

```python
@app.get("/api/v1/ready")
async def readiness_check():
    """Readiness check with dependency validation."""
    services_status = {}
    overall_healthy = True
    
    # Check BigQuery
    try:
        bq_healthy = bigquery_client.test_connection()
        services_status["bigquery"] = "healthy" if bq_healthy else "unhealthy"
        if not bq_healthy:
            overall_healthy = False
    except Exception as e:
        services_status["bigquery"] = "unhealthy"
        overall_healthy = False
    
    # Check GitLab
    try:
        gitlab_healthy = gitlab_client.test_connection()
        services_status["gitlab"] = "healthy" if gitlab_healthy else "unhealthy"
        if not gitlab_healthy:
            overall_healthy = False
    except Exception as e:
        services_status["gitlab"] = "unhealthy"
        overall_healthy = False
    
    # Check Vertex AI
    try:
        vertex_healthy = vertex_client.test_connection()
        services_status["vertex"] = "healthy" if vertex_healthy else "unhealthy"
        if not vertex_healthy:
            overall_healthy = False
    except Exception as e:
        services_status["vertex"] = "unhealthy"
        overall_healthy = False
    
    status_code = 200 if overall_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall_healthy else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status
        }
    )
```

### Detailed Health Check

```python
@app.get("/api/v1/health/detailed")
async def detailed_health():
    """Comprehensive health check with metrics."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "metrics": {}
    }
    
    # Check each service with timing
    services = [
        ("bigquery", bigquery_client),
        ("gitlab", gitlab_client),
        ("vertex", vertex_client)
    ]
    
    for service_name, service_client in services:
        start_time = time.time()
        try:
            healthy = service_client.test_connection()
            response_time = (time.time() - start_time) * 1000
            
            health_status["services"][service_name] = {
                "status": "healthy" if healthy else "unhealthy",
                "response_time_ms": round(response_time, 2)
            }
            
            if not healthy:
                health_status["status"] = "degraded"
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            health_status["services"][service_name] = {
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # Get application metrics
    health_status["metrics"] = metrics_service.get_summary()
    
    return health_status
```

## Alerting

### Alert Policies

#### Critical Alerts

```yaml
# High error rate
alert: HighErrorRate
expr: rate(mergemind_errors_total[5m]) > 0.05
for: 2m
labels:
  severity: critical
annotations:
  summary: "High error rate detected"
  description: "Error rate is {{ $value }} errors per second"

# Service down
alert: ServiceDown
expr: up{job="mergemind-api"} == 0
for: 1m
labels:
  severity: critical
annotations:
  summary: "MergeMind API is down"
  description: "API service has been down for more than 1 minute"

# High latency
alert: HighLatency
expr: histogram_quantile(0.95, mergemind_request_duration_seconds_bucket) > 5
for: 5m
labels:
  severity: warning
annotations:
  summary: "High latency detected"
  description: "95th percentile latency is {{ $value }} seconds"
```

#### Warning Alerts

```yaml
# High CPU usage
alert: HighCPUUsage
expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
for: 5m
labels:
  severity: warning
annotations:
  summary: "High CPU usage"
  description: "CPU usage is {{ $value }}%"

# High memory usage
alert: HighMemoryUsage
expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
for: 5m
labels:
  severity: warning
annotations:
  summary: "High memory usage"
  description: "Memory usage is {{ $value }}%"

# BigQuery quota exceeded
alert: BigQueryQuotaExceeded
expr: rate(bigquery_job_total_bytes_processed[1h]) > 1000000000
for: 1m
labels:
  severity: warning
annotations:
  summary: "BigQuery quota exceeded"
  description: "BigQuery processing rate is {{ $value }} bytes/hour"
```

#### Business Alerts

```yaml
# Low MR analysis rate
alert: LowMRAnalysisRate
expr: rate(mergemind_mr_analysis_total[1h]) < 10
for: 30m
labels:
  severity: warning
annotations:
  summary: "Low MR analysis rate"
  description: "MR analysis rate is {{ $value }} per hour"

# AI service failures
alert: AIServiceFailures
expr: rate(mergemind_ai_summary_total{status="error"}[5m]) > 0.1
for: 2m
labels:
  severity: warning
annotations:
  summary: "AI service failures"
  description: "AI summary failure rate is {{ $value }} per second"
```

### Notification Channels

```yaml
# Email notifications
- name: email-alerts
  type: email
  config:
    to: admin@mergemind.com
    subject: "MergeMind Alert: {{ .GroupLabels.alertname }}"
    body: |
      Alert: {{ .GroupLabels.alertname }}
      Status: {{ .Status }}
      Description: {{ .Annotations.description }}
      Time: {{ .StartsAt }}

# Email notifications
- name: email-alerts
  type: email
  config:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    channel: "#alerts"
    title: "MergeMind Alert"
    text: |
      *Alert:* {{ .GroupLabels.alertname }}
      *Status:* {{ .Status }}
      *Description:* {{ .Annotations.description }}
      *Time:* {{ .StartsAt }}

# PagerDuty notifications
- name: pagerduty-alerts
  type: pagerduty
  config:
    service_key: "your-service-key"
    description: "{{ .GroupLabels.alertname }}: {{ .Annotations.description }}"
```

## Logging

### Structured Logging

```python
import structlog
import logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage examples
logger.info("MR analysis started", mr_id=123, project_id=456)
logger.error("BigQuery query failed", error=str(e), query=sql)
logger.warning("High latency detected", duration=5.2, endpoint="/mrs")
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened but the application continues
- **ERROR**: An error occurred but the application can continue
- **CRITICAL**: A serious error occurred and the application may not continue

### Log Aggregation

```yaml
# Fluentd configuration for log aggregation
<source>
  @type tail
  path /var/log/mergemind/*.log
  pos_file /var/log/fluentd/mergemind.log.pos
  tag mergemind.*
  format json
</source>

<match mergemind.**>
  @type elasticsearch
  host elasticsearch.mergemind.com
  port 9200
  index_name mergemind
  type_name _doc
</match>
```

## Dashboards

### Application Dashboard

```json
{
  "dashboard": {
    "title": "MergeMind Application Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mergemind_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mergemind_errors_total[5m])",
            "legendFormat": "{{error_type}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, mergemind_request_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, mergemind_request_duration_seconds_bucket)",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "MR Analysis Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mergemind_mr_analysis_total[1h])",
            "legendFormat": "{{analysis_type}}"
          }
        ]
      }
    ]
  }
}
```

### Infrastructure Dashboard

```json
{
  "dashboard": {
    "title": "MergeMind Infrastructure",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total[5m]) * 100",
            "legendFormat": "{{container_name}}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "container_memory_usage_bytes / container_spec_memory_limit_bytes * 100",
            "legendFormat": "{{container_name}}"
          }
        ]
      },
      {
        "title": "BigQuery Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bigquery_job_total_bytes_processed[1h])",
            "legendFormat": "Bytes processed per hour"
          }
        ]
      }
    ]
  }
}
```

## SLO Monitoring

### Service Level Objectives

```yaml
# SLO definitions
slo:
  name: "API Availability"
  description: "API should be available 99.9% of the time"
  target: 0.999
  window: 30d
  metrics:
    - name: "uptime"
      query: "up{job='mergemind-api'}"
      threshold: 0.999

slo:
  name: "Response Time"
  description: "95% of requests should complete within 2 seconds"
  target: 0.95
  window: 7d
  metrics:
    - name: "latency"
      query: "histogram_quantile(0.95, mergemind_request_duration_seconds_bucket)"
      threshold: 2.0

slo:
  name: "Error Rate"
  description: "Error rate should be less than 1%"
  target: 0.01
  window: 7d
  metrics:
    - name: "error_rate"
      query: "rate(mergemind_errors_total[5m]) / rate(mergemind_requests_total[5m])"
      threshold: 0.01
```

### SLO Monitoring Implementation

```python
class SLOMonitor:
    def __init__(self):
        self.slos = self.load_slos()
    
    def check_slo_violations(self):
        """Check for SLO violations."""
        violations = []
        
        for slo in self.slos:
            current_value = self.get_current_metric_value(slo['metrics'][0]['query'])
            threshold = slo['metrics'][0]['threshold']
            
            if self.is_violation(current_value, threshold, slo['target']):
                violations.append({
                    'slo_name': slo['name'],
                    'current_value': current_value,
                    'threshold': threshold,
                    'target': slo['target'],
                    'severity': self.get_severity(current_value, threshold)
                })
        
        return violations
    
    def is_violation(self, current_value, threshold, target):
        """Check if current value violates SLO."""
        if target < 1.0:  # Rate-based SLO
            return current_value > threshold
        else:  # Count-based SLO
            return current_value < threshold
    
    def get_severity(self, current_value, threshold):
        """Determine violation severity."""
        if current_value > threshold * 2:
            return 'critical'
        elif current_value > threshold * 1.5:
            return 'warning'
        else:
            return 'info'
```

## Troubleshooting

### Common Issues

#### 1. High Error Rate

**Symptoms:**
- Error rate > 1%
- Multiple 500 status codes
- Service degradation

**Investigation:**
```bash
# Check error logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=mergemind-api AND severity>=ERROR" \
  --limit=50 --format="table(timestamp,severity,textPayload)"

# Check specific error types
gcloud logs read "resource.type=cloud_run_revision AND textPayload:\"ValidationError\"" \
  --limit=20 --format="table(timestamp,textPayload)"
```

**Resolution:**
- Check external service dependencies
- Verify input validation
- Review rate limiting
- Check resource limits

#### 2. High Latency

**Symptoms:**
- P95 latency > 2 seconds
- Slow response times
- Timeout errors

**Investigation:**
```bash
# Check slow queries
gcloud logs read "resource.type=cloud_run_revision AND textPayload:\"slow query\"" \
  --limit=20 --format="table(timestamp,textPayload)"

# Check BigQuery performance
bq query --use_legacy_sql=false "
SELECT
  job_id,
  creation_time,
  total_bytes_processed,
  total_slot_ms,
  total_slot_ms / (total_bytes_processed / 1024 / 1024 / 1024) as slot_ms_per_gb
FROM \`mergemind-prod.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT\`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY total_slot_ms DESC
LIMIT 10
"
```

**Resolution:**
- Optimize database queries
- Implement caching
- Scale up resources
- Review external API calls

#### 3. Service Unavailable

**Symptoms:**
- 503 status codes
- Health checks failing
- Service down

**Investigation:**
```bash
# Check service status
gcloud run services describe mergemind-api --region=us-central1

# Check recent deployments
gcloud run revisions list --service=mergemind-api --region=us-central1

# Check resource usage
gcloud run services describe mergemind-api --region=us-central1 \
  --format="value(spec.template.spec.containers[0].resources)"
```

**Resolution:**
- Check resource limits
- Review deployment logs
- Verify external dependencies
- Scale up if needed

### Monitoring Commands

```bash
# Check current metrics
curl "https://api.mergemind.com/api/v1/metrics" | jq .

# Check health status
curl "https://api.mergemind.com/api/v1/health/detailed" | jq .

# Check SLO violations
curl "https://api.mergemind.com/api/v1/metrics/slo" | jq .

# Check recent errors
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=10 --format="table(timestamp,severity,textPayload)"

# Check BigQuery usage
bq query --use_legacy_sql=false "
SELECT
  DATE(creation_time) as date,
  COUNT(*) as job_count,
  SUM(total_bytes_processed) as total_bytes,
  SUM(total_slot_ms) as total_slots
FROM \`mergemind-prod.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT\`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY date
ORDER BY date DESC
"
```

### Performance Tuning

```python
# Connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "bigquery://mergemind-prod/mergemind",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Caching strategy
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

# Async processing
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_mrs_async(mr_ids):
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, analyze_mr, mr_id)
            for mr_id in mr_ids
        ]
        results = await asyncio.gather(*tasks)
    return results
```

This monitoring guide provides comprehensive coverage of all aspects of monitoring the MergeMind system, from basic health checks to advanced SLO monitoring and troubleshooting procedures.
