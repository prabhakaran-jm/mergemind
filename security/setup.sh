#!/bin/bash
# Security setup script for MergeMind

set -e

echo "🔒 Setting up MergeMind security infrastructure..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✅ Prerequisites check passed."

# Create necessary directories
echo "📁 Creating security directories..."
mkdir -p security/secrets-manager
mkdir -p security/auth
mkdir -p security/encryption
mkdir -p security/logs
mkdir -p security/keys

# Set secure permissions
chmod 700 security/secrets-manager
chmod 700 security/auth
chmod 700 security/encryption
chmod 700 security/logs
chmod 700 security/keys

echo "✅ Security directories created."

# Install Python dependencies
echo "🔧 Installing Python dependencies..."

# Install secrets manager dependencies
if [ -f "security/secrets-manager/requirements.txt" ]; then
    pip3 install -r security/secrets-manager/requirements.txt
fi

# Install auth dependencies
if [ -f "security/auth/requirements.txt" ]; then
    pip3 install -r security/auth/requirements.txt
fi

# Install encryption dependencies
if [ -f "security/encryption/requirements.txt" ]; then
    pip3 install -r security/encryption/requirements.txt
fi

echo "✅ Dependencies installed."

# Generate initial encryption keys
echo "🔑 Generating encryption keys..."

# Generate encryption key for secrets manager
if [ ! -f "security/secrets-manager/.encryption_key" ]; then
    python3 -c "
from cryptography.fernet import Fernet
import os
os.makedirs('security/secrets-manager', exist_ok=True)
key = Fernet.generate_key()
with open('security/secrets-manager/.encryption_key', 'wb') as f:
    f.write(key)
print('Generated secrets manager encryption key')
"
fi

# Generate RSA key pair for asymmetric encryption
if [ ! -f "security/encryption/private_key.pem" ]; then
    python3 -c "
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os
os.makedirs('security/encryption', exist_ok=True)

# Generate private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Save private key
with open('security/encryption/private_key.pem', 'wb') as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Save public key
public_key = private_key.public_key()
with open('security/encryption/public_key.pem', 'wb') as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print('Generated RSA key pair')
"
fi

# Set secure permissions on key files
chmod 600 security/secrets-manager/.encryption_key
chmod 600 security/encryption/private_key.pem
chmod 644 security/encryption/public_key.pem

echo "✅ Encryption keys generated."

# Initialize secrets manager
echo "🔐 Initializing secrets manager..."

# Create initial secrets if they don't exist
if [ ! -f "security/secrets-manager/.secrets_store" ]; then
    python3 -c "
from security.secrets_manager.secrets_manager import SecretsManager
import os

# Set up environment variables for testing
os.environ['GCP_PROJECT_ID'] = 'mergemind-prod'
os.environ['GITLAB_BASE_URL'] = 'https://gitlab.com'
os.environ['GITLAB_TOKEN'] = 'glpat-test-token'

manager = SecretsManager()

# Set up initial secrets
secrets_to_set = {
    'gitlab-token': 'glpat-test-token',
    'api-secret-key': 'test-secret-key-12345',
    'jwt-secret-key': 'test-jwt-secret-key-67890',
    'encryption-key': 'test-encryption-key-abcdef'
}

for name, value in secrets_to_set.items():
    success = manager.set_secret(name, value, 'development')
    if success:
        print(f'Set secret: {name}')
    else:
        print(f'Failed to set secret: {name}')

print('Secrets manager initialized')
"
fi

echo "✅ Secrets manager initialized."

# Create security configuration
echo "⚙️ Creating security configuration..."

# Create security config file
cat > security/security_config.yml << EOF
# MergeMind Security Configuration

