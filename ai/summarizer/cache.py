"""
In-memory TTL cache for diff summaries.
"""

import time
import threading
from typing import Dict, Any, Optional
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class SummaryCache:
    """Thread-safe in-memory cache with TTL."""
    
    def __init__(self, ttl_seconds: int = 900):  # 15 minutes default
        """
        Initialize cache with TTL.
        
        Args:
            ttl_seconds: Time to live in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        logger.info(f"Summary cache initialized with TTL: {ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check if expired
            if self._is_expired(key):
                self._remove(key)
                return None
            
            # Move to end (LRU)
            value = self._cache.pop(key)
            self._cache[key] = value
            
            return value
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Remove if exists
            if key in self._cache:
                self._remove(key)
            
            # Add new entry
            self._cache[key] = value
            self._timestamps[key] = time.time()
            
            # Limit cache size (remove oldest if needed)
            if len(self._cache) > 1000:  # Max 1000 entries
                oldest_key = next(iter(self._cache))
                self._remove(oldest_key)
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [key for key in self._cache.keys() if self._is_expired(key)]
            
            for key in expired_keys:
                self._remove(key)
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for key in self._cache.keys() if self._is_expired(key))
            
            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_entries,
                "expired_entries": expired_entries,
                "ttl_seconds": self.ttl_seconds,
                "max_size": 1000
            }
    
    def _is_expired(self, key: str) -> bool:
        """Check if key is expired."""
        if key not in self._timestamps:
            return True
        
        return time.time() - self._timestamps[key] > self.ttl_seconds
    
    def _remove(self, key: str) -> None:
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
