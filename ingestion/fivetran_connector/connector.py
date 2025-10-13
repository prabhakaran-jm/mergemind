"""
Improved Fivetran Connector for GitLab Data with Incremental Syncs
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Iterator
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from fivetran_connector_sdk import Operations as op

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default configuration (will be overridden by Fivetran configuration)
DEFAULT_CONFIG = {
    "gitlab_token": os.getenv("GITLAB_TOKEN", ""),
    "gitlab_base_url": os.getenv("GITLAB_BASE_URL", "https://35.202.37.189.sslip.io"),
    "gitlab_project_ids": os.getenv("GITLAB_PROJECT_IDS", "4,5,6,7,8,9"),
    "start_date": "2024-01-01T00:00:00Z",
    "sync_projects_table": True,
    "sync_merge_requests_table": True,
    "sync_users_table": True,
    "max_records_per_sync": 10000,
    "sync_interval_hours": 1,
    # Dynamic discovery options
    "auto_discover_projects": False,
    "project_name_pattern": "*",
    "include_private_projects": True,
    "max_projects_to_sync": 100
}

logger.info("GitLab connector module loaded")

# Global cache for discovered projects
_discovered_projects = None
_last_discovery = None
_discovery_cache_ttl = 3600  # 1 hour cache


def get_headers(config: Dict[str, Any]) -> Dict[str, str]:
    """Get HTTP headers for GitLab API requests."""
    return {
        'Authorization': f'Bearer {config["gitlab_token"]}',
        'Content-Type': 'application/json'
    }


def discover_projects(config: Dict[str, Any], force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Dynamically discover GitLab projects based on configuration.
    
    Args:
        config: Configuration dictionary
        force_refresh: Force refresh of project discovery cache
        
    Returns:
        List of project dictionaries
    """
    global _discovered_projects, _last_discovery
    
    # Check cache first
    if (not force_refresh and 
        _discovered_projects and 
        _last_discovery and 
        (datetime.now() - _last_discovery).seconds < _discovery_cache_ttl):
        logger.info(f"Using cached project discovery ({len(_discovered_projects)} projects)")
        return _discovered_projects

    logger.info("Discovering GitLab projects dynamically...")
    
    try:
        projects = []
        page = 1
        per_page = 100
        max_projects = int(config.get("max_projects_to_sync", 1000))
        
        while len(projects) < max_projects:
            url = f"{config['gitlab_base_url']}/api/v4/projects"
            params = {
                'page': page,
                'per_page': per_page,
                'membership': True,  # Only projects user has access to
                'simple': False,
                'order_by': 'last_activity_at',
                'sort': 'desc'
            }
            
            # Add visibility filter
            if not config.get("include_private_projects", True):
                params['visibility'] = 'public'
            
            response = requests.get(url, headers=get_headers(config), params=params)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch projects: {response.status_code} - {response.text}")
                break
            
            page_projects = response.json()
            if not page_projects:
                break
            
            # Filter projects based on name pattern
            pattern = config.get("project_name_pattern", "*")
            for project in page_projects:
                if matches_project_pattern(project['name'], pattern):
                    projects.append({
                        'id': project['id'],
                        'name': project['name'],
                        'description': project.get('description', ''),
                        'web_url': project['web_url'],
                        'created_at': project['created_at'],
                        'updated_at': project['updated_at'],
                        'visibility': project['visibility'],
                        'default_branch': project.get('default_branch', 'main'),
                        'last_activity_at': project.get('last_activity_at'),
                        'star_count': project.get('star_count', 0),
                        'fork_count': project.get('fork_count', 0)
                    })
            
            # Check if we have more pages
            if len(page_projects) < per_page:
                break
                
            page += 1
        
        # Cache the results
        _discovered_projects = projects
        _last_discovery = datetime.now()
        
        logger.info(f"Discovered {len(projects)} projects matching pattern '{pattern}'")
        return projects
        
    except Exception as e:
        logger.error(f"Error discovering projects: {e}")
        return []