security:
  # Rate limiting
  rate_limits:
    max_requests_per_minute: 100
    max_requests_per_hour: 1000
    block_duration_minutes: 60
  
  # Authentication
  authentication:
    jwt_expiration_hours: 24
    session_timeout_hours: 24
    password_min_length: 8
    password_require_special_chars: true
  
  # Encryption
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
    data_classification:
      public: "no_encryption"
      internal: "symmetric_encryption"
      confidential: "symmetric_encryption"
      restricted: "asymmetric_encryption"
  
  # Audit logging
  audit_logging:
    enabled: true
    retention_days: 365
    log_level: "INFO"
    include_sensitive_data: false
  
  # Security headers
  security_headers:
    enabled: true
    hsts_max_age: 31536000
    csp_policy: "default-src 'self'"
    x_frame_options: "DENY"
    x_content_type_options: "nosniff"
  
  # Compliance
  compliance:
    gdpr:
      enabled: true
      data_retention_days: 2555  # 7 years
      right_to_be_forgotten: true
    soc2:
      enabled: true
      audit_logging: true
      access_control: true
    pci:
      enabled: false
      encryption_required: true
EOF

echo "✅ Security configuration created."

# Create security monitoring script
echo "📊 Creating security monitoring script..."

cat > security/monitor_security.py << 'EOF'
#!/usr/bin/env python3
"""
Security monitoring script for MergeMind.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add security modules to path
sys.path.append(str(Path(__file__).parent))

from security_middleware import security_middleware, security_audit
from secrets_manager.secrets_manager import secrets_manager

def check_security_status():
    """Check overall security status."""
    print("🔒 MergeMind Security Status Check")
    print("=" * 50)
    
    # Check secrets manager
    print("\n📋 Secrets Manager:")
    try:
        secrets_count = len(secrets_manager.list_secrets("production"))
        print(f"  ✅ Active secrets: {secrets_count}")
        
        # Check rotation schedule
        secrets_to_rotate = secrets_manager.check_rotation_schedule()
        if secrets_to_rotate:
            print(f"  ⚠️  Secrets needing rotation: {len(secrets_to_rotate)}")
            for secret in secrets_to_rotate:
                print(f"    - {secret}")
        else:
            print("  ✅ All secrets up to date")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check security middleware
    print("\n🛡️ Security Middleware:")
    try:
        stats = security_middleware.get_security_stats()
        print(f"  ✅ Blocked IPs: {stats['blocked_ips_count']}")
        print(f"  ✅ Suspicious IPs: {stats['suspicious_ips_count']}")
        print(f"  ✅ Total requests: {stats['total_requests']}")
        print(f"  ✅ Security events: {stats['security_events_count']}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check audit logs
    print("\n📝 Audit Logs:")
    try:
        report = security_audit.generate_security_report(24)
        print(f"  ✅ Events (24h): {report['total_events']}")
        print(f"  ✅ Failed access: {report['failed_access_attempts']}")
        print(f"  ✅ Suspicious activity: {report['suspicious_activity_events']}")
        print(f"  ✅ Unique IPs: {report['unique_ip_addresses']}")
        print(f"  ✅ Unique users: {report['unique_users']}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check log files
    print("\n📁 Log Files:")
    log_files = [
        "security/audit.log",
        "security/security_audit.log",
        "security/security_events.log",
        "security/secrets-manager/audit.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"  ✅ {log_file}: {size} bytes")
        else:
            print(f"  ⚠️  {log_file}: Not found")
    
    print("\n" + "=" * 50)
    print("Security status check completed.")

def check_recent_events(hours=24):
    """Check recent security events."""
    print(f"\n🔍 Recent Security Events (last {hours} hours)")
    print("=" * 50)
    
    try:
        events = security_audit.get_audit_trail(hours=hours)
        
        if not events:
            print("No events found.")
            return
        
        # Group events by type
        event_types = {}
        for event in events:
            event_type = event.get('event_type', 'unknown')
            if event_type not in event_types:
                event_types[event_type] = []
            event_types[event_type].append(event)
        
        for event_type, type_events in event_types.items():
            print(f"\n{event_type}: {len(type_events)} events")
            for event in type_events[-5:]:  # Show last 5 events
                timestamp = event.get('timestamp', 'unknown')
                print(f"  {timestamp}: {event.get('details', {})}")
                
    except Exception as e:
        print(f"Error checking events: {e}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MergeMind Security Monitor")
    parser.add_argument("--events", action="store_true", help="Show recent events")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back")
    
    args = parser.parse_args()
    
    check_security_status()
    
    if args.events:
        check_recent_events(args.hours)

if __name__ == "__main__":
    main()
EOF

chmod +x security/monitor_security.py

echo "✅ Security monitoring script created."

# Create security cleanup script
echo "🧹 Creating security cleanup script..."

cat > security/cleanup_security.py << 'EOF'
#!/usr/bin/env python3
"""
Security cleanup script for MergeMind.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add security modules to path
sys.path.append(str(Path(__file__).parent))

