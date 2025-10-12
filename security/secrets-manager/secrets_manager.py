#!/usr/bin/env python3
"""
Secrets management service for MergeMind.
Handles secure storage, retrieval, and rotation of secrets.
"""

import os
import json
import logging
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecretType(Enum):
    """Types of secrets."""
    API_TOKEN = "api-token"
    WEBHOOK_SECRET = "webhook-secret"
    BOT_TOKEN = "bot-token"
    SERVICE_ACCOUNT_KEY = "service-account-key"
    CONNECTION_STRING = "connection-string"
    SECRET_KEY = "secret-key"
    JWT_SECRET = "jwt-secret"
    ENCRYPTION_KEY = "encryption-key"
    BASIC_AUTH = "basic-auth"
    ADMIN_PASSWORD = "admin-password"
    DSN = "dsn"
    API_KEY = "api-key"

class AccessLevel(Enum):
    """Access levels for secrets."""
    READ_ONLY = "read-only"
    READ_WRITE = "read-write"
    ADMIN = "admin"

@dataclass
class SecretMetadata:
    """Metadata for a secret."""
    name: str
    description: str
    secret_type: SecretType
    rotation_schedule: str
    access_level: AccessLevel
    environments: List[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    last_rotated: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class SecretsManager:
    """Manages secrets securely with encryption and rotation."""
    
    def __init__(self, config_path: str = "security/secrets-manager/secrets.yml"):
        """Initialize secrets manager."""
        self.config_path = config_path
        self.secrets_config = self._load_config()
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.secrets_store = self._load_secrets_store()
        
        logger.info("Secrets manager initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load secrets configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Secrets configuration not found: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML configuration: {e}")
            return {}
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key."""
        key_path = "security/secrets-manager/.encryption_key"
        
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            # Generate new encryption key
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_path), exist_ok=True)
            with open(key_path, 'wb') as f:
                f.write(key)
            os.chmod(key_path, 0o600)  # Restrict permissions
            logger.info("Generated new encryption key")
            return key
    
    def _load_secrets_store(self) -> Dict[str, Any]:
        """Load encrypted secrets store."""
        store_path = "security/secrets-manager/.secrets_store"
        
        if os.path.exists(store_path):
            try:
                with open(store_path, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    return json.loads(decrypted_data.decode())
            except Exception as e:
                logger.error(f"Failed to load secrets store: {e}")
                return {}
        else:
            return {}
    
    def _save_secrets_store(self):
        """Save encrypted secrets store."""
        store_path = "security/secrets-manager/.secrets_store"
        
        try:
            data = json.dumps(self.secrets_store).encode()
            encrypted_data = self.cipher.encrypt(data)
            
            os.makedirs(os.path.dirname(store_path), exist_ok=True)
            with open(store_path, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(store_path, 0o600)  # Restrict permissions
        except Exception as e:
            logger.error(f"Failed to save secrets store: {e}")
    
    def get_secret(self, name: str, environment: str = "production") -> Optional[str]:
        """Get a secret value."""
        try:
            if name not in self.secrets_store:
                logger.warning(f"Secret not found: {name}")
                return None
            
            secret_data = self.secrets_store[name]
            
            # Check if secret exists for environment
            if environment not in secret_data.get("environments", {}):
                logger.warning(f"Secret {name} not available for environment {environment}")
                return None
            
            # Decrypt secret value
            encrypted_value = secret_data["environments"][environment]["value"]
            decrypted_value = self.cipher.decrypt(encrypted_value.encode()).decode()
            
            # Log access
            self._log_secret_access(name, environment, "read")
            
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Failed to get secret {name}: {e}")
            return None
    
    def set_secret(self, name: str, value: str, environment: str = "production", 
                   secret_type: SecretType = SecretType.SECRET_KEY) -> bool:
        """Set a secret value."""
        try:
            # Validate secret name
            if not self._validate_secret_name(name):
                return False
            
            # Encrypt secret value
            encrypted_value = self.cipher.encrypt(value.encode()).decode()
            
            # Get or create secret metadata
            if name not in self.secrets_store:
                self.secrets_store[name] = {
                    "metadata": {
                        "name": name,
                        "description": f"Secret: {name}",
                        "secret_type": secret_type.value,
                        "rotation_schedule": "90d",
                        "access_level": "read-write",
                        "environments": [],
                        "tags": [],
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    },
                    "environments": {}
                }
            
            # Set secret value for environment
            self.secrets_store[name]["environments"][environment] = {
                "value": encrypted_value,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Update metadata
            self.secrets_store[name]["metadata"]["updated_at"] = datetime.utcnow().isoformat()
            if environment not in self.secrets_store[name]["metadata"]["environments"]:
                self.secrets_store[name]["metadata"]["environments"].append(environment)
            
            # Save secrets store
            self._save_secrets_store()
            
            # Log access
            self._log_secret_access(name, environment, "write")
            
            logger.info(f"Secret {name} set for environment {environment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set secret {name}: {e}")
            return False
    
    def rotate_secret(self, name: str, environment: str = "production") -> bool:
        """Rotate a secret value."""
        try:
            if name not in self.secrets_store:
                logger.warning(f"Secret not found: {name}")
                return False
            
            secret_data = self.secrets_store[name]
            secret_type = SecretType(secret_data["metadata"]["secret_type"])
            
            # Generate new secret value based on type
            new_value = self._generate_secret_value(secret_type)
            
            # Set new secret value
            success = self.set_secret(name, new_value, environment, secret_type)
            
            if success:
                # Update rotation metadata
                self.secrets_store[name]["metadata"]["last_rotated"] = datetime.utcnow().isoformat()
                self._save_secrets_store()
                
                logger.info(f"Secret {name} rotated for environment {environment}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rotate secret {name}: {e}")
            return False
    
    def _generate_secret_value(self, secret_type: SecretType) -> str:
        """Generate a new secret value based on type."""
        if secret_type == SecretType.API_TOKEN:
            return self._generate_api_token()
        elif secret_type == SecretType.WEBHOOK_SECRET:
            return self._generate_webhook_secret()
        elif secret_type == SecretType.BOT_TOKEN:
            return self._generate_bot_token()
        elif secret_type == SecretType.SECRET_KEY:
            return self._generate_secret_key()
        elif secret_type == SecretType.JWT_SECRET:
            return self._generate_jwt_secret()
        elif secret_type == SecretType.ENCRYPTION_KEY:
            return Fernet.generate_key().decode()
        elif secret_type == SecretType.BASIC_AUTH:
            return self._generate_basic_auth()
        elif secret_type == SecretType.ADMIN_PASSWORD:
            return self._generate_admin_password()
        else:
            return self._generate_generic_secret()
    
    def _generate_api_token(self) -> str:
        """Generate API token."""
        return f"glpat-{self._generate_random_string(20)}"
    
    def _generate_webhook_secret(self) -> str:
        """Generate webhook secret."""
        return self._generate_random_string(32)
    
    def _generate_bot_token(self) -> str:
        """Generate bot token."""
        return f"xoxb-{self._generate_random_string(24)}"
    
    def _generate_secret_key(self) -> str:
        """Generate secret key."""
        return self._generate_random_string(32)
    
    def _generate_jwt_secret(self) -> str:
        """Generate JWT secret."""
        return self._generate_random_string(64)
    
    def _generate_basic_auth(self) -> str:
        """Generate basic auth credentials."""
        username = self._generate_random_string(8)
        password = self._generate_random_string(16)
        return base64.b64encode(f"{username}:{password}".encode()).decode()
    
    def _generate_admin_password(self) -> str:
        """Generate admin password."""
        return self._generate_random_string(16)
    
    def _generate_generic_secret(self) -> str:
        """Generate generic secret."""
        return self._generate_random_string(32)
    
    def _generate_random_string(self, length: int) -> str:
        """Generate random string."""
        alphabet = string.ascii_letters + string.digits + "_-"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _validate_secret_name(self, name: str) -> bool:
        """Validate secret name."""
        if not name or not isinstance(name, str):
            return False
        
        # Check for valid characters
        if not all(c.isalnum() or c in "_-" for c in name):
            return False
        
        # Check length
        if len(name) < 3 or len(name) > 50:
            return False
        
        return True
    
    def _log_secret_access(self, name: str, environment: str, action: str):
        """Log secret access for audit."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "secret_name": name,
            "environment": environment,
            "action": action,
            "user": os.getenv("USER", "unknown")
        }
        
        # Log to file
        log_path = "security/secrets-manager/audit.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def list_secrets(self, environment: str = "production") -> List[str]:
        """List available secrets for environment."""
        secrets_list = []
        
        for name, secret_data in self.secrets_store.items():
            if environment in secret_data.get("environments", {}):
                secrets_list.append(name)
        
        return secrets_list
    
    def get_secret_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get secret metadata."""
        if name not in self.secrets_store:
            return None
        
        return self.secrets_store[name]["metadata"]
    
    def check_rotation_schedule(self) -> List[str]:
        """Check which secrets need rotation."""
        secrets_to_rotate = []
        
        for name, secret_data in self.secrets_store.items():
            metadata = secret_data["metadata"]
            rotation_schedule = metadata.get("rotation_schedule", "90d")
            last_rotated = metadata.get("last_rotated")
            
            if last_rotated:
                last_rotated_date = datetime.fromisoformat(last_rotated)
                rotation_days = self._parse_rotation_schedule(rotation_schedule)
                
                if datetime.utcnow() - last_rotated_date > timedelta(days=rotation_days):
                    secrets_to_rotate.append(name)
        
        return secrets_to_rotate
    
    def _parse_rotation_schedule(self, schedule: str) -> int:
        """Parse rotation schedule string to days."""
        if schedule.endswith('d'):
            return int(schedule[:-1])
        elif schedule.endswith('w'):
            return int(schedule[:-1]) * 7
        elif schedule.endswith('m'):
            return int(schedule[:-1]) * 30
        elif schedule.endswith('y'):
            return int(schedule[:-1]) * 365
        else:
            return 90  # Default to 90 days
    
    def export_secrets(self, environment: str = "production") -> Dict[str, str]:
        """Export secrets for environment (for deployment)."""
        exported_secrets = {}
        
        for name in self.list_secrets(environment):
            value = self.get_secret(name, environment)
            if value:
                exported_secrets[name] = value
        
        return exported_secrets
    
    def import_secrets(self, secrets_dict: Dict[str, str], environment: str = "production"):
        """Import secrets from dictionary."""
        for name, value in secrets_dict.items():
            self.set_secret(name, value, environment)
        
        logger.info(f"Imported {len(secrets_dict)} secrets for environment {environment}")

# Global secrets manager instance
secrets_manager = SecretsManager()

def get_secret(name: str, environment: str = "production") -> Optional[str]:
    """Get a secret value."""
    return secrets_manager.get_secret(name, environment)

def set_secret(name: str, value: str, environment: str = "production") -> bool:
    """Set a secret value."""
    return secrets_manager.set_secret(name, value, environment)

def rotate_secret(name: str, environment: str = "production") -> bool:
    """Rotate a secret value."""
    return secrets_manager.rotate_secret(name, environment)

if __name__ == "__main__":
    # Example usage
    manager = SecretsManager()
    
    # Set a secret
    manager.set_secret("test-secret", "test-value", "development")
    
    # Get a secret
    value = manager.get_secret("test-secret", "development")
    print(f"Secret value: {value}")
    
    # List secrets
    secrets = manager.list_secrets("development")
    print(f"Available secrets: {secrets}")
    
    # Check rotation schedule
    to_rotate = manager.check_rotation_schedule()
    print(f"Secrets to rotate: {to_rotate}")