def matches_project_pattern(project_name: str, pattern: str) -> bool:
    """Check if project name matches the configured pattern."""
    if not pattern or pattern == "*":
        return True
        
    # Simple wildcard matching
    if '*' in pattern:
        import re
        regex_pattern = pattern.replace('*', '.*')
        return bool(re.match(regex_pattern, project_name, re.IGNORECASE))
    
    return project_name.lower() == pattern.lower()


def get_project_ids(config: Dict[str, Any]) -> List[int]:
    """Get list of project IDs to sync."""
    if config.get("auto_discover_projects", False):
        projects = discover_projects(config)
        return [p['id'] for p in projects]
    else:
        # Fallback to configured project IDs
        project_ids_str = config.get("gitlab_project_ids", "")
        return [int(pid.strip()) for pid in project_ids_str.split(',') if pid.strip()]


def schema(configuration: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Define the schema for GitLab data tables."""
    return [
        {
            "table": "projects",
            "primary_key": ["id"],
            "columns": {
                "id": "INT",
                "name": "STRING",
                "description": "STRING",
                "web_url": "STRING",
                "created_at": "UTC_DATETIME",
                "updated_at": "UTC_DATETIME",
                "visibility": "STRING",
                "default_branch": "STRING",
            }
        },
        {
            "table": "merge_requests",
            "primary_key": ["id"],
            "columns": {
                "id": "INT",
                "project_id": "INT",
                "title": "STRING",
                "description": "STRING",
                "state": "STRING",
                "author_id": "INT",
                "assignee_id": "INT",
                "created_at": "UTC_DATETIME",
                "updated_at": "UTC_DATETIME",
                "merged_at": "UTC_DATETIME",
                "closed_at": "UTC_DATETIME",
                "source_branch": "STRING",
                "target_branch": "STRING",
                "web_url": "STRING",
            }
        },
        {
            "table": "users",
            "primary_key": ["id"],
            "columns": {
                "id": "INT",
                "username": "STRING",
                "name": "STRING",
                "email": "STRING",
                "state": "STRING",
                "created_at": "UTC_DATETIME",
                "last_activity_on": "NAIVE_DATE",
            }
        },
    ]


def update(configuration: Dict[str, Any] = None, state: Dict[str, Any] = None) -> Iterator[Dict[str, Any]]:
    """Update method with incremental sync support."""
    logger.info("Starting incremental data sync")
    
    # Handle Fivetran's secrets_list format
    config = {**DEFAULT_CONFIG}
    
    if configuration:
        # Check if configuration has secrets_list (Fivetran format)
        if "secrets_list" in configuration:
            logger.info("Processing Fivetran secrets_list format")
            for secret in configuration["secrets_list"]:
                key = secret.get("key")
                value = secret.get("value")
                if key and value:
                    config[key] = value
        else:
            # Regular configuration format
            config.update(configuration)
    
    # Parse string values to appropriate types
    config["sync_projects_table"] = config.get("sync_projects_table", "true").lower() == "true"
    config["sync_merge_requests_table"] = config.get("sync_merge_requests_table", "true").lower() == "true"
    config["sync_users_table"] = config.get("sync_users_table", "true").lower() == "true"
    config["max_records_per_sync"] = int(config.get("max_records_per_sync", "10000"))
    config["sync_interval_hours"] = int(config.get("sync_interval_hours", "1"))
    config["auto_discover_projects"] = config.get("auto_discover_projects", "false").lower() == "true"
    config["include_private_projects"] = config.get("include_private_projects", "true").lower() == "true"
    
    logger.info(f"Configuration keys: {list(config.keys())}")
    
    # Validate required configuration
    if not config.get("gitlab_token"):
        logger.error(f"Missing gitlab_token. Available config keys: {list(config.keys())}")
        logger.error(f"Configuration received: {configuration}")
        raise ValueError("gitlab_token is required in configuration")
    
    # Get project IDs (dynamic discovery or configured)
    if config.get("auto_discover_projects", False):
        project_ids = get_project_ids(config)
        logger.info(f"GitLab connector initialized with dynamic discovery: {len(project_ids)} projects")
    else:
        project_ids = [int(pid.strip()) for pid in config['gitlab_project_ids'].split(",")]
        logger.info(f"GitLab connector initialized for configured projects: {','.join(map(str, project_ids))}")
    
    # Get last sync time from state for incremental sync
    last_sync_time = None
    if state and "last_sync_time" in state:
        try:
            last_sync_time = datetime.fromisoformat(state["last_sync_time"])
            logger.info(f"Last sync time: {last_sync_time}")
        except ValueError as e:
            logger.warning(f"Invalid last_sync_time format: {e}")
    else:
        # First run - use start_date from config to limit historical data
        if config.get("start_date"):
            try:
                last_sync_time = datetime.fromisoformat(config["start_date"].replace('Z', '+00:00'))
                logger.info(f"First sync - using start_date: {last_sync_time}")
            except ValueError as e:
                logger.warning(f"Invalid start_date format: {e}")
                last_sync_time = None
    
    # Record current sync start time
    current_sync_time = datetime.utcnow()
    
    # Initialize state for this sync
    sync_state = {"last_sync_time": current_sync_time.isoformat()}
    
    # 1. Sync Projects (always full sync for projects)
    if config.get("sync_projects_table", True):
        logger.info("Processing table: projects")
        project_count = 0
        
        if config.get("auto_discover_projects", False):
            # Use dynamic discovery
            projects = discover_projects(config)
            for project in projects:
                yield op.upsert("projects", {
                    "id": project["id"],
                    "name": project["name"],
                    "description": project.get("description", ""),
                    "web_url": project["web_url"],
                    "created_at": project["created_at"],
                    "updated_at": project["updated_at"],
                    "visibility": project["visibility"],
                    "default_branch": project.get("default_branch", ""),
                })
                project_count += 1
        else:
            # Use configured project IDs (legacy mode)
            for project_id in project_ids:
                project = _get_project_info(project_id, config)
                if project:
                    yield op.upsert("projects", {
                        "id": project["id"],
                        "name": project["name"],
                        "description": project.get("description", ""),
                        "web_url": project["web_url"],
                        "created_at": project["created_at"],
                        "updated_at": project["updated_at"],
                        "visibility": project["visibility"],
                        "default_branch": project.get("default_branch", ""),
                    })
                    project_count += 1
        
        logger.info(f"Successfully processed {project_count} records for table projects")
        
        # Save checkpoint after projects
        yield op.checkpoint(sync_state)
    else:
        logger.info("Skipping projects table sync (disabled in configuration)")
    
    # 2. Sync Merge Requests (incremental)
    if config.get("sync_merge_requests_table", True):
        logger.info("Processing table: merge_requests")
        mr_count = 0
        user_ids = set()  # Collect user IDs for later batch processing
        
        for project_id in project_ids:
            mrs = _get_merge_requests(project_id, updated_after=last_sync_time, config=config)
            for mr in mrs:
                yield op.upsert("merge_requests", {
                    "id": mr["id"],
                    "project_id": project_id,
                    "title": mr["title"],
                    "description": mr.get("description", ""),
                    "state": mr["state"],
                    "author_id": mr["author"]["id"],
                    "assignee_id": mr.get("assignee", {}).get("id") if mr.get("assignee") else None,
                    "created_at": mr["created_at"],
                    "updated_at": mr["updated_at"],
                    "merged_at": mr.get("merged_at"),
                    "closed_at": mr.get("closed_at"),
                    "source_branch": mr["source_branch"],
                    "target_branch": mr["target_branch"],
                    "web_url": mr["web_url"],
                })
                mr_count += 1
                
                # Collect user IDs for batch processing
                user_ids.add(mr["author"]["id"])
                if mr.get("assignee"):
                    user_ids.add(mr["assignee"]["id"])
        
        logger.info(f"Successfully processed {mr_count} records for table merge_requests")
        
        # Save checkpoint after merge requests
        yield op.checkpoint(sync_state)
    else:
        logger.info("Skipping merge_requests table sync (disabled in configuration)")
        user_ids = set()  # Initialize empty set if merge requests are skipped
    
    # 3. Sync Users (batch processing)
    if config.get("sync_users_table", True):
        logger.info("Processing table: users")
        user_count = 0
        
        if user_ids:
            # Batch fetch users to eliminate N+1 problem
            users = _get_users_batch(list(user_ids), config)
            for user in users:
                yield op.upsert("users", {
                    "id": user["id"],
                    "username": user["username"],
                    "name": user["name"],
                    "email": user.get("email", ""),
                    "state": user["state"],
                    "created_at": user["created_at"],
                    "last_activity_on": user.get("last_activity_on"),
                })
                user_count += 1
        
        logger.info(f"Successfully processed {user_count} records for table users")
    else:
        logger.info("Skipping users table sync (disabled in configuration)")
    
    # Save final state with sync completion time
    # Note: op.state() is not available in this SDK version, using op.checkpoint()
    yield op.checkpoint(sync_state)
    logger.info("Sync completed successfully")


def _make_request(url: str, params: Dict[str, Any] | List[tuple] = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make authenticated request to GitLab API with improved error handling."""
    config = config or DEFAULT_CONFIG
    headers = {
        "Authorization": f"Bearer {config['gitlab_token']}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Making request to: {url}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 404:
            logger.warning(f"Resource not found: {url}")
            return []
        
        if response.status_code == 429:
            logger.warning("Rate limit exceeded, waiting before retry")
            # Could implement exponential backoff here
            raise requests.exceptions.RequestException("Rate limit exceeded")
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"GitLab API request failed: {e}")
        logger.error(f"URL: {url}")
        logger.error(f"Status: {getattr(e.response, 'status_code', 'Unknown') if hasattr(e, 'response') else 'No response'}")
        # Re-raise critical errors instead of silently failing
        raise


def _get_merge_requests(project_id: int, updated_after: Optional[datetime] = None, config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Get merge requests for a project with incremental sync support."""
    config = config or DEFAULT_CONFIG
    url = f"{config['gitlab_base_url']}/api/v4/projects/{project_id}/merge_requests"
    
    params = {
        "per_page": 100,
        "state": "all"
    }
    
    if updated_after:
        params["updated_after"] = updated_after.isoformat()
        logger.info(f"Fetching merge requests updated after: {updated_after}")
    
    all_mrs = []
    page = 1
    
    while True:
        params["page"] = page
        response = _make_request(url, params, config)
        
        if not response:
            break
            
        all_mrs.extend(response)
        
        if len(response) < 100:  # Last page
            break
            
        page += 1
    
    logger.info(f"Fetched {len(all_mrs)} merge requests for project {project_id}")
    return all_mrs


def _get_project_info(project_id: int, config: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Get project information."""
    config = config or DEFAULT_CONFIG
    url = f"{config['gitlab_base_url']}/api/v4/projects/{project_id}"
    
    try:
        return _make_request(url, config=config)
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        return None


def _get_users_batch(user_ids: List[int], config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Get multiple users in a single API call to eliminate N+1 problem."""
    config = config or DEFAULT_CONFIG
    
    if not user_ids:
        return []
    
    # GitLab API supports batch user fetching using repeating query parameters
    url = f"{config['gitlab_base_url']}/api/v4/users"
    params = [('id[]', str(user_id)) for user_id in user_ids]
    
    try:
        logger.info(f"Batch fetching {len(user_ids)} users")
        response = _make_request(url, params=params, config=config)
        logger.info(f"Successfully fetched {len(response)} users")
        return response
    except Exception as e:
        logger.error(f"Failed to batch fetch users: {e}")
        # Fallback to individual requests if batch fails
        logger.warning("Falling back to individual user requests")
        users = []
        for user_id in user_ids:
            user = _get_user_info(user_id, config)
            if user:
                users.append(user)
        return users


def _get_user_info(user_id: int, config: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Get user information (fallback method)."""
    config = config or DEFAULT_CONFIG
    url = f"{config['gitlab_base_url']}/api/v4/users/{user_id}"
    
    try:
        return _make_request(url, config=config)
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return None


# Create connector object for Fivetran SDK
from fivetran_connector_sdk import Connector
connector = Connector(update, schema)