"""
GitLab client for fetching merge request data and diffs.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class GitLabClient:
    """Client for GitLab API operations."""
    
    def __init__(self):
        """Initialize GitLab client."""
        self.base_url = os.getenv("GITLAB_BASE_URL", "https://gitlab.com")
        self.token = os.getenv("GITLAB_TOKEN")
        
        if not self.token:
            logger.warning("GITLAB_TOKEN not provided - GitLab operations will be limited")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        } if self.token else {}
        
        logger.info(f"GitLab client initialized for: {self.base_url}")
    
    async def get_merge_request(self, project_id: int, mr_id: int) -> Optional[Dict[str, Any]]:
        """
        Get merge request metadata.
        
        Args:
            project_id: GitLab project ID
            mr_id: Merge request ID
            
        Returns:
            Merge request data or None if not found
        """
        try:
            url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Merge request {mr_id} not found in project {project_id}")
                    return None
                else:
                    logger.error(f"GitLab API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to fetch merge request {mr_id}: {e}")
            return None
    
    async def get_merge_request_diff(self, project_id: int, mr_id: int, 
                                   max_files: int = 20, max_hunk_size: int = 1000) -> Optional[str]:
        """
        Get merge request diff with size limits.
        
        Args:
            project_id: GitLab project ID
            mr_id: Merge request ID
            max_files: Maximum number of files to include
            max_hunk_size: Maximum size of each diff hunk
            
        Returns:
            Trimmed diff content or None if not found
        """
        try:
            url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_id}/changes"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=15.0)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._trim_diff(data, max_files, max_hunk_size)
                elif response.status_code == 404:
                    logger.warning(f"Merge request {mr_id} changes not found")
                    return None
                else:
                    logger.error(f"GitLab API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to fetch diff for MR {mr_id}: {e}")
            return None
    
    def _trim_diff(self, changes_data: Dict[str, Any], max_files: int, max_hunk_size: int) -> str:
        """
        Trim diff content to manageable size.
        
        Args:
            changes_data: GitLab changes API response
            max_files: Maximum number of files to include
            max_hunk_size: Maximum size of each diff hunk
            
        Returns:
            Trimmed diff content
        """
        try:
            changes = changes_data.get("changes", [])
            
            if not changes:
                return ""
            
            # Limit number of files
            limited_changes = changes[:max_files]
            
            diff_parts = []
            
            for change in limited_changes:
                old_path = change.get("old_path", "")
                new_path = change.get("new_path", "")
                diff_content = change.get("diff", "")
                
                # Add file header
                if old_path != new_path:
                    diff_parts.append(f"--- {old_path}\n+++ {new_path}")
                else:
                    diff_parts.append(f"--- {old_path}\n+++ {new_path}")
                
                # Trim diff content
                if diff_content:
                    lines = diff_content.split('\n')
                    trimmed_lines = lines[:max_hunk_size]
                    diff_parts.append('\n'.join(trimmed_lines))
                    
                    if len(lines) > max_hunk_size:
                        diff_parts.append(f"... ({len(lines) - max_hunk_size} more lines)")
                
                diff_parts.append("")  # Empty line between files
            
            return '\n'.join(diff_parts)
            
        except Exception as e:
            logger.error(f"Failed to trim diff: {e}")
            return ""
    
    async def get_project_info(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Get project information.
        
        Args:
            project_id: GitLab project ID
            
        Returns:
            Project data or None if not found
        """
        try:
            url = f"{self.base_url}/api/v4/projects/{project_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Project {project_id} not found")
                    return None
                else:
                    logger.error(f"GitLab API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to fetch project {project_id}: {e}")
            return None
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user information.
        
        Args:
            user_id: GitLab user ID
            
        Returns:
            User data or None if not found
        """
        try:
            url = f"{self.base_url}/api/v4/users/{user_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"User {user_id} not found")
                    return None
                else:
                    logger.error(f"GitLab API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to fetch user {user_id}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test GitLab connection."""
        try:
            # Simple test - try to get current user
            url = f"{self.base_url}/api/v4/user"
            
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, timeout=5.0)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"GitLab connection test failed: {e}")
            return False


# Global instance
gitlab_client = GitLabClient()
