#!/usr/bin/env python3
"""
Security middleware for MergeMind API.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
import hashlib
import secrets
import json

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for request validation and protection."""
    
    def __init__(self):
        """Initialize security middleware."""
        self.rate_limits = defaultdict(lambda: deque())
        self.blocked_ips = set()
        self.suspicious_ips = defaultdict(int)
        self.request_patterns = defaultdict(list)
        self.security_events = deque(maxlen=10000)
        
        # Configuration
        self.max_requests_per_minute = 100
        self.max_requests_per_hour = 1000
        self.block_duration_minutes = 60
        self.suspicious_threshold = 10
        
        # Security headers
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
    
    def check_rate_limit(self, ip_address: str) -> bool:
        """Check if IP address is within rate limits."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        # Clean old entries
        while self.rate_limits[ip_address] and self.rate_limits[ip_address][0] < minute_ago:
            self.rate_limits[ip_address].popleft()
        
        # Check minute limit
        if len(self.rate_limits[ip_address]) >= self.max_requests_per_minute:
            self._log_security_event('rate_limit_exceeded', {
                'ip_address': ip_address,
                'limit': self.max_requests_per_minute,
                'window': '1 minute'
            })
            return False
        
        # Add current request
        self.rate_limits[ip_address].append(now)
        
        return True
    
    def check_blocked_ip(self, ip_address: str) -> bool:
        """Check if IP address is blocked."""
        return ip_address in self.blocked_ips
    
    def block_ip(self, ip_address: str, reason: str):
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        self._log_security_event('ip_blocked', {
            'ip_address': ip_address,
            'reason': reason,
            'blocked_at': datetime.utcnow().isoformat()
        })
        logger.warning(f"IP address {ip_address} blocked: {reason}")
    
    def unblock_ip(self, ip_address: str):
        """Unblock an IP address."""
        self.blocked_ips.discard(ip_address)
        self._log_security_event('ip_unblocked', {
            'ip_address': ip_address,
            'unblocked_at': datetime.utcnow().isoformat()
        })
        logger.info(f"IP address {ip_address} unblocked")
    
    def check_suspicious_activity(self, ip_address: str, request_data: Dict[str, Any]) -> bool:
        """Check for suspicious activity patterns."""
        # Check for SQL injection patterns
        sql_patterns = ['union', 'select', 'insert', 'update', 'delete', 'drop', 'exec', 'script']
        request_string = json.dumps(request_data).lower()
        
        for pattern in sql_patterns:
            if pattern in request_string:
                self.suspicious_ips[ip_address] += 1
                self._log_security_event('suspicious_activity', {
                    'ip_address': ip_address,
                    'pattern': pattern,
                    'request_data': request_data
                })
                
                if self.suspicious_ips[ip_address] >= self.suspicious_threshold:
                    self.block_ip(ip_address, f"Suspicious activity: {pattern}")
                    return False
        
        # Check for XSS patterns
        xss_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
        for pattern in xss_patterns:
            if pattern in request_string:
                self.suspicious_ips[ip_address] += 1
                self._log_security_event('suspicious_activity', {
                    'ip_address': ip_address,
                    'pattern': pattern,
                    'request_data': request_data
                })
                
                if self.suspicious_ips[ip_address] >= self.suspicious_threshold:
                    self.block_ip(ip_address, f"Suspicious activity: {pattern}")
                    return False
        
        return True
    
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """Validate request data."""
        # Check for required fields
        required_fields = ['endpoint', 'method']
        for field in required_fields:
            if field not in request_data:
                return False
        
        # Validate endpoint format
        endpoint = request_data.get('endpoint', '')
        if not endpoint.startswith('/'):
            return False
        
        # Validate method
        method = request_data.get('method', '').upper()
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        if method not in allowed_methods:
            return False
        
        return True
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data."""
        if isinstance(data, str):
            # Remove potentially dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$']
            for char in dangerous_chars:
                data = data.replace(char, '')
            return data
        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token."""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Validate CSRF token."""
        return token == session_token
    
    def _log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log security event."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'data': event_data
        }
        self.security_events.append(event)
        
        # Log to file
        log_path = "security/security_events.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers."""
        return self.security_headers.copy()
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        return {
            'blocked_ips_count': len(self.blocked_ips),
            'suspicious_ips_count': len(self.suspicious_ips),
            'total_requests': sum(len(requests) for requests in self.rate_limits.values()),
            'security_events_count': len(self.security_events),
            'rate_limits_active': len(self.rate_limits)
        }