from security_middleware import security_middleware, security_audit
from secrets_manager.secrets_manager import secrets_manager

def cleanup_old_logs(days=30):
    """Clean up old log files."""
    print(f"🧹 Cleaning up logs older than {days} days...")
    
    log_files = [
        "security/audit.log",
        "security/security_audit.log", 
        "security/security_events.log",
        "security/secrets-manager/audit.log"
    ]
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    for log_file in log_files:
        if os.path.exists(log_file):
            file_time = os.path.getmtime(log_file)
            if file_time < cutoff_time:
                try:
                    os.remove(log_file)
                    print(f"  ✅ Removed: {log_file}")
                except Exception as e:
                    print(f"  ❌ Failed to remove {log_file}: {e}")
            else:
                print(f"  ⏭️  Keeping: {log_file}")

def cleanup_expired_sessions():
    """Clean up expired sessions."""
    print("🧹 Cleaning up expired sessions...")
    
    try:
        session_manager.cleanup_expired_sessions()
        print("  ✅ Expired sessions cleaned up")
    except Exception as e:
        print(f"  ❌ Error cleaning sessions: {e}")

def rotate_secrets():
    """Rotate secrets that need rotation."""
    print("🔄 Rotating secrets...")
    
    try:
        secrets_to_rotate = secrets_manager.check_rotation_schedule()
        
        if not secrets_to_rotate:
            print("  ✅ No secrets need rotation")
            return
        
        for secret_name in secrets_to_rotate:
            try:
                success = secrets_manager.rotate_secret(secret_name, "production")
                if success:
                    print(f"  ✅ Rotated: {secret_name}")
                else:
                    print(f"  ❌ Failed to rotate: {secret_name}")
            except Exception as e:
                print(f"  ❌ Error rotating {secret_name}: {e}")
                
    except Exception as e:
        print(f"  ❌ Error checking rotation schedule: {e}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MergeMind Security Cleanup")
    parser.add_argument("--logs", action="store_true", help="Clean up old logs")
    parser.add_argument("--sessions", action="store_true", help="Clean up expired sessions")
    parser.add_argument("--secrets", action="store_true", help="Rotate secrets")
    parser.add_argument("--all", action="store_true", help="Run all cleanup tasks")
    parser.add_argument("--days", type=int, default=30, help="Days to keep logs")
    
    args = parser.parse_args()
    
    if args.all or args.logs:
        cleanup_old_logs(args.days)
    
    if args.all or args.sessions:
        cleanup_expired_sessions()
    
    if args.all or args.secrets:
        rotate_secrets()
    
    if not any([args.logs, args.sessions, args.secrets, args.all]):
        parser.print_help()

if __name__ == "__main__":
    main()
EOF

chmod +x security/cleanup_security.py

echo "✅ Security cleanup script created."

# Create security test script
echo "🧪 Creating security test script..."

cat > security/test_security.py << 'EOF'
#!/usr/bin/env python3
"""
Security test script for MergeMind.
"""

import os
import sys
import time
from pathlib import Path

# Add security modules to path
sys.path.append(str(Path(__file__).parent))

