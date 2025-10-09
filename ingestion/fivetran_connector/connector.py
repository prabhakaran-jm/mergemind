"""
Fivetran Connector for GitLab Merge Request Data
Extracts MR data, notes, pipelines, users, and projects from GitLab API
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Iterator
from datetime import datetime, timedelta
import requests
from fivetran_sdk import Connector, Table, Column, DataType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitLabConnector(Connector):
    """Fivetran connector for GitLab merge request data."""
    
    def __init__(self):
        """Initialize the connector."""
        super().__init__()
        self.gitlab_token = os.getenv("GITLAB_TOKEN")
        self.gitlab_base_url = os.getenv("GITLAB_BASE_URL", "https://gitlab.com")
        self.project_ids = self._get_project_ids()
        
        if not self.gitlab_token:
            raise ValueError("GITLAB_TOKEN environment variable is required")
        
        logger.info(f"GitLab connector initialized for {len(self.project_ids)} projects")
    
    def _get_project_ids(self) -> List[int]:
        """Get list of project IDs to sync."""
        # For demo purposes, use predefined project IDs
        # In production, this could be configured via environment variables
        project_ids_str = os.getenv("GITLAB_PROJECT_IDS", "100,101,102")
        return [int(pid.strip()) for pid in project_ids_str.split(",")]
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to GitLab API."""
        headers = {
            "Authorization": f"Bearer {self.gitlab_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GitLab API request failed: {e}")
            raise
    
    def _get_merge_requests(self, project_id: int, updated_after: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get merge requests for a project."""
        url = f"{self.gitlab_base_url}/api/v4/projects/{project_id}/merge_requests"
        
        params = {
            "state": "all",
            "per_page": 100,
            "order_by": "updated_at",
            "sort": "desc"
        }
        
        if updated_after:
            params["updated_after"] = updated_after.isoformat()
        
        all_mrs = []
        page = 1
        
        while True:
            params["page"] = page
            response = self._make_request(url, params)
            
            if not response:
                break
            
            all_mrs.extend(response)
            
            if len(response) < 100:  # Last page
                break
            
            page += 1
        
        logger.info(f"Retrieved {len(all_mrs)} merge requests for project {project_id}")
        return all_mrs
    
    def _get_mr_notes(self, project_id: int, mr_id: int) -> List[Dict[str, Any]]:
        """Get notes for a specific merge request."""
        url = f"{self.gitlab_base_url}/api/v4/projects/{project_id}/merge_requests/{mr_id}/notes"
        
        try:
            response = self._make_request(url)
            return response if response else []
        except Exception as e:
            logger.warning(f"Failed to get notes for MR {mr_id}: {e}")
            return []
    
    def _get_mr_pipelines(self, project_id: int, mr_id: int) -> List[Dict[str, Any]]:
        """Get pipelines for a specific merge request."""
        url = f"{self.gitlab_base_url}/api/v4/projects/{project_id}/merge_requests/{mr_id}/pipelines"
        
        try:
            response = self._make_request(url)
            return response if response else []
        except Exception as e:
            logger.warning(f"Failed to get pipelines for MR {mr_id}: {e}")
            return []
    
    def _get_project_info(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project information."""
        url = f"{self.gitlab_base_url}/api/v4/projects/{project_id}"
        
        try:
            return self._make_request(url)
        except Exception as e:
            logger.warning(f"Failed to get project info for {project_id}: {e}")
            return None
    
    def _get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information."""
        url = f"{self.gitlab_base_url}/api/v4/users/{user_id}"
        
        try:
            return self._make_request(url)
        except Exception as e:
            logger.warning(f"Failed to get user info for {user_id}: {e}")
            return None
    
    def _normalize_timestamp(self, timestamp_str: Optional[str]) -> Optional[str]:
        """Normalize timestamp to ISO format."""
        if not timestamp_str:
            return None
        
        try:
            # GitLab timestamps are already in ISO format
            return timestamp_str
        except Exception:
            return None
    
    def _extract_mr_data(self, mr: Dict[str, Any], project_id: int) -> Dict[str, Any]:
        """Extract and normalize merge request data."""
        return {
            "mr_id": mr["id"],
            "project_id": project_id,
            "title": mr.get("title", ""),
            "description": mr.get("description", ""),
            "author_id": mr["author"]["id"],
            "created_at": self._normalize_timestamp(mr.get("created_at")),
            "updated_at": self._normalize_timestamp(mr.get("updated_at")),
            "merged_at": self._normalize_timestamp(mr.get("merged_at")),
            "closed_at": self._normalize_timestamp(mr.get("closed_at")),
            "state": mr.get("state", ""),
            "source_branch": mr.get("source_branch", ""),
            "target_branch": mr.get("target_branch", ""),
            "web_url": mr.get("web_url", ""),
            "sha": mr.get("sha", ""),
            "merge_commit_sha": mr.get("merge_commit_sha"),
            "additions": mr.get("changes_count", {}).get("additions", 0),
            "deletions": mr.get("changes_count", {}).get("deletions", 0),
            "approvals_left": mr.get("approvals_left", 0),
            "labels": json.dumps(mr.get("labels", [])),
            "work_in_progress": mr.get("work_in_progress", False),
            "merge_status": mr.get("merge_status", ""),
            "has_conflicts": mr.get("has_conflicts", False),
            "blocking_discussions_resolved": mr.get("blocking_discussions_resolved", False)
        }
    
    def _extract_note_data(self, note: Dict[str, Any], project_id: int, mr_id: int) -> Dict[str, Any]:
        """Extract and normalize note data."""
        return {
            "note_id": note["id"],
            "project_id": project_id,
            "mr_id": mr_id,
            "author_id": note["author"]["id"],
            "created_at": self._normalize_timestamp(note.get("created_at")),
            "updated_at": self._normalize_timestamp(note.get("updated_at")),
            "body": note.get("body", ""),
            "note_type": self._classify_note_type(note.get("body", "")),
            "system": note.get("system", False),
            "resolved": note.get("resolved", False),
            "resolvable": note.get("resolvable", False)
        }
    
    def _classify_note_type(self, body: str) -> str:
        """Classify note type based on content."""
        body_lower = body.lower()
        
        if "approved" in body_lower or "approve" in body_lower:
            return "approval"
        elif "lgtm" in body_lower or "looks good" in body_lower:
            return "approval"
        elif "review" in body_lower or "reviewed" in body_lower:
            return "review"
        elif "comment" in body_lower or len(body) > 100:
            return "comment"
        else:
            return "comment"
    
    def _extract_pipeline_data(self, pipeline: Dict[str, Any], project_id: int, mr_id: int) -> Dict[str, Any]:
        """Extract and normalize pipeline data."""
        return {
            "pipeline_id": pipeline["id"],
            "project_id": project_id,
            "mr_id": mr_id,
            "status": pipeline.get("status", ""),
            "created_at": self._normalize_timestamp(pipeline.get("created_at")),
            "updated_at": self._normalize_timestamp(pipeline.get("updated_at")),
            "started_at": self._normalize_timestamp(pipeline.get("started_at")),
            "finished_at": self._normalize_timestamp(pipeline.get("finished_at")),
            "duration": pipeline.get("duration"),
            "web_url": pipeline.get("web_url", ""),
            "ref": pipeline.get("ref", ""),
            "sha": pipeline.get("sha", "")
        }
    
    def _extract_project_data(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize project data."""
        return {
            "project_id": project["id"],
            "name": project.get("name", ""),
            "path": project.get("path", ""),
            "path_with_namespace": project.get("path_with_namespace", ""),
            "description": project.get("description", ""),
            "created_at": self._normalize_timestamp(project.get("created_at")),
            "last_activity_at": self._normalize_timestamp(project.get("last_activity_at")),
            "visibility": project.get("visibility", ""),
            "web_url": project.get("web_url", ""),
            "default_branch": project.get("default_branch", ""),
            "archived": project.get("archived", False),
            "forked_from_project": project.get("forked_from_project", {}).get("id") if project.get("forked_from_project") else None
        }
    
    def _extract_user_data(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize user data."""
        return {
            "user_id": user["id"],
            "name": user.get("name", ""),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "created_at": self._normalize_timestamp(user.get("created_at")),
            "last_activity_on": user.get("last_activity_on"),
            "state": user.get("state", ""),
            "avatar_url": user.get("avatar_url", ""),
            "web_url": user.get("web_url", ""),
            "is_admin": user.get("is_admin", False),
            "can_create_group": user.get("can_create_group", False),
            "can_create_project": user.get("can_create_project", False)
        }
    
    def get_schema(self) -> List[Table]:
        """Define the schema for all tables."""
        return [
            # Merge Requests table
            Table(
                name="merge_requests",
                columns=[
                    Column(name="mr_id", data_type=DataType.INTEGER, primary_key=True),
                    Column(name="project_id", data_type=DataType.INTEGER),
                    Column(name="title", data_type=DataType.STRING),
                    Column(name="description", data_type=DataType.STRING),
                    Column(name="author_id", data_type=DataType.INTEGER),
                    Column(name="created_at", data_type=DataType.TIMESTAMP),
                    Column(name="updated_at", data_type=DataType.TIMESTAMP),
                    Column(name="merged_at", data_type=DataType.TIMESTAMP),
                    Column(name="closed_at", data_type=DataType.TIMESTAMP),
                    Column(name="state", data_type=DataType.STRING),
                    Column(name="source_branch", data_type=DataType.STRING),
                    Column(name="target_branch", data_type=DataType.STRING),
                    Column(name="web_url", data_type=DataType.STRING),
                    Column(name="sha", data_type=DataType.STRING),
                    Column(name="merge_commit_sha", data_type=DataType.STRING),
                    Column(name="additions", data_type=DataType.INTEGER),
                    Column(name="deletions", data_type=DataType.INTEGER),
                    Column(name="approvals_left", data_type=DataType.INTEGER),
                    Column(name="labels", data_type=DataType.STRING),
                    Column(name="work_in_progress", data_type=DataType.BOOLEAN),
                    Column(name="merge_status", data_type=DataType.STRING),
                    Column(name="has_conflicts", data_type=DataType.BOOLEAN),
                    Column(name="blocking_discussions_resolved", data_type=DataType.BOOLEAN)
                ]
            ),
            
            # MR Notes table
            Table(
                name="mr_notes",
                columns=[
                    Column(name="note_id", data_type=DataType.INTEGER, primary_key=True),
                    Column(name="project_id", data_type=DataType.INTEGER),
                    Column(name="mr_id", data_type=DataType.INTEGER),
                    Column(name="author_id", data_type=DataType.INTEGER),
                    Column(name="created_at", data_type=DataType.TIMESTAMP),
                    Column(name="updated_at", data_type=DataType.TIMESTAMP),
                    Column(name="body", data_type=DataType.STRING),
                    Column(name="note_type", data_type=DataType.STRING),
                    Column(name="system", data_type=DataType.BOOLEAN),
                    Column(name="resolved", data_type=DataType.BOOLEAN),
                    Column(name="resolvable", data_type=DataType.BOOLEAN)
                ]
            ),
            
            # Pipelines table
            Table(
                name="pipelines",
                columns=[
                    Column(name="pipeline_id", data_type=DataType.INTEGER, primary_key=True),
                    Column(name="project_id", data_type=DataType.INTEGER),
                    Column(name="mr_id", data_type=DataType.INTEGER),
                    Column(name="status", data_type=DataType.STRING),
                    Column(name="created_at", data_type=DataType.TIMESTAMP),
                    Column(name="updated_at", data_type=DataType.TIMESTAMP),
                    Column(name="started_at", data_type=DataType.TIMESTAMP),
                    Column(name="finished_at", data_type=DataType.TIMESTAMP),
                    Column(name="duration", data_type=DataType.INTEGER),
                    Column(name="web_url", data_type=DataType.STRING),
                    Column(name="ref", data_type=DataType.STRING),
                    Column(name="sha", data_type=DataType.STRING)
                ]
            ),
            
            # Projects table
            Table(
                name="projects",
                columns=[
                    Column(name="project_id", data_type=DataType.INTEGER, primary_key=True),
                    Column(name="name", data_type=DataType.STRING),
                    Column(name="path", data_type=DataType.STRING),
                    Column(name="path_with_namespace", data_type=DataType.STRING),
                    Column(name="description", data_type=DataType.STRING),
                    Column(name="created_at", data_type=DataType.TIMESTAMP),
                    Column(name="last_activity_at", data_type=DataType.TIMESTAMP),
                    Column(name="visibility", data_type=DataType.STRING),
                    Column(name="web_url", data_type=DataType.STRING),
                    Column(name="default_branch", data_type=DataType.STRING),
                    Column(name="archived", data_type=DataType.BOOLEAN),
                    Column(name="forked_from_project", data_type=DataType.INTEGER)
                ]
            ),
            
            # Users table
            Table(
                name="users",
                columns=[
                    Column(name="user_id", data_type=DataType.INTEGER, primary_key=True),
                    Column(name="name", data_type=DataType.STRING),
                    Column(name="username", data_type=DataType.STRING),
                    Column(name="email", data_type=DataType.STRING),
                    Column(name="created_at", data_type=DataType.TIMESTAMP),
                    Column(name="last_activity_on", data_type=DataType.DATE),
                    Column(name="state", data_type=DataType.STRING),
                    Column(name="avatar_url", data_type=DataType.STRING),
                    Column(name="web_url", data_type=DataType.STRING),
                    Column(name="is_admin", data_type=DataType.BOOLEAN),
                    Column(name="can_create_group", data_type=DataType.BOOLEAN),
                    Column(name="can_create_project", data_type=DataType.BOOLEAN)
                ]
            )
        ]
    
    def read(self, table: str, last_sync_time: Optional[datetime] = None) -> Iterator[Dict[str, Any]]:
        """Read data from GitLab API for the specified table."""
        logger.info(f"Reading data for table: {table}")
        
        if table == "merge_requests":
            for project_id in self.project_ids:
                mrs = self._get_merge_requests(project_id, last_sync_time)
                for mr in mrs:
                    yield self._extract_mr_data(mr, project_id)
        
        elif table == "mr_notes":
            for project_id in self.project_ids:
                mrs = self._get_merge_requests(project_id, last_sync_time)
                for mr in mrs:
                    notes = self._get_mr_notes(project_id, mr["id"])
                    for note in notes:
                        yield self._extract_note_data(note, project_id, mr["id"])
        
        elif table == "pipelines":
            for project_id in self.project_ids:
                mrs = self._get_merge_requests(project_id, last_sync_time)
                for mr in mrs:
                    pipelines = self._get_mr_pipelines(project_id, mr["id"])
                    for pipeline in pipelines:
                        yield self._extract_pipeline_data(pipeline, project_id, mr["id"])
        
        elif table == "projects":
            for project_id in self.project_ids:
                project = self._get_project_info(project_id)
                if project:
                    yield self._extract_project_data(project)
        
        elif table == "users":
            # Get unique user IDs from MRs and notes
            user_ids = set()
            for project_id in self.project_ids:
                mrs = self._get_merge_requests(project_id, last_sync_time)
                for mr in mrs:
                    user_ids.add(mr["author"]["id"])
                    
                    # Get notes to collect more user IDs
                    notes = self._get_mr_notes(project_id, mr["id"])
                    for note in notes:
                        user_ids.add(note["author"]["id"])
            
            for user_id in user_ids:
                user = self._get_user_info(user_id)
                if user:
                    yield self._extract_user_data(user)
        
        else:
            raise ValueError(f"Unknown table: {table}")


def main():
    """Main entry point for the connector."""
    connector = GitLabConnector()
    connector.run()


if __name__ == "__main__":
    main()