class InputValidation:
    """Input validation utilities."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def validate_mr_id(mr_id: str) -> bool:
        """Validate merge request ID."""
        try:
            mr_id_int = int(mr_id)
            return 1 <= mr_id_int <= 999999
        except ValueError:
            return False
    
    @staticmethod
    def validate_project_id(project_id: str) -> bool:
        """Validate project ID."""
        try:
            project_id_int = int(project_id)
            return 1 <= project_id_int <= 999999
        except ValueError:
            return False
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID."""
        try:
            user_id_int = int(user_id)
            return 1 <= user_id_int <= 999999
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return ""
        
        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$', '\n', '\r', '\t']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        return value.strip()

class SecurityAudit:
    """Security audit utilities."""
    
    def __init__(self):
        """Initialize security audit."""
        self.audit_log = deque(maxlen=10000)
    
    def log_access(self, user_id: str, resource: str, action: str, ip_address: str, 
                   user_agent: str, success: bool = True):
        """Log access attempt."""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'success': success
        }
        
        self.audit_log.append(audit_entry)
        
        # Log to file
        log_path = "security/audit.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        self.audit_log.append(event)
        
        # Log to file
        log_path = "security/security_audit.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def get_audit_trail(self, user_id: Optional[str] = None, 
                       resource: Optional[str] = None,
                       hours: int = 24) -> List[Dict[str, Any]]:
        """Get audit trail."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_entries = []
        for entry in self.audit_log:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            
            if entry_time < cutoff_time:
                continue
            
            if user_id and entry.get('user_id') != user_id:
                continue
            
            if resource and entry.get('resource') != resource:
                continue
            
            filtered_entries.append(entry)
        
        return filtered_entries
    
    def generate_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate security report."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        total_events = 0
        failed_access = 0
        suspicious_activity = 0
        ip_addresses = set()
        users = set()
        
        for entry in self.audit_log:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            
            if entry_time < cutoff_time:
                continue
            
            total_events += 1
            
            if not entry.get('success', True):
                failed_access += 1
            
            if entry.get('event_type') == 'suspicious_activity':
                suspicious_activity += 1
            
            if 'ip_address' in entry:
                ip_addresses.add(entry['ip_address'])
            
            if 'user_id' in entry:
                users.add(entry['user_id'])
        
        return {
            'report_period_hours': hours,
            'total_events': total_events,
            'failed_access_attempts': failed_access,
            'suspicious_activity_events': suspicious_activity,
            'unique_ip_addresses': len(ip_addresses),
            'unique_users': len(users),
            'generated_at': datetime.utcnow().isoformat()
        }

# Global instances
security_middleware = SecurityMiddleware()
input_validation = InputValidation()
security_audit = SecurityAudit()

def require_security_check(func):
    """Decorator to require security check."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get request data from context
        request_data = getattr(func, '_request_data', {})
        ip_address = request_data.get('ip_address', 'unknown')
        
        # Check if IP is blocked
        if security_middleware.check_blocked_ip(ip_address):
            security_audit.log_security_event('blocked_ip_access', {
                'ip_address': ip_address,
                'endpoint': request_data.get('endpoint', 'unknown')
            })
            raise SecurityError("IP address is blocked")
        
        # Check rate limit
        if not security_middleware.check_rate_limit(ip_address):
            security_audit.log_security_event('rate_limit_exceeded', {
                'ip_address': ip_address,
                'endpoint': request_data.get('endpoint', 'unknown')
            })
            raise SecurityError("Rate limit exceeded")
        
        # Check suspicious activity
        if not security_middleware.check_suspicious_activity(ip_address, request_data):
            security_audit.log_security_event('suspicious_activity_blocked', {
                'ip_address': ip_address,
                'endpoint': request_data.get('endpoint', 'unknown')
            })
            raise SecurityError("Suspicious activity detected")
        
        return func(*args, **kwargs)
    return wrapper

class SecurityError(Exception):
    """Security error."""
    pass