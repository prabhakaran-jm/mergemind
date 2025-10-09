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
        if cursor:
            where_conditions.append("mr_id > @cursor")
            params["cursor"] = int(cursor)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        sql = f"""
        SELECT 
          mr_id,
          project_id,
          title,
          author_id,
          created_at,
          state,
          TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours,
          additions,
          deletions,
          last_pipeline_status,
          approvals_left,
          notes_count_24h
        FROM `mergemind.mr_activity_view`
        WHERE {where_clause}
        ORDER BY mr_id DESC
        LIMIT @limit
        """
        
        results = bigquery_client.query(sql, **params)
        
        # Calculate risk scores for each MR
        items = []
        for row in results:
            # Get risk score
            risk_result = risk_service.calculate_risk(row["mr_id"])
            
            item = {
                "mr_id": row["mr_id"],
                "project_id": row["project_id"],
                "title": row["title"],
                "author": f"User {row['author_id']}",  # TODO: Get actual user name
                "age_hours": row["age_hours"],
                "risk_band": risk_result["band"],
                "risk_score": risk_result["score"],
                "pipeline_status": row["last_pipeline_status"],
                "approvals_left": row["approvals_left"],
                "notes_count_24h": row["notes_count_24h"],
                "additions": row["additions"],
                "deletions": row["deletions"]
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
          created_at,
          TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours,
          last_pipeline_status,
          approvals_left,
          notes_count_24h,
          additions,
          deletions
        FROM `mergemind.mr_activity_view`
        WHERE state = 'opened'
          AND (last_pipeline_status = 'failed' OR approvals_left > 0)
        ORDER BY 
          CASE 
            WHEN last_pipeline_status = 'failed' THEN 1
            ELSE 2
          END,
          age_hours DESC
        LIMIT @limit
        """
        
        results = bigquery_client.query(sql, limit=limit)
        
        blockers = []
        for row in results:
            # Get risk score
            risk_result = risk_service.calculate_risk(row["mr_id"])
            
            blocker = {
                "mr_id": row["mr_id"],
                "project_id": row["project_id"],
                "title": row["title"],
                "author": f"User {row['author_id']}",  # TODO: Get actual user name
                "age_hours": row["age_hours"],
                "risk_band": risk_result["band"],
                "risk_score": risk_result["score"],
                "blocking_reason": "Pipeline failed" if row["last_pipeline_status"] == "failed" else f"{row['approvals_left']} approvals needed",
                "pipeline_status": row["last_pipeline_status"],
                "approvals_left": row["approvals_left"],
                "notes_count_24h": row["notes_count_24h"]
            }
            blockers.append(blocker)
        
        return blockers
        
    except Exception as e:
        logger.error(f"Failed to get top blockers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top blockers: {str(e)}")
