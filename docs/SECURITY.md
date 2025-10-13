# MergeMind Security Guide

Comprehensive security guide for the MergeMind system, covering authentication, authorization, data protection, and security best practices.

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection](#data-protection)
4. [Network Security](#network-security)
5. [API Security](#api-security)
6. [Infrastructure Security](#infrastructure-security)
7. [Compliance](#compliance)
8. [Incident Response](#incident-response)

## Security Overview

MergeMind implements defense-in-depth security across multiple layers:

- **Application Security**: Input validation, output encoding, secure coding practices
- **API Security**: Rate limiting, authentication, authorization, input validation
- **Data Security**: Encryption at rest and in transit, access controls, data classification
- **Infrastructure Security**: Network segmentation, firewall rules, secure configurations
- **Operational Security**: Monitoring, logging, incident response, security updates

## Authentication & Authorization

### API Authentication

#### API Key Authentication (Recommended)

```python
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

security = HTTPBearer()

class APIKeyAuth:
    def __init__(self):
        self.api_keys = self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from secure storage."""
        # In production, use Google Secret Manager
        return {
            "prod_key_123": {
                "user_id": "user_123",
                "permissions": ["read", "write"],
                "rate_limit": 1000,
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }
    
    def validate_api_key(self, api_key: str):
        """Validate API key and return user info."""
        if api_key not in self.api_keys:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        key_info = self.api_keys[api_key]
        
        # Check expiration
        if key_info.get("expires_at"):
            expires_at = datetime.fromisoformat(key_info["expires_at"])
            if datetime.utcnow() > expires_at:
                raise HTTPException(
                    status_code=401,
                    detail="API key expired"
                )
        
        return key_info

api_auth = APIKeyAuth()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Get current user from API key."""
    api_key = credentials.credentials
    return api_auth.validate_api_key(api_key)

# Usage in endpoints
@app.get("/api/v1/mrs")
async def list_mrs(current_user: dict = Depends(get_current_user)):
    """List MRs with authentication."""
    # Check permissions
    if "read" not in current_user["permissions"]:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    
    return await get_mrs_from_bigquery()
```

#### OAuth 2.0 Authentication (Future)

```python
from authlib.integrations.fastapi_oauth2 import OAuth2

oauth2 = OAuth2()

# Configure OAuth providers
oauth2.register(
    name='gitlab',
    client_id=os.getenv('GITLAB_CLIENT_ID'),
    client_secret=os.getenv('GITLAB_CLIENT_SECRET'),
    server_metadata_url='https://gitlab.com/.well-known/openid_configuration',
    client_kwargs={'scope': 'read_user read_api'}
)

@app.get("/api/v1/auth/login")
async def login():
    """Initiate OAuth login."""
    redirect_uri = oauth2.gitlab.authorize_redirect(
        redirect_uri="https://api.mergemind.com/api/v1/auth/callback"
    )
    return {"redirect_uri": redirect_uri}

@app.get("/api/v1/auth/callback")
async def callback(request: Request):
    """Handle OAuth callback."""
    token = await oauth2.gitlab.authorize_access_token(request)
    user_info = await oauth2.gitlab.get_user_info(token)
    
    # Create or update user session
    session_id = create_user_session(user_info)
    
    return {"session_id": session_id}
```

### JWT Token Authentication

```python
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

class JWTAuth:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        self.algorithm = 'HS256'
        self.expiration_hours = 24
    
    def create_token(self, user_id: str, permissions: list):
        """Create JWT token."""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=self.expiration_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_token(self, token: str):
        """Validate JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

jwt_auth = JWTAuth()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Get current user from JWT token."""
    token = credentials.credentials
    return jwt_auth.validate_token(token)
```

### Role-Based Access Control (RBAC)

```python
from enum import Enum
from typing import List

class Permission(Enum):
    READ_MRS = "read:mrs"
    WRITE_MRS = "write:mrs"
    READ_ANALYTICS = "read:analytics"
    ADMIN = "admin"

class Role(Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"

ROLE_PERMISSIONS = {
    Role.VIEWER: [Permission.READ_MRS],
    Role.ANALYST: [Permission.READ_MRS, Permission.READ_ANALYTICS],
    Role.ADMIN: [Permission.READ_MRS, Permission.WRITE_MRS, Permission.READ_ANALYTICS, Permission.ADMIN]
}

def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            user_permissions = current_user.get('permissions', [])
            if permission.value not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission {permission.value} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@app.get("/api/v1/mrs")
@require_permission(Permission.READ_MRS)
async def list_mrs(current_user: dict = Depends(get_current_user)):
    """List MRs with permission check."""
    return await get_mrs_from_bigquery()
```

## Data Protection

### Encryption at Rest

```python
# BigQuery encryption
CREATE TABLE `mergemind_raw.merge_requests` (
  mr_id INT64,
  project_id INT64,
  title STRING,
  description STRING,
  created_at TIMESTAMP
)
PARTITION BY DATE(created_at)
CLUSTER BY project_id, mr_id
OPTIONS (
  encryption_configuration = (
    kms_key_name = "projects/mergemind-prod/locations/us-central1/keyRings/mergemind-ring/cryptoKeys/mergemind-key"
  )
);

# Google Secret Manager for sensitive data
from google.cloud import secretmanager

def get_secret(secret_id: str):
    """Get secret from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/mergemind-prod/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
gitlab_token = get_secret("gitlab-token")
```

### Encryption in Transit

```python
# HTTPS enforcement
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# Redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Security headers
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mergemind.com", "https://app.mergemind.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["mergemind.com", "*.mergemind.com"]
)

# Security headers middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### Data Classification

```python
from enum import Enum
from typing import Dict, Any

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class DataProtection:
    def __init__(self):
        self.classification_rules = {
            "mr_id": DataClassification.INTERNAL,
            "project_id": DataClassification.INTERNAL,
            "title": DataClassification.INTERNAL,
            "description": DataClassification.CONFIDENTIAL,
            "author_email": DataClassification.RESTRICTED,
            "source_code": DataClassification.RESTRICTED
        }
    
    def classify_data(self, data: Dict[str, Any]) -> Dict[str, DataClassification]:
        """Classify data fields."""
        classification = {}
        for field, value in data.items():
            if field in self.classification_rules:
                classification[field] = self.classification_rules[field]
            else:
                classification[field] = DataClassification.INTERNAL
        return classification
    
    def mask_sensitive_data(self, data: Dict[str, Any], classification: Dict[str, DataClassification]):
        """Mask sensitive data based on classification."""
        masked_data = {}
        for field, value in data.items():
            if classification[field] == DataClassification.RESTRICTED:
                masked_data[field] = "***REDACTED***"
            elif classification[field] == DataClassification.CONFIDENTIAL:
                masked_data[field] = value[:10] + "..." if len(str(value)) > 10 else value
            else:
                masked_data[field] = value
        return masked_data

data_protection = DataProtection()
```

## Network Security

### VPC Configuration

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

gcloud compute firewall-rules create deny-all \
  --network mergemind-vpc \
  --action deny \
  --rules all \
  --priority 65534
```

### Load Balancer Security

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

## API Security

### Input Validation

```python
from pydantic import BaseModel, validator, Field
from typing import Optional, List
import re

class MRListRequest(BaseModel):
    state: Optional[str] = Field(None, regex="^(open|merged|closed)$")
    project_id: Optional[int] = Field(None, ge=1)
    limit: int = Field(50, ge=1, le=200)
    cursor: Optional[str] = Field(None, max_length=1000)
    
    @validator('state')
    def validate_state(cls, v):
        if v and v not in ['open', 'merged', 'closed']:
            raise ValueError('Invalid state value')
        return v
    
    @validator('cursor')
    def validate_cursor(cls, v):
        if v and not re.match(r'^[A-Za-z0-9+/=]+$', v):
            raise ValueError('Invalid cursor format')
        return v

class MRSummaryRequest(BaseModel):
    mr_id: int = Field(..., ge=1)
    include_risks: bool = Field(True)
    include_tests: bool = Field(True)
    
    @validator('mr_id')
    def validate_mr_id(cls, v):
        if v <= 0:
            raise ValueError('MR ID must be positive')
        return v

# SQL injection prevention
def safe_query(sql: str, params: Dict[str, Any]) -> str:
    """Execute query with parameterized inputs."""
    # Validate SQL structure
    allowed_keywords = ['SELECT', 'FROM', 'WHERE', 'ORDER BY', 'LIMIT']
    sql_upper = sql.upper()
    
    for keyword in allowed_keywords:
        if keyword not in sql_upper:
            raise ValueError(f"Invalid SQL: missing {keyword}")
    
    # Parameterize inputs
    for key, value in params.items():
        if isinstance(value, str):
            # Escape single quotes
            value = value.replace("'", "''")
            sql = sql.replace(f"@{key}", f"'{value}'")
        else:
            sql = sql.replace(f"@{key}", str(value))
    
    return sql
```

### Rate Limiting

```python
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis

# Redis for rate limiting
redis_client = redis.Redis(
    host='redis.mergemind.com',
    port=6379,
    db=0
)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis.mergemind.com:6379"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Rate limiting decorators
@app.get("/api/v1/mrs")
@limiter.limit("100/minute")
async def list_mrs(request: Request):
    """List MRs with rate limiting."""
    return await get_mrs_from_bigquery()

@app.post("/api/v1/mr/{mr_id}/summary")
@limiter.limit("10/minute")
async def generate_summary(request: Request, mr_id: int):
    """Generate summary with rate limiting."""
    return await generate_ai_summary(mr_id)

# Custom rate limiting
class CustomRateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.redis_client = redis_client
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        current_time = int(time.time())
        window_start = current_time - 60
        
        # Count requests in current window
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, 60)
        results = pipe.execute()
        
        request_count = results[1]
        return request_count < self.requests_per_minute

rate_limiter = CustomRateLimiter(100)
```

### API Security Headers

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response
```

## Infrastructure Security

### Service Account Security

```bash
# Create minimal service account
gcloud iam service-accounts create mergemind-api \
  --display-name="MergeMind API Service Account"

# Grant minimal permissions
gcloud projects add-iam-policy-binding mergemind-prod \
  --member="serviceAccount:mergemind-api@mergemind-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding mergemind-prod \
  --member="serviceAccount:mergemind-api@mergemind-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# Create and download key
gcloud iam service-accounts keys create mergemind-api-key.json \
  --iam-account=mergemind-api@mergemind-prod.iam.gserviceaccount.com
```

### Container Security

```dockerfile
# Multi-stage build for security
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r mergemind && useradd -r -g mergemind mergemind

# Copy application
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . /app

# Set ownership
RUN chown -R mergemind:mergemind /app

# Switch to non-root user
USER mergemind

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/healthz || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Kubernetes Security

```yaml
# Pod Security Policy
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: mergemind-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'

---
# Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mergemind-network-policy
spec:
  podSelector:
    matchLabels:
      app: mergemind-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

## Compliance

### GDPR Compliance

```python
class GDPRCompliance:
    def __init__(self):
        self.data_retention_days = 365
        self.anonymization_rules = {
            "user_id": "hash",
            "email": "mask",
            "name": "mask"
        }
    
    def anonymize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize user data for GDPR compliance."""
        anonymized = {}
        for field, value in user_data.items():
            if field in self.anonymization_rules:
                if self.anonymization_rules[field] == "hash":
                    anonymized[field] = hashlib.sha256(str(value).encode()).hexdigest()[:8]
                elif self.anonymization_rules[field] == "mask":
                    anonymized[field] = "***REDACTED***"
            else:
                anonymized[field] = value
        return anonymized
    
    def delete_user_data(self, user_id: str):
        """Delete user data for GDPR compliance."""
        # Delete from BigQuery
        sql = f"""
        DELETE FROM `mergemind_raw.users`
        WHERE user_id = @user_id
        """
        bigquery_client.query(sql, user_id=user_id)
        
        # Delete from cache
        cache_key = f"user:{user_id}"
        redis_client.delete(cache_key)
        
        # Log deletion
        logger.info(f"User data deleted for GDPR compliance", user_id=user_id)
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data for GDPR compliance."""
        # Get user data from BigQuery
        sql = f"""
        SELECT * FROM `mergemind_raw.users`
        WHERE user_id = @user_id
        """
        user_data = bigquery_client.query(sql, user_id=user_id)
        
        # Get related data
        sql = f"""
        SELECT * FROM `mergemind_raw.mr_notes`
        WHERE author_id = @user_id
        """
        notes_data = bigquery_client.query(sql, user_id=user_id)
        
        return {
            "user_data": user_data,
            "notes_data": notes_data,
            "exported_at": datetime.utcnow().isoformat()
        }

gdpr_compliance = GDPRCompliance()
```

### SOC 2 Compliance

```python
class SOC2Compliance:
    def __init__(self):
        self.access_logs = []
        self.data_classification = DataProtection()
    
    def log_access(self, user_id: str, resource: str, action: str):
        """Log access for SOC 2 compliance."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent")
        }
        self.access_logs.append(log_entry)
        
        # Store in BigQuery
        sql = """
        INSERT INTO `mergemind.audit_logs`
        (timestamp, user_id, resource, action, ip_address, user_agent)
        VALUES (@timestamp, @user_id, @resource, @action, @ip_address, @user_agent)
        """
        bigquery_client.query(sql, **log_entry)
    
    def monitor_data_access(self, data: Dict[str, Any]):
        """Monitor data access for SOC 2 compliance."""
        classification = self.data_classification.classify_data(data)
        
        # Check for restricted data access
        restricted_fields = [
            field for field, cls in classification.items()
            if cls == DataClassification.RESTRICTED
        ]
        
        if restricted_fields:
            logger.warning(
                "Restricted data accessed",
                fields=restricted_fields,
                user_id=current_user.get("user_id")
            )
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate SOC 2 compliance report."""
        # Get access logs
        sql = """
        SELECT
          DATE(timestamp) as date,
          COUNT(*) as access_count,
          COUNT(DISTINCT user_id) as unique_users,
          COUNT(DISTINCT resource) as unique_resources
        FROM `mergemind.audit_logs`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY date
        ORDER BY date DESC
        """
        access_stats = bigquery_client.query(sql)
        
        return {
            "report_period": "30 days",
            "access_statistics": access_stats,
            "data_classification": "implemented",
            "encryption": "enabled",
            "access_controls": "enabled",
            "monitoring": "enabled"
        }

soc2_compliance = SOC2Compliance()
```

## Incident Response

### Security Incident Response Plan

```python
class SecurityIncidentResponse:
    def __init__(self):
        self.incident_types = {
            "data_breach": "critical",
            "unauthorized_access": "high",
            "malicious_activity": "high",
            "service_compromise": "critical",
            "data_leak": "high"
        }
    
    def detect_incident(self, incident_type: str, details: Dict[str, Any]):
        """Detect and respond to security incident."""
        severity = self.incident_types.get(incident_type, "medium")
        
        # Log incident
        logger.critical(
            "Security incident detected",
            incident_type=incident_type,
            severity=severity,
            details=details
        )
        
        # Immediate response based on severity
        if severity == "critical":
            self.trigger_critical_response(incident_type, details)
        elif severity == "high":
            self.trigger_high_response(incident_type, details)
        else:
            self.trigger_medium_response(incident_type, details)
    
    def trigger_critical_response(self, incident_type: str, details: Dict[str, Any]):
        """Trigger critical incident response."""
        # Notify security team
        self.notify_security_team(incident_type, details)
        
        # Isolate affected systems
        self.isolate_systems(details.get("affected_systems", []))
        
        # Preserve evidence
        self.preserve_evidence(details)
        
        # Notify stakeholders
        self.notify_stakeholders(incident_type, details)
    
    def notify_security_team(self, incident_type: str, details: Dict[str, Any]):
        """Notify security team of incident."""
        # Send alert to security team
        alert_message = f"""
        CRITICAL SECURITY INCIDENT DETECTED
        
        Type: {incident_type}
        Time: {datetime.utcnow().isoformat()}
        Details: {details}
        
        Immediate action required.
        """
        
        # Send to security team notification channel
        # Implementation depends on notification system
        pass
    
    def isolate_systems(self, affected_systems: List[str]):
        """Isolate affected systems."""
        for system in affected_systems:
            # Disable API access
            if system == "api":
                self.disable_api_access()
            
            # Block IP addresses
            if system == "network":
                self.block_suspicious_ips()
            
            # Revoke access tokens
            if system == "authentication":
                self.revoke_compromised_tokens()
    
    def preserve_evidence(self, details: Dict[str, Any]):
        """Preserve evidence for investigation."""
        # Create evidence snapshot
        evidence = {
            "timestamp": datetime.utcnow().isoformat(),
            "incident_details": details,
            "system_state": self.get_system_state(),
            "access_logs": self.get_recent_access_logs(),
            "error_logs": self.get_recent_error_logs()
        }
        
        # Store in secure location
        self.store_evidence(evidence)
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state."""
        return {
            "active_sessions": len(get_active_sessions()),
            "recent_errors": get_recent_errors(),
            "system_metrics": get_system_metrics(),
            "network_connections": get_network_connections()
        }

security_incident_response = SecurityIncidentResponse()
```

### Security Monitoring

```python
class SecurityMonitoring:
    def __init__(self):
        self.suspicious_patterns = [
            "multiple_failed_logins",
            "unusual_data_access",
            "privilege_escalation",
            "data_exfiltration"
        ]
    
    def monitor_suspicious_activity(self):
        """Monitor for suspicious activity."""
        # Check for multiple failed logins
        self.check_failed_logins()
        
        # Check for unusual data access patterns
        self.check_data_access_patterns()
        
        # Check for privilege escalation attempts
        self.check_privilege_escalation()
        
        # Check for data exfiltration
        self.check_data_exfiltration()
    
    def check_failed_logins(self):
        """Check for multiple failed login attempts."""
        sql = """
        SELECT
          ip_address,
          COUNT(*) as failed_attempts
        FROM `mergemind.audit_logs`
        WHERE action = 'login_failed'
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        GROUP BY ip_address
        HAVING failed_attempts > 5
        """
        results = bigquery_client.query(sql)
        
        for result in results:
            if result["failed_attempts"] > 10:
                security_incident_response.detect_incident(
                    "unauthorized_access",
                    {
                        "ip_address": result["ip_address"],
                        "failed_attempts": result["failed_attempts"],
                        "time_window": "1 hour"
                    }
                )
    
    def check_data_access_patterns(self):
        """Check for unusual data access patterns."""
        sql = """
        SELECT
          user_id,
          COUNT(*) as access_count,
          COUNT(DISTINCT resource) as unique_resources
        FROM `mergemind.audit_logs`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        GROUP BY user_id
        HAVING access_count > 100 OR unique_resources > 50
        """
        results = bigquery_client.query(sql)
        
        for result in results:
            security_incident_response.detect_incident(
                "malicious_activity",
                {
                    "user_id": result["user_id"],
                    "access_count": result["access_count"],
                    "unique_resources": result["unique_resources"]
                }
            )

security_monitoring = SecurityMonitoring()
```

This security guide provides comprehensive coverage of all security aspects of the MergeMind system, from authentication and authorization to compliance and incident response.
