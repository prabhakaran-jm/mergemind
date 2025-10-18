# Service Down Runbook

## Alert Description
The MergeMind API service is down or unreachable.

## Severity
Critical

## Impact
- Users cannot access the MergeMind application
- All API endpoints are unavailable
- Real-time MR analysis is unavailable

## Immediate Actions

### 1. Verify Alert
```bash
# Check service status
curl -f http://localhost:8080/api/v1/healthz

# Check Docker container status
docker ps | grep mergemind-api

# Check container logs
docker logs mergemind-api
```

### 2. Check Infrastructure
```bash
# Check Cloud Run status (if deployed)
gcloud run services describe mergemind-api --region=us-central1

# Check Kubernetes pods (if deployed)
kubectl get pods -l app=mergemind-api

# Check node status
kubectl get nodes
```

### 3. Restart Service
```bash
# Docker Compose
docker-compose restart mergemind-api

# Kubernetes
kubectl rollout restart deployment/mergemind-api

# Cloud Run
gcloud run services update mergemind-api --region=us-central1
```

### 4. Verify Recovery
```bash
# Wait 30 seconds
sleep 30

# Check health endpoint
curl -f http://localhost:8080/api/v1/healthz

# Check metrics
curl http://localhost:8080/api/v1/metrics
```

## Root Cause Analysis

### Common Causes
1. **Out of Memory**: Container killed due to memory limits
2. **Crash Loop**: Application errors causing repeated restarts
3. **Network Issues**: Connectivity problems to external services
4. **Resource Exhaustion**: CPU or disk space issues
5. **Configuration Errors**: Invalid environment variables or config

### Investigation Steps
```bash
# Check container resource usage
docker stats mergemind-api

# Check system resources
top
df -h
free -h

# Check network connectivity
ping google.com
nslookup api.mergemind.com

# Check external service dependencies
curl -f https://your-gitlab.com/api/v4/user
```

## Prevention

### Monitoring
- Set up health checks with proper intervals
- Monitor resource usage trends
- Alert on high memory/CPU usage
- Track restart frequency

### Configuration
- Set appropriate resource limits
- Configure proper health check endpoints
- Use circuit breakers for external calls
- Implement graceful shutdown

### Deployment
- Use rolling deployments
- Test deployments in staging first
- Have rollback procedures ready
- Monitor deployment metrics

## Escalation

### When to Escalate
- Service remains down after 15 minutes
- Multiple services are affected
- Data loss is suspected
- Security incident is possible

### Escalation Contacts
- **Primary**: DevOps Team (devops@mergemind.com)
- **Secondary**: Engineering Manager (eng-manager@mergemind.com)
- **Emergency**: On-call Engineer (oncall@mergemind.com)

## Post-Incident

### Actions Required
1. **Incident Report**: Document root cause and resolution
2. **Timeline**: Create detailed timeline of events
3. **Lessons Learned**: Identify improvement opportunities
4. **Prevention**: Implement additional monitoring/alerting
5. **Testing**: Verify prevention measures work

### Follow-up Tasks
- [ ] Update monitoring thresholds if needed
- [ ] Review and update this runbook
- [ ] Schedule post-incident review meeting
- [ ] Implement any identified improvements
- [ ] Test recovery procedures

## Related Documentation
- [Production Deployment Guide](../docs/PRODUCTION_DEPLOYMENT.md)
- [Monitoring Guide](../docs/MONITORING.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
