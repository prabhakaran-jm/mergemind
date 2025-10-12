"""
User service for user information lookup and management.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from services.bigquery_client import bigquery_client
from services.gitlab_client import gitlab_client

logger = logging.getLogger(__name__)


class UserService:
    """Service for user information and lookup."""
    
    def __init__(self):
        """Initialize user service."""
        self.bq_client = bigquery_client
        self.gitlab_client = gitlab_client
        self._user_cache = {}  # Simple in-memory cache
    
    def get_user_name(self, user_id: int) -> str:
        """
        Get user name by ID with caching.
        
        Args:
            user_id: User ID
            
        Returns:
            User name or fallback
        """
        try:
            # Check cache first
            if user_id in self._user_cache:
                return self._user_cache[user_id]
            
            # Try BigQuery first
            user_info = self._get_user_from_bigquery(user_id)
            if user_info:
                name = user_info.get("name") or user_info.get("username", f"User {user_id}")
                self._user_cache[user_id] = name
                return name
            
            # Fallback to GitLab API
            # Note: This would be async in real implementation
            # For now, return fallback
            fallback_name = f"User {user_id}"
            self._user_cache[user_id] = fallback_name
            return fallback_name
            
        except Exception as e:
            logger.error(f"Failed to get user name for {user_id}: {e}")
            return f"User {user_id}"
    
    def _get_user_from_bigquery(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information from BigQuery."""
        try:
            sql = """
            SELECT 
              user_id,
              username,
              name,
              email,
              state,
              created_at,
              last_activity_on
            FROM `mergemind_raw.users`
            WHERE user_id = @user_id
            LIMIT 1
            """
            
            results = self.bq_client.query(sql, user_id=user_id)
            
            if results:
                return results[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user from BigQuery for {user_id}: {e}")
            return None
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive user information.
        
        Args:
            user_id: User ID
            
        Returns:
            User information dictionary
        """
        try:
            # Get from BigQuery
            user_info = self._get_user_from_bigquery(user_id)
            
            if not user_info:
                return None
            
            # Add additional computed fields
            user_info["display_name"] = user_info.get("name") or user_info.get("username", f"User {user_id}")
            
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            return None
    
    def get_users_by_ids(self, user_ids: List[int]) -> Dict[int, str]:
        """
        Get user names for multiple user IDs.
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            Dictionary mapping user_id to user_name
        """
        try:
            result = {}
            
            for user_id in user_ids:
                result[user_id] = self.get_user_name(user_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get users by IDs: {e}")
            return {user_id: f"User {user_id}" for user_id in user_ids}
    
    def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search users by name or username.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        try:
            sql = """
            SELECT 
              user_id,
              username,
              name,
              email,
              state,
              created_at,
              last_activity_on
            FROM `mergemind_raw.users`
            WHERE 
              LOWER(username) LIKE LOWER(@query) OR
              LOWER(name) LIKE LOWER(@query)
            ORDER BY 
              CASE 
                WHEN LOWER(username) = LOWER(@query) THEN 1
                WHEN LOWER(name) = LOWER(@query) THEN 2
                WHEN LOWER(username) LIKE LOWER(@query) THEN 3
                ELSE 4
              END,
              last_activity_on DESC
            LIMIT @limit
            """
            
            search_query = f"%{query}%"
            results = self.bq_client.query(sql, query=search_query, limit=limit)
            
            # Add display names
            for user in results:
                user["display_name"] = user.get("name") or user.get("username", f"User {user['user_id']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search users: {e}")
            return []
    
    def get_active_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get active users.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of active users
        """
        try:
            sql = """
            SELECT 
              user_id,
              username,
              name,
              email,
              state,
              created_at,
              last_activity_on
            FROM `mergemind_raw.users`
            WHERE state = 'active'
            ORDER BY last_activity_on DESC
            LIMIT @limit
            """
            
            results = self.bq_client.query(sql, limit=limit)
            
            # Add display names
            for user in results:
                user["display_name"] = user.get("name") or user.get("username", f"User {user['user_id']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []
    
    def clear_cache(self):
        """Clear user cache."""
        self._user_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_users": len(self._user_cache),
            "cache_keys": list(self._user_cache.keys())
        }


# Global user service instance
user_service = UserService()
