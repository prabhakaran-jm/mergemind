# MergeMind Observability and Operations Guide

## Overview
This document outlines the observability features, monitoring, and operational procedures for MergeMind.

## Logging

### Structured Logging
- All requests are logged with structured JSON format
- Each request gets a unique `request_id` for tracing
- Logs include timing, status codes, and error details
- Request IDs are returned in response headers

### Log Levels
- `INFO`: Normal operations, request start/completion
- `WARNING`: Non-critical issues, degraded functionality
- `ERROR`: Critical errors, failed requests
- `DEBUG`: Detailed debugging information

### Log Format
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "request_id": "uuid-here",
  "method": "GET",
  "url": "/api/v1/mrs",
  "status_code": 200,
  "duration_ms": 150.5,
  "client_ip": "192.168.1.1"
}
```

## Metrics

### Key Metrics
- **Request Count**: Total number of requests
- **Error Rate**: Percentage of failed requests
- **Latency**: P50, P95, P99 response times
- **Throughput**: Requests per second
- **Uptime**: Service availability

### Endpoint Metrics
- Request count per endpoint
- Error rate per endpoint
- Average response time per endpoint
- Percentile latencies per endpoint

### Error Tracking
- Error types and frequencies
- Error distribution by endpoint
- Error trends over time

## SLOs (Service Level Objectives)

### Current SLOs
- **Error Rate**: < 1% of requests should fail
- **P95 Latency**: < 2 seconds for 95% of requests
- **P99 Latency**: < 5 seconds for 99% of requests
- **Availability**: > 99.9% uptime

### SLO Violations
- SLO violations are automatically detected
- Violations are logged with severity levels
- Alerts can be configured based on violation patterns

## Health Checks

### Basic Health Check (`/healthz`)
- Returns basic service status
- Tests core functionality
- Used by load balancers and monitoring

### Readiness Check (`/ready`)
- Tests external dependencies
- Validates service readiness
- Used for deployment health checks

### Detailed Health Check (`/health/detailed`)
- Comprehensive health status
- Includes all service dependencies
- Provides metrics and SLO status

## Monitoring Endpoints

### Metrics Endpoint (`/metrics`)
- Returns current metrics summary
- Includes request counts, error rates, latencies
- Top endpoints and error types

### SLO Status (`/metrics/slo`)
- Checks for SLO violations
- Returns violation details and severity
- Overall service health status

### Endpoint Metrics (`/metrics/endpoint/{endpoint}`)
- Detailed metrics for specific endpoints
- Includes percentiles and error rates
- Useful for performance analysis

## Alerting

### Recommended Alerts
1. **High Error Rate**: Error rate > 5%
2. **High Latency**: P95 latency > 5 seconds
3. **Service Down**: Health check failures
4. **SLO Violations**: Any SLO violation
5. **Dependency Failures**: External service failures

### Alert Severity Levels
- **Critical**: Service down, P99 > 10s
- **High**: Error rate > 5%, P95 > 5s
- **Medium**: SLO violations, P95 > 2s
- **Low**: Warning conditions, minor issues

## Operational Procedures

### Deployment Health Checks
1. Check `/healthz` endpoint
2. Verify `/ready` endpoint
3. Monitor metrics for 5 minutes
4. Check for SLO violations
5. Verify external dependencies

### Incident Response
1. Check health endpoints
2. Review recent logs for errors
3. Check metrics for anomalies
4. Verify external service status
5. Check SLO violation status

### Performance Tuning
1. Monitor endpoint metrics
2. Identify slow endpoints
3. Check for error patterns
4. Review dependency performance
5. Optimize based on metrics

## Troubleshooting

### Common Issues
- **High Error Rate**: Check external dependencies, review logs
- **High Latency**: Check database queries, external API calls
- **Service Unavailable**: Check health endpoints, verify dependencies
- **SLO Violations**: Review metrics, check for bottlenecks

### Debugging Steps
1. Check request logs with `request_id`
2. Review endpoint-specific metrics
3. Check external service health
4. Review error patterns and types
5. Check system resources

## Best Practices

### Logging
- Use structured logging consistently
- Include request IDs in all log entries
- Log important business events
- Avoid logging sensitive data

### Metrics
- Monitor key business metrics
- Track performance trends
- Set up appropriate alerts
- Review metrics regularly

### Health Checks
- Implement comprehensive health checks
- Test all critical dependencies
- Use health checks for deployments
- Monitor health check results

### SLOs
- Set realistic SLO targets
- Monitor SLO compliance
- Alert on SLO violations
- Review and adjust SLOs regularly
