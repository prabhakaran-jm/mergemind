"""
Merge requests list router.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from services.bigquery_client import bigquery_client
from services.risk_service import risk_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/mrs")
async def list_merge_requests(
    state: Optional[str] = Query(None, description="Filter by MR state (open, merged, closed)"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    cursor: Optional[str] = Query(None, description="Pagination cursor")
) -> Dict[str, Any]:
    """
    List merge requests with risk badges.
    
    Returns:
        Dictionary with items and pagination info
    """
    try:
        # Build query with filters
        where_conditions = []
        params = {"limit": limit}
        
        if state:
            where_conditions.append("state = @state")
            params["state"] = state
        
        if project_id:
            where_conditions.append("project_id = @project_id")
            params["project_id"] = project_id
        
        # Add cursor-based pagination
        if cursor and cursor != "None":
            where_conditions.append("id > @cursor")
            params["cursor"] = int(cursor)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"
        
        
        sql = f"""
        SELECT 
          mr_id,
          project_id,
          title,
          author_id,
          assignee_id,
          created_at,
          updated_at,
          state,
          TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours,
          last_pipeline_status,
          notes_count_24_h,
          approvals_left,
          additions,
          deletions,
          source_branch,
          target_branch,
          web_url,
          merged_at,
          closed_at
        FROM `{bigquery_client.project_id}.{bigquery_client.dataset_modeled}.mr_activity_view`
        WHERE {where_clause}
        ORDER BY mr_id DESC
        LIMIT @limit
        """
        
        results = bigquery_client.query(sql, **params)
        
        # Calculate risk scores for each MR
        items = []
        for row in results:
            # Get risk score (with fallback for missing data)
            try:
                risk_result = await risk_service.calculate_risk(row["mr_id"])
            except Exception as e:
                logger.warning(f"Risk calculation failed for MR {row['mr_id']}: {e}")
                risk_result = {"band": "Unknown", "score": 0}
            
            item = {
                "mr_id": row["mr_id"],
                "project_id": row["project_id"],
                "title": row["title"],
                "author": f"User {row['author_id']}",  # TODO: Get actual user name
                "assignee": f"User {row['assignee_id']}" if row["assignee_id"] else None,
                "age_hours": row["age_hours"],
                "risk_band": risk_result.get("combined_band", risk_result.get("band", "Unknown")),
                "risk_score": risk_result.get("combined_score", risk_result.get("score", 0)),
                "state": row["state"],
                "pipeline_status": row["last_pipeline_status"],
                "notes_count_24_h": row["notes_count_24_h"],
                "approvals_left": row["approvals_left"],
                "additions": row["additions"],
                "deletions": row["deletions"],
                "source_branch": row["source_branch"],
                "target_branch": row["target_branch"],
                "web_url": row["web_url"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "merged_at": row["merged_at"].isoformat() if row["merged_at"] else None,
                "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None
            }
            items.append(item)
        
        # Determine next cursor
        next_cursor = None
        if len(items) == limit and items:
            next_cursor = str(items[-1]["mr_id"])
        
        return {
            "items": items,
            "next_cursor": next_cursor,
            "total": len(items)
        }
        
    except Exception as e:
        logger.error(f"Failed to list merge requests: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list merge requests: {str(e)}")


@router.get("/blockers/top")
async def get_top_blockers(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of blockers")
) -> List[Dict[str, Any]]:
    """
    Get top blocking merge requests.
    
    Returns:
        List of blocking MRs
    """
    try:
        sql = """
        SELECT 
          mr_id,
          project_id,
          title,
          author_id,
          assignee_id,
          created_at,
          updated_at,
          state,
          TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours,
          last_pipeline_status,
          notes_count_24_h,
          approvals_left,
          additions,
          deletions,
          source_branch,
          target_branch,
          web_url,
          merged_at,
          closed_at
        FROM `{bigquery_client.project_id}.{bigquery_client.dataset_modeled}.mr_activity_view`
        WHERE state = 'opened'
        ORDER BY age_hours DESC
        LIMIT @limit
        """
        
        results = bigquery_client.query(sql, limit=limit)
        
        blockers = []
        for row in results:
            # Get risk score (with fallback for missing data)
            try:
                risk_result = await risk_service.calculate_risk(row["mr_id"])
            except Exception as e:
                logger.warning(f"Risk calculation failed for MR {row['mr_id']}: {e}")
                risk_result = {"band": "Unknown", "score": 0}
            
            blocker = {
                "mr_id": row["mr_id"],
                "project_id": row["project_id"],
                "title": row["title"],
                "author": f"User {row['author_id']}",  # TODO: Get actual user name
                "assignee": f"User {row['assignee_id']}" if row["assignee_id"] else None,
                "age_hours": row["age_hours"],
                "risk_band": risk_result.get("combined_band", risk_result.get("band", "Unknown")),
                "risk_score": risk_result.get("combined_score", risk_result.get("score", 0)),
                "blocking_reason": f"Open for {row['age_hours']} hours",
                "state": row["state"],
                "pipeline_status": row["last_pipeline_status"],
                "notes_count_24_h": row["notes_count_24_h"],
                "approvals_left": row["approvals_left"],
                "additions": row["additions"],
                "deletions": row["deletions"],
                "source_branch": row["source_branch"],
                "target_branch": row["target_branch"],
                "web_url": row["web_url"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            }
            blockers.append(blocker)
        
        return blockers
        
    except Exception as e:
        logger.error(f"Failed to get top blockers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top blockers: {str(e)}")
