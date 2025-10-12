#!/usr/bin/env python3
"""
Authentication and authorization system for MergeMind.
"""

import os
import jwt
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles."""
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class Permission(Enum):
    """Permissions."""
    READ_MRS = "read:mrs"
    WRITE_MRS = "write:mrs"
    READ_ANALYTICS = "read:analytics"
    WRITE_ANALYTICS = "write:analytics"
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    READ_SECRETS = "read:secrets"
    WRITE_SECRETS = "write:secrets"

@dataclass
class User:
    """User model."""
    user_id: str
    username: str
    email: str
    role: UserRole
    permissions: List[Permission]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = None

@dataclass
class Session:
    """Session model."""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True

class AuthenticationError(Exception):
    """Authentication error."""
    pass

class AuthorizationError(Exception):
    """Authorization error."""
    pass

class JWTAuth:
    """JWT-based authentication."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """Initialize JWT auth."""
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'default-secret-key')
        self.algorithm = 'HS256'
        self.expiration_hours = 24
    
    def create_token(self, user: User, expires_in_hours: Optional[int] = None) -> str:
        """Create JWT token for user."""
        try:
            expiration_hours = expires_in_hours or self.expiration_hours
            payload = {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'role': user.role.value,
                'permissions': [p.value for p in user.permissions],
                'exp': datetime.utcnow() + timedelta(hours=expiration_hours),
                'iat': datetime.utcnow(),
                'jti': secrets.token_urlsafe(32)  # JWT ID for revocation
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"JWT token created for user {user.user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create JWT token: {e}")
            raise AuthenticationError("Failed to create authentication token")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is revoked
            if self._is_token_revoked(payload.get('jti')):
                raise AuthenticationError("Token has been revoked")
            
            logger.info(f"JWT token validated for user {payload['user_id']}")
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise AuthenticationError("Token validation failed")
    
    def revoke_token(self, token: str) -> bool:
        """Revoke JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get('jti')
            
            if jti:
                self._add_to_revocation_list(jti)
                logger.info(f"JWT token revoked: {jti}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    def _is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked."""
        # In production, this would check a database or cache
        # For now, we'll use a simple file-based approach
        revocation_file = "security/auth/.revoked_tokens"
        
        if not os.path.exists(revocation_file):
            return False
        
        try:
            with open(revocation_file, 'r') as f:
                revoked_tokens = f.read().splitlines()
                return jti in revoked_tokens
        except Exception:
            return False
    
    def _add_to_revocation_list(self, jti: str):
        """Add token to revocation list."""
        revocation_file = "security/auth/.revoked_tokens"
        
        try:
            os.makedirs(os.path.dirname(revocation_file), exist_ok=True)
            with open(revocation_file, 'a') as f:
                f.write(f"{jti}\n")
        except Exception as e:
            logger.error(f"Failed to add token to revocation list: {e}")

class APIKeyAuth:
    """API key-based authentication."""
    
    def __init__(self):
        """Initialize API key auth."""
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from storage."""
        # In production, this would load from a database
        # For now, we'll use environment variables
        api_keys = {}
        
        # Load from environment variables
        for key, value in os.environ.items():
            if key.startswith('API_KEY_'):
                key_name = key[8:]  # Remove 'API_KEY_' prefix
                api_keys[value] = {
                    'name': key_name,
                    'permissions': ['read:mrs', 'read:analytics'],
                    'expires_at': None,
                    'is_active': True
                }
        
        return api_keys
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validate API key."""
        if api_key not in self.api_keys:
            raise AuthenticationError("Invalid API key")
        
        key_info = self.api_keys[api_key]
        
        if not key_info['is_active']:
            raise AuthenticationError("API key is inactive")
        
        if key_info['expires_at'] and datetime.utcnow() > key_info['expires_at']:
            raise AuthenticationError("API key has expired")
        
        return key_info

class PasswordAuth:
    """Password-based authentication."""
    
    def __init__(self):
        """Initialize password auth."""
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from storage."""
        # In production, this would load from a database
        # For now, we'll use environment variables
        users = {}
        
        # Load from environment variables
        for key, value in os.environ.items():
            if key.startswith('USER_'):
                parts = key.split('_', 2)
                if len(parts) >= 3:
                    username = parts[1]
                    field = parts[2].lower()
                    
                    if username not in users:
                        users[username] = {}
                    
                    users[username][field] = value
        
        return users
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt).encode())
        return f"{salt}:{hash_obj.hexdigest()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            salt, hash_hex = hashed_password.split(':')
            hash_obj = hashlib.sha256()
            hash_obj.update((password + salt).encode())
            return hash_obj.hexdigest() == hash_hex
        except Exception:
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        if username not in self.users:
            return None
        
        user_info = self.users[username]
        stored_password = user_info.get('password')
        
        if not stored_password or not self.verify_password(password, stored_password):
            return None
        
        # Create user object
        user = User(
            user_id=user_info.get('user_id', username),
            username=username,
            email=user_info.get('email', ''),
            role=UserRole(user_info.get('role', 'viewer')),
            permissions=[Permission(p) for p in user_info.get('permissions', ['read:mrs']).split(',')],
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        return user

class AuthorizationManager:
    """Authorization manager."""
    
    def __init__(self):
        """Initialize authorization manager."""
        self.role_permissions = {
            UserRole.VIEWER: [Permission.READ_MRS],
            UserRole.ANALYST: [Permission.READ_MRS, Permission.READ_ANALYTICS],
            UserRole.ADMIN: [Permission.READ_MRS, Permission.WRITE_MRS, Permission.READ_ANALYTICS, Permission.WRITE_ANALYTICS, Permission.ADMIN_USERS],
            UserRole.SUPER_ADMIN: [p for p in Permission]  # All permissions
        }
    
    def has_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission."""
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        user_permissions = set(user.permissions)
        role_permissions = set(self.role_permissions.get(user.role, []))
        
        return permission in user_permissions or permission in role_permissions
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get current user from context
                current_user = getattr(func, '_current_user', None)
                
                if not current_user:
                    raise AuthorizationError("User not authenticated")
                
                if not self.has_permission(current_user, permission):
                    raise AuthorizationError(f"Permission {permission.value} required")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def check_resource_access(self, user: User, resource_type: str, resource_id: str) -> bool:
        """Check if user has access to specific resource."""
        # Implement resource-based access control
        # For now, return True for all resources
        return True

class SessionManager:
    """Session management."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions = {}  # In production, use database
        self.session_timeout_hours = 24
    
    def create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        """Create new session."""
        session_id = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        
        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            created_at=now,
            expires_at=now + timedelta(hours=self.session_timeout_hours),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        logger.info(f"Session created for user {user.user_id}")
        
        return session
    
    def validate_session(self, session_id: str) -> Optional[Session]:
        """Validate session."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        if not session.is_active:
            return None
        
        if datetime.utcnow() > session.expires_at:
            session.is_active = False
            return None
        
        return session
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke session."""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            logger.info(f"Session revoked: {session_id}")
            return True
        
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if now > session.expires_at
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global instances
jwt_auth = JWTAuth()
api_key_auth = APIKeyAuth()
password_auth = PasswordAuth()
authz_manager = AuthorizationManager()
session_manager = SessionManager()

def get_current_user() -> Optional[User]:
    """Get current user from context."""
    # This would be implemented based on your framework
    # For FastAPI, you'd get this from the request context
    return None

def require_auth(func):
    """Decorator to require authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = get_current_user()
        
        if not current_user:
            raise AuthenticationError("Authentication required")
        
        if not current_user.is_active:
            raise AuthenticationError("User account is inactive")
        
        # Set current user in function context
        func._current_user = current_user
        
        return func(*args, **kwargs)
    return wrapper

def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = get_current_user()
            
            if not current_user:
                raise AuthenticationError("Authentication required")
            
            if not authz_manager.has_permission(current_user, permission):
                raise AuthorizationError(f"Permission {permission.value} required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: UserRole):
    """Decorator to require specific role."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = get_current_user()
            
            if not current_user:
                raise AuthenticationError("Authentication required")
            
            if current_user.role != role and current_user.role != UserRole.SUPER_ADMIN:
                raise AuthorizationError(f"Role {role.value} required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