from security_middleware import security_middleware, input_validation, security_audit
from secrets_manager.secrets_manager import secrets_manager
from auth.authentication import jwt_auth, password_auth
from encryption.encryption import symmetric_encryption, password_encryption

def test_secrets_manager():
    """Test secrets manager functionality."""
    print("🔐 Testing Secrets Manager...")
    
    try:
        # Test setting and getting secrets
        test_secret = "test-secret-value-12345"
        success = secrets_manager.set_secret("test-secret", test_secret, "development")
        
        if success:
            retrieved_secret = secrets_manager.get_secret("test-secret", "development")
            if retrieved_secret == test_secret:
                print("  ✅ Secret set and retrieved successfully")
            else:
                print("  ❌ Secret retrieval failed")
        else:
            print("  ❌ Secret setting failed")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_authentication():
    """Test authentication functionality."""
    print("🔑 Testing Authentication...")
    
    try:
        # Test password hashing
        password = "test-password-123"
        hashed = password_encryption.hash_password(password)
        
        if password_encryption.verify_password(password, hashed):
            print("  ✅ Password hashing and verification successful")
        else:
            print("  ❌ Password verification failed")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_encryption():
    """Test encryption functionality."""
    print("🔒 Testing Encryption...")
    
    try:
        # Test symmetric encryption
        test_data = "test-data-to-encrypt"
        encrypted = symmetric_encryption.encrypt(test_data)
        decrypted = symmetric_encryption.decrypt(encrypted)
        
        if decrypted == test_data:
            print("  ✅ Symmetric encryption successful")
        else:
            print("  ❌ Symmetric encryption failed")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_input_validation():
    """Test input validation."""
    print("✅ Testing Input Validation...")
    
    try:
        # Test email validation
        valid_email = "test@example.com"
        invalid_email = "invalid-email"
        
        if input_validation.validate_email(valid_email):
            print("  ✅ Email validation successful")
        else:
            print("  ❌ Email validation failed")
            
        if not input_validation.validate_email(invalid_email):
            print("  ✅ Invalid email rejection successful")
        else:
            print("  ❌ Invalid email rejection failed")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_security_middleware():
    """Test security middleware."""
    print("🛡️ Testing Security Middleware...")
    
    try:
        # Test rate limiting
        test_ip = "127.0.0.1"
        
        # Should allow first request
        if security_middleware.check_rate_limit(test_ip):
            print("  ✅ Rate limiting allows first request")
        else:
            print("  ❌ Rate limiting blocks first request")
            
        # Test security headers
        headers = security_middleware.get_security_headers()
        if headers:
            print("  ✅ Security headers generated")
        else:
            print("  ❌ Security headers generation failed")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    """Main function."""
    print("🧪 MergeMind Security Test Suite")
    print("=" * 50)
    
    test_secrets_manager()
    test_authentication()
    test_encryption()
    test_input_validation()
    test_security_middleware()
    
    print("\n" + "=" * 50)
    print("Security tests completed.")

if __name__ == "__main__":
    main()
EOF

chmod +x security/test_security.py

echo "✅ Security test script created."

# Create security documentation
echo "📚 Creating security documentation..."

cat > security/README.md << 'EOF'
# MergeMind Security Infrastructure

Comprehensive security implementation for the MergeMind system, including secrets management, authentication, encryption, and security monitoring.

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Security Layer"
        SM[Secrets Manager]
        AUTH[Authentication]
        ENC[Encryption]
        MW[Security Middleware]
    end
    
    subgraph "Application Layer"
        API[FastAPI Application]
        UI[React Application]
    end
    
    subgraph "Data Layer"
        BQ[BigQuery]
        GL[GitLab API]
        VAI[Vertex AI]
    end
    
    API --> SM
    API --> AUTH
    API --> ENC
    API --> MW
    
    UI --> AUTH
    BOT --> AUTH
    
    SM --> BQ
    AUTH --> GL
    ENC --> VAI
