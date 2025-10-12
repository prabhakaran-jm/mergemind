# High Latency Runbook

## Alert Description
The 95th percentile response time has exceeded 5 seconds for more than 5 minutes.

## Severity
Warning

## Impact
- Slow user experience
- Timeout errors for users
- Reduced system throughput
- Potential cascading failures

## Immediate Actions

### 1. Verify Alert
```bash
# Check current latency metrics
curl http://localhost:9090/api/v1/query?query=histogram_quantile\(0.95, mergemind_request_duration_seconds_bucket\)

# Check latency by endpoint
curl http://localhost:9090/api/v1/query?query=histogram_quantile\(0.95, mergemind_request_duration_seconds_bucket\) by \(endpoint\)

# Check request rate
curl http://localhost:9090/api/v1/query?query=rate\(mergemind_requests_total\[5m\]\)
```

### 2. Identify Slow Endpoints
```bash
# Check endpoint-specific latency
curl http://localhost:9090/api/v1/query?query=histogram_quantile\(0.95, mergemind_request_duration_seconds_bucket\) by \(endpoint\)

# Check slowest endpoints
curl http://localhost:9090/api/v1/query?query=topk\(10, histogram_quantile\(0.95, mergemind_request_duration_seconds_bucket\) by \(endpoint\)\)

# Check request volume by endpoint
curl http://localhost:9090/api/v1/query?query=sum by \(endpoint\) \(rate\(mergemind_requests_total\[5m\]\)\)
```

### 3. Check System Resources
```bash
# Check CPU usage
curl http://localhost:9090/api/v1/query?query=rate\(container_cpu_usage_seconds_total\[5m\]\)

# Check memory usage
curl http://localhost:9090/api/v1/query?query=container_memory_usage_bytes / container_spec_memory_limit_bytes

# Check disk I/O
curl http://localhost:9090/api/v1/query?query=rate\(container_fs_io_time_seconds_total\[5m\]\)

# Check network I/O
curl http://localhost:9090/api/v1/query?query=rate\(container_network_receive_bytes_total\[5m\]\)
```

### 4. Check External Dependencies
```bash
# Check BigQuery performance
curl http://localhost:9090/api/v1/query?query=histogram_quantile\(0.95, bigquery_query_duration_seconds_bucket\)

# Check GitLab API performance
curl http://localhost:9090/api/v1/query?query=histogram_quantile\(0.95, gitlab_api_duration_seconds_bucket\)

# Check Vertex AI performance
curl http://localhost:9090/api/v1/query?query=histogram_quantile\(0.95, vertex_ai_request_duration_seconds_bucket\)
```

## Root Cause Analysis

### Common Causes
1. **Database Performance**: Slow BigQuery queries
2. **External API Delays**: GitLab or Vertex AI slow responses
3. **Resource Contention**: CPU, memory, or disk bottlenecks
4. **Network Issues**: Slow network connectivity
5. **Application Bottlenecks**: Inefficient code or algorithms
6. **Concurrent Load**: High request volume

### Investigation Steps
```bash
# Check application logs for slow queries
docker logs mergemind-api --tail=100 | grep -i "slow\|timeout\|duration"

# Check BigQuery job performance
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

# Check GitLab API response times
curl -w "@curl-format.txt" -o /dev/null -s https://your-gitlab.com/api/v4/user

# Check Vertex AI response times
gcloud ai models predict gemini-1.5-pro --region=us-central1 --json-request='{"instances": [{"prompt": "test"}]}'
```

## Mitigation Strategies

### Immediate Mitigation
1. **Scale Up**: Increase CPU/memory resources
2. **Connection Pooling**: Optimize database connections
3. **Caching**: Implement response caching
4. **Rate Limiting**: Limit request rate to prevent overload
5. **Circuit Breaker**: Fail fast for slow external services

### Long-term Solutions
1. **Query Optimization**: Optimize BigQuery queries
2. **Indexing**: Add proper database indexes
3. **Architecture**: Implement microservices architecture
4. **Load Balancing**: Distribute load across instances
5. **Performance Testing**: Regular performance testing

## Prevention

### Monitoring
- Set up latency alerts with different percentiles
- Monitor external service response times
- Track resource usage trends
- Alert on performance degradation

### Performance Testing
- Regular load testing
- Performance benchmarking
- Stress testing
- Capacity planning

### Optimization
- Code profiling and optimization
- Database query optimization
- Caching strategies
- Resource allocation optimization

## Escalation

### When to Escalate
- Latency exceeds 10 seconds
- Multiple endpoints affected
- System stability at risk
- User experience severely impacted

### Escalation Contacts
- **Primary**: DevOps Team (devops@mergemind.com)
- **Secondary**: Engineering Manager (eng-manager@mergemind.com)
- **Emergency**: On-call Engineer (oncall@mergemind.com)

## Post-Incident

### Actions Required
1. **Performance Analysis**: Document performance impact
2. **Root Cause**: Identify the underlying cause
3. **Optimization**: Implement performance improvements
4. **Monitoring**: Enhance performance monitoring
5. **Testing**: Verify performance improvements

### Follow-up Tasks
- [ ] Optimize slow queries
- [ ] Implement caching where appropriate
- [ ] Scale resources if needed
- [ ] Update performance monitoring
- [ ] Schedule performance review

## Related Documentation
- [Performance Guide](../docs/PERFORMANCE.md)
- [Monitoring Guide](../docs/MONITORING.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
