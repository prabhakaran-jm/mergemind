# High Error Rate Runbook

## Alert Description
The error rate for the MergeMind API has exceeded 5% over the last 5 minutes.

## Severity
Critical

## Impact
- Users experiencing failed requests
- Degraded user experience
- Potential data inconsistency
- Increased support load

## Immediate Actions

### 1. Verify Alert
```bash
# Check current error rate
curl http://localhost:9090/api/v1/query?query=rate\(mergemind_errors_total\[5m\]\)/rate\(mergemind_requests_total\[5m\]\)

# Check error types
curl http://localhost:9090/api/v1/query?query=rate\(mergemind_errors_total\[5m\]\)

# Check application logs
docker logs mergemind-api --tail=100
```

### 2. Identify Error Types
```bash
# Check error breakdown
curl http://localhost:9090/api/v1/query?query=sum by \(error_type\) \(rate\(mergemind_errors_total\[5m\]\)\)

# Check endpoint-specific errors
curl http://localhost:9090/api/v1/query?query=sum by \(endpoint\) \(rate\(mergemind_errors_total\[5m\]\)\)

# Check status code breakdown
curl http://localhost:9090/api/v1/query?query=sum by \(status_code\) \(rate\(mergemind_requests_total\[5m\]\)\)
```

### 3. Check External Dependencies
```bash
# Check BigQuery connectivity
curl http://localhost:8081/health

# Check GitLab API status
curl http://localhost:8082/health

# Check Vertex AI status
curl http://localhost:8083/health

# Test external services directly
curl -f https://your-gitlab.com/api/v4/user
```

### 4. Implement Mitigation
```bash
# If BigQuery issues
# Check quota usage
bq query --use_legacy_sql=false "
SELECT
  DATE(creation_time) as date,
  SUM(total_bytes_processed) as total_bytes
FROM \`mergemind-prod.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT\`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
GROUP BY date
"

# If GitLab API issues
# Check rate limits
curl -I https://your-gitlab.com/api/v4/user

# If Vertex AI issues
# Check quota usage
gcloud ai models list --region=us-central1
```

## Root Cause Analysis

### Common Causes
1. **External Service Outages**: BigQuery, GitLab, or Vertex AI down
2. **Rate Limiting**: API rate limits exceeded
3. **Resource Exhaustion**: Memory, CPU, or disk space issues
4. **Configuration Errors**: Invalid credentials or settings
5. **Network Issues**: Connectivity problems
6. **Application Bugs**: Code errors or edge cases

### Investigation Steps
```bash
# Check application metrics
curl http://localhost:8080/api/v1/metrics

# Check system resources
docker stats mergemind-api

# Check network connectivity
ping google.com
nslookup your-gitlab.com

# Check recent deployments
git log --oneline -10

# Check configuration
docker exec mergemind-api env | grep -E "(GITLAB|BIGQUERY|VERTEX)"
```

## Mitigation Strategies

### Immediate Mitigation
1. **Circuit Breaker**: Implement circuit breakers for external calls
2. **Retry Logic**: Add exponential backoff for failed requests
3. **Fallback Responses**: Return cached or default responses
4. **Rate Limiting**: Implement client-side rate limiting
5. **Graceful Degradation**: Disable non-essential features

### Long-term Solutions
1. **Monitoring**: Improve error tracking and alerting
2. **Testing**: Add more comprehensive tests
3. **Resilience**: Implement better error handling
4. **Capacity Planning**: Scale resources appropriately
5. **Documentation**: Improve error handling documentation

## Prevention

### Monitoring
- Set up error rate alerts with different thresholds
- Monitor external service health
- Track error patterns and trends
- Alert on resource usage spikes

### Testing
- Implement chaos engineering
- Test failure scenarios
- Load test with realistic traffic
- Test external service failures

### Configuration
- Use connection pooling
- Implement timeouts and retries
- Configure proper resource limits
- Use health checks for dependencies

## Escalation

### When to Escalate
- Error rate exceeds 10%
- Multiple external services affected
- Data corruption suspected
- Security incident possible

### Escalation Contacts
- **Primary**: DevOps Team (devops@mergemind.com)
- **Secondary**: Engineering Manager (eng-manager@mergemind.com)
- **Emergency**: On-call Engineer (oncall@mergemind.com)

## Post-Incident

### Actions Required
1. **Root Cause Analysis**: Document the cause and impact
2. **Timeline**: Create detailed incident timeline
3. **Lessons Learned**: Identify improvement opportunities
4. **Prevention**: Implement additional safeguards
5. **Testing**: Verify mitigation measures work

### Follow-up Tasks
- [ ] Update error handling code
- [ ] Improve monitoring and alerting
- [ ] Add more comprehensive tests
- [ ] Review and update this runbook
- [ ] Schedule post-incident review

## Related Documentation
- [Error Handling Guide](../docs/ERROR_HANDLING.md)
- [Monitoring Guide](../docs/MONITORING.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