```

## 📦 Components

### Secrets Management
- **Encrypted Storage**: All secrets encrypted at rest
- **Rotation**: Automated secret rotation
- **Access Control**: Role-based access to secrets
- **Audit Logging**: Complete audit trail

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **API Keys**: API key authentication
- **Password Auth**: Secure password authentication
- **RBAC**: Role-based access control

### Encryption
- **Symmetric**: AES-256 encryption for data
- **Asymmetric**: RSA encryption for keys
- **Password Hashing**: PBKDF2 password hashing
- **Field Encryption**: Sensitive field encryption

### Security Middleware
- **Rate Limiting**: Request rate limiting
- **Input Validation**: Input sanitization
- **Security Headers**: Security headers
- **Audit Logging**: Security event logging

## 🚀 Quick Start

### Setup
```bash
# Run security setup
./security/setup.sh

# Test security components
python3 security/test_security.py

# Monitor security status
python3 security/monitor_security.py
```

### Usage Examples

#### Secrets Management
```python
from security.secrets_manager.secrets_manager import get_secret, set_secret

# Get a secret
gitlab_token = get_secret("gitlab-token", "production")

# Set a secret
set_secret("new-secret", "secret-value", "production")
```

#### Authentication
```python
from security.auth.authentication import jwt_auth, require_auth

# Create JWT token
token = jwt_auth.create_token(user)

# Validate token
payload = jwt_auth.validate_token(token)

# Require authentication
@require_auth
def protected_endpoint():
    pass
```

#### Encryption
```python
from security.encryption.encryption import encrypt_data, decrypt_data

# Encrypt data
encrypted = encrypt_data("sensitive-data")

# Decrypt data
decrypted = decrypt_data(encrypted)
```

#### Security Middleware
```python
from security.security_middleware import security_middleware, require_security_check

# Check rate limit
if security_middleware.check_rate_limit(ip_address):
    # Process request
    pass

# Require security check
@require_security_check
def secure_endpoint():
    pass
```

## ⚙️ Configuration

### Environment Variables
```bash
# Encryption keys
ENCRYPTION_KEY=your-encryption-key
FILE_ENCRYPTION_KEY=your-file-encryption-key
JWT_SECRET_KEY=your-jwt-secret-key

# API keys
API_KEY_PROD=your-production-api-key
API_KEY_STAGING=your-staging-api-key

# User credentials
USER_ADMIN_PASSWORD=admin-password
USER_ANALYST_PASSWORD=analyst-password
```

### Security Configuration
```yaml
# security/security_config.yml
security:
  rate_limits:
    max_requests_per_minute: 100
    max_requests_per_hour: 1000
  
  authentication:
    jwt_expiration_hours: 24
    session_timeout_hours: 24
  
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
```

## 🔧 Management

### Secrets Management
```bash
# List secrets
python3 security/secrets-manager/cli.py list

# Get secret
python3 security/secrets-manager/cli.py get gitlab-token

# Set secret
python3 security/secrets-manager/cli.py set new-secret "secret-value"

# Rotate secret
python3 security/secrets-manager/cli.py rotate gitlab-token

# Export secrets
python3 security/secrets-manager/cli.py export --environment production
```

### Security Monitoring
```bash
# Check security status
python3 security/monitor_security.py

# Check recent events
python3 security/monitor_security.py --events --hours 24

# Generate security report
python3 security/monitor_security.py --report
```

### Security Cleanup
```bash
# Clean up old logs
python3 security/cleanup_security.py --logs --days 30

# Clean up expired sessions
python3 security/cleanup_security.py --sessions

# Rotate secrets
python3 security/cleanup_security.py --secrets

