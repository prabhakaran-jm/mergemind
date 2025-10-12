#!/usr/bin/env python3
"""
Encryption utilities for MergeMind.
"""

import os
import base64
import hashlib
import secrets
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import logging

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    """Encryption error."""
    pass

class SymmetricEncryption:
    """Symmetric encryption using Fernet."""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize symmetric encryption."""
        if key:
            self.key = key
        else:
            # Generate key from environment variable or create new one
            key_str = os.getenv('ENCRYPTION_KEY')
            if key_str:
                self.key = base64.urlsafe_b64decode(key_str.encode())
            else:
                self.key = Fernet.generate_key()
                logger.warning("No encryption key found, generated new one")
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data."""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self.cipher.encrypt(data)
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError("Encryption failed")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError("Decryption failed")
    
    def get_key(self) -> str:
        """Get encryption key as base64 string."""
        return base64.urlsafe_b64encode(self.key).decode('utf-8')

class AsymmetricEncryption:
    """Asymmetric encryption using RSA."""
    
    def __init__(self, private_key_path: Optional[str] = None, public_key_path: Optional[str] = None):
        """Initialize asymmetric encryption."""
        if private_key_path and os.path.exists(private_key_path):
            self.private_key = self._load_private_key(private_key_path)
            self.public_key = self.private_key.public_key()
        elif public_key_path and os.path.exists(public_key_path):
            self.public_key = self._load_public_key(public_key_path)
            self.private_key = None
        else:
            # Generate new key pair
            self.private_key, self.public_key = self._generate_key_pair()
            logger.warning("No RSA keys found, generated new key pair")
    
    def _generate_key_pair(self) -> tuple:
        """Generate RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def _load_private_key(self, path: str):
        """Load private key from file."""
        with open(path, 'rb') as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None
            )
    
    def _load_public_key(self, path: str):
        """Load public key from file."""
        with open(path, 'rb') as f:
            return serialization.load_pem_public_key(f.read())
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data with public key."""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self.public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"RSA encryption failed: {e}")
            raise EncryptionError("RSA encryption failed")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data with private key."""
        if not self.private_key:
            raise EncryptionError("Private key not available")
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"RSA decryption failed: {e}")
            raise EncryptionError("RSA decryption failed")
    
    def save_keys(self, private_key_path: str, public_key_path: str):
        """Save keys to files."""
        if self.private_key:
            with open(private_key_path, 'wb') as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
        
        with open(public_key_path, 'wb') as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

class PasswordEncryption:
    """Password encryption using PBKDF2."""
    
    def __init__(self, salt: Optional[bytes] = None):
        """Initialize password encryption."""
        self.salt = salt or secrets.token_bytes(16)
    
    def hash_password(self, password: str) -> str:
        """Hash password using PBKDF2."""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            salt_b64 = base64.urlsafe_b64encode(self.salt).decode()
            return f"{salt_b64}:{key.decode()}"
            
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise EncryptionError("Password hashing failed")
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            salt_b64, key_b64 = hashed_password.split(':')
            salt = base64.urlsafe_b64decode(salt_b64.encode())
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            return key.decode() == key_b64
            
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

class DataEncryption:
    """Data encryption for sensitive fields."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize data encryption."""
        self.symmetric = SymmetricEncryption(encryption_key.encode() if encryption_key else None)
    
    def encrypt_field(self, field_value: str, field_name: str = "data") -> str:
        """Encrypt a field value."""
        try:
            # Add field name as context
            context = f"{field_name}:{field_value}"
            return self.symmetric.encrypt(context)
            
        except Exception as e:
            logger.error(f"Field encryption failed: {e}")
            raise EncryptionError("Field encryption failed")
    
    def decrypt_field(self, encrypted_value: str, field_name: str = "data") -> str:
        """Decrypt a field value."""
        try:
            decrypted = self.symmetric.decrypt(encrypted_value)
            
            # Extract field value from context
            if decrypted.startswith(f"{field_name}:"):
                return decrypted[len(f"{field_name}:"):]
            else:
                raise EncryptionError("Invalid field context")
                
        except Exception as e:
            logger.error(f"Field decryption failed: {e}")
            raise EncryptionError("Field decryption failed")
    
    def encrypt_sensitive_data(self, data: dict) -> dict:
        """Encrypt sensitive fields in data dictionary."""
        sensitive_fields = ['email', 'phone', 'ssn', 'credit_card', 'password']
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt_field(encrypted_data[field], field)
        
        return encrypted_data
    
    def decrypt_sensitive_data(self, data: dict) -> dict:
        """Decrypt sensitive fields in data dictionary."""
        sensitive_fields = ['email', 'phone', 'ssn', 'credit_card', 'password']
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_field(decrypted_data[field], field)
                except EncryptionError:
                    # Keep original value if decryption fails
                    pass
        
        return decrypted_data

class FileEncryption:
    """File encryption utilities."""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize file encryption."""
        if key:
            self.key = key
        else:
            # Generate key from environment or create new one
            key_str = os.getenv('FILE_ENCRYPTION_KEY')
            if key_str:
                self.key = base64.urlsafe_b64decode(key_str.encode())
            else:
                self.key = secrets.token_bytes(32)
                logger.warning("No file encryption key found, generated new one")
    
    def encrypt_file(self, input_path: str, output_path: str) -> bool:
        """Encrypt a file."""
        try:
            with open(input_path, 'rb') as infile:
                data = infile.read()
            
            # Generate random IV
            iv = secrets.token_bytes(16)
            
            # Create cipher
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            # Pad data to block size
            block_size = 16
            padding_length = block_size - (len(data) % block_size)
            padded_data = data + bytes([padding_length] * padding_length)
            
            # Encrypt data
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Write IV + encrypted data
            with open(output_path, 'wb') as outfile:
                outfile.write(iv + encrypted_data)
            
            return True
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            return False
    
    def decrypt_file(self, input_path: str, output_path: str) -> bool:
        """Decrypt a file."""
        try:
            with open(input_path, 'rb') as infile:
                data = infile.read()
            
            # Extract IV and encrypted data
            iv = data[:16]
            encrypted_data = data[16:]
            
            # Create cipher
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            
            # Decrypt data
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Remove padding
            padding_length = decrypted_data[-1]
            decrypted_data = decrypted_data[:-padding_length]
            
            # Write decrypted data
            with open(output_path, 'wb') as outfile:
                outfile.write(decrypted_data)
            
            return True
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            return False
    
    def get_key(self) -> str:
        """Get encryption key as base64 string."""
        return base64.urlsafe_b64encode(self.key).decode('utf-8')

# Global instances
symmetric_encryption = SymmetricEncryption()
asymmetric_encryption = AsymmetricEncryption()
password_encryption = PasswordEncryption()
data_encryption = DataEncryption()
file_encryption = FileEncryption()

def encrypt_sensitive_field(field_value: str, field_name: str = "data") -> str:
    """Encrypt a sensitive field."""
    return data_encryption.encrypt_field(field_value, field_name)

def decrypt_sensitive_field(encrypted_value: str, field_name: str = "data") -> str:
    """Decrypt a sensitive field."""
    return data_encryption.decrypt_field(encrypted_value, field_name)

def hash_password(password: str) -> str:
    """Hash a password."""
    return password_encryption.hash_password(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return password_encryption.verify_password(password, hashed_password)

def encrypt_data(data: str) -> str:
    """Encrypt data."""
    return symmetric_encryption.encrypt(data)

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data."""
    return symmetric_encryption.decrypt(encrypted_data)