# Run all cleanup tasks
python3 security/cleanup_security.py --all
```

## 🔒 Security Features

### Data Protection
- **Encryption at Rest**: All sensitive data encrypted
- **Encryption in Transit**: HTTPS/TLS for all communications
- **Field-level Encryption**: Sensitive fields encrypted
- **Key Management**: Secure key storage and rotation

### Access Control
- **Authentication**: Multiple authentication methods
- **Authorization**: Role-based access control
- **Session Management**: Secure session handling
- **API Security**: API key and token authentication

### Monitoring & Auditing
- **Audit Logging**: Complete audit trail
- **Security Events**: Security event monitoring
- **Access Logging**: User access logging
- **Compliance**: GDPR, SOC2 compliance

### Threat Protection
- **Rate Limiting**: DDoS protection
- **Input Validation**: SQL injection prevention
- **XSS Protection**: Cross-site scripting prevention
- **CSRF Protection**: Cross-site request forgery prevention

## 📊 Monitoring

### Security Metrics
- **Authentication Events**: Login attempts, failures
- **Authorization Events**: Permission checks, denials
- **Security Events**: Suspicious activity, blocks
- **Access Patterns**: User behavior analysis

### Alerting
- **Failed Authentication**: Multiple failed login attempts
- **Suspicious Activity**: Unusual access patterns
- **Security Violations**: Policy violations
- **System Compromise**: Potential security breaches

## 🚨 Incident Response

### Security Incidents
1. **Detection**: Automated threat detection
2. **Assessment**: Impact and severity assessment
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threats
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Post-incident review

### Response Procedures
- **Immediate**: Block suspicious IPs
- **Short-term**: Rotate compromised secrets
- **Long-term**: Update security policies
- **Prevention**: Implement additional safeguards

## 📚 Compliance

### GDPR Compliance
- **Data Minimization**: Collect only necessary data
- **Purpose Limitation**: Use data for stated purposes
- **Storage Limitation**: Limit data retention
- **Right to Erasure**: Data deletion capabilities
- **Data Portability**: Data export capabilities

### SOC2 Compliance
- **Security**: Protect against unauthorized access
- **Availability**: Ensure system availability
- **Processing Integrity**: Ensure data integrity
- **Confidentiality**: Protect confidential information
- **Privacy**: Protect personal information

## 🛠️ Development

### Adding New Security Features
1. **Design**: Plan security feature
2. **Implementation**: Implement securely
3. **Testing**: Security testing
4. **Review**: Security code review
5. **Deployment**: Secure deployment

### Security Testing
```bash
# Run security tests
python3 security/test_security.py

# Test specific components
python3 -m pytest security/tests/

# Security scan
python3 security/security_scan.py
```

## 📄 License

This security infrastructure is part of the MergeMind project and is licensed under the MIT License.
EOF

echo "✅ Security documentation created."

# Set final permissions
echo "🔐 Setting final permissions..."
chmod 700 security/
chmod 600 security/secrets-manager/.encryption_key
chmod 600 security/encryption/private_key.pem
chmod 644 security/encryption/public_key.pem
chmod 600 security/security_config.yml

echo ""
echo "🎉 Security infrastructure setup complete!"
echo ""
echo "📊 Security Components:"
echo "   ✅ Secrets Manager - Encrypted secret storage"
echo "   ✅ Authentication - JWT, API key, password auth"
echo "   ✅ Encryption - Symmetric and asymmetric encryption"
echo "   ✅ Security Middleware - Rate limiting, validation"
echo "   ✅ Audit Logging - Complete audit trail"
echo "   ✅ Monitoring - Security status monitoring"
echo "   ✅ Cleanup - Automated security cleanup"
echo "   ✅ Testing - Security component testing"
echo ""
echo "🔧 Management Commands:"
echo "   Monitor: python3 security/monitor_security.py"
echo "   Cleanup: python3 security/cleanup_security.py --all"
echo "   Test: python3 security/test_security.py"
echo "   Secrets: python3 security/secrets-manager/cli.py list"
echo ""
echo "📚 Documentation: security/README.md"
echo ""
echo "⚠️  Important Security Notes:"
echo "   - Keep encryption keys secure"
echo "   - Regularly rotate secrets"
echo "   - Monitor security events"
echo "   - Review audit logs"
echo "   - Update security policies"
