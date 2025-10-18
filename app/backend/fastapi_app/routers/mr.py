"""
Individual merge request router.
"""

from fastapi import APIRouter, HTTPException, Path, Depends
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
from collections import defaultdict
import time

from services.bigquery_client import bigquery_client
from services.risk_service import risk_service
from services.reviewer_service import reviewer_service
from services.summary_service import summary_service
from services.test_suggestion_service import test_suggestion_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple in-process rate limiting
rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 10


def check_rate_limit(client_ip: str = "default") -> bool:
    """Check if client is within rate limit."""
    now = time.time()
    
    # Clean old entries
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if now - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Add current request
    rate_limit_store[client_ip].append(now)
    return True


@router.get("/mr/{mr_id}/context")
async def get_mr_context(
    mr_id: int = Path(..., description="Merge request ID")
) -> Dict[str, Any]:
    """
    Get comprehensive context for a merge request.
    
    Returns:
        Dictionary with MR context including risk, pipeline status, etc.
    """
    try:
        # Check rate limit
        if not check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Get MR context from summary service
        context = await summary_service.get_mr_context(mr_id)
        
        if not context:
            raise HTTPException(status_code=404, detail=f"Merge request {mr_id} not found")
        
        # Get risk score
        risk_result = await risk_service.calculate_risk(mr_id)
        
        # Get author info (stub for now)
        author = {
            "user_id": context["author_id"],
            "name": context.get("author_name", f"User {context['author_id']}")  # Use author_name if available, otherwise fallback
        }
        
        # Get last pipeline info
        last_pipeline = {
            "status": context.get("last_pipeline_status", "unknown"),
            "age_min": context.get("last_pipeline_age_min", 0)
        }
        
        # Get size info
        size = {
            "additions": context.get("additions", 0),
            "deletions": context.get("deletions", 0)
        }
        
        # Get risk info
        risk = {
            "score": risk_result.get("combined_score", risk_result.get("score", 0)),
            "band": risk_result.get("combined_band", risk_result.get("band", "Low")),
            "reasons": risk_result.get("reasons", []),
            "ai_enhanced": risk_result.get("ai_enhanced", False),
            "ai_insights": risk_result.get("ai_insights", []),
            "ai_recommendations": risk_result.get("ai_recommendations", [])
        }
        
        result = {
            "mr_id": mr_id,
            "project_id": context["project_id"],
            "title": context["title"],
            "author": author,
            "state": context["state"],
            "age_hours": context.get("age_hours", 0),
            "risk": risk,
            "last_pipeline": last_pipeline,
            "approvals_left": context.get("approvals_left", 0),
            "notes_recent": context.get("notes_count_24_h", 0),
            "size": size,
            "labels": context.get("labels", []),
            "web_url": context.get("web_url"),
            "source_branch": context.get("source_branch"),
            "target_branch": context.get("target_branch")
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MR context for {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MR context: {str(e)}")


@router.post("/mr/{mr_id}/summary")
async def generate_mr_summary(
    mr_id: int = Path(..., description="Merge request ID")
) -> Dict[str, Any]:
    """
    Generate AI summary for a merge request.
    
    Returns:
        Dictionary with summary, risks, and tests
    """
    try:
        # Check rate limit
        if not check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Check if summary is already cached
        cached_summary = summary_service.get_cached_summary(mr_id)
        if cached_summary:
            logger.info(f"Returning cached summary for MR {mr_id}")
            return cached_summary
        
        # Generate new summary
        summary_result = await summary_service.generate_summary(mr_id)
        
        return summary_result
        
    except Exception as e:
        logger.error(f"Failed to generate summary for MR {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.get("/mr/{mr_id}/reviewers")
async def get_mr_reviewers(
    mr_id: int = Path(..., description="Merge request ID")
) -> Dict[str, Any]:
    """
    Get suggested reviewers for a merge request.
    
    Returns:
        Dictionary with reviewer suggestions
    """
    try:
        # Check rate limit
        if not check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Get reviewer suggestions
        suggestions = await reviewer_service.suggest_reviewers(mr_id)
        
        return {
            "reviewers": suggestions
        }
        
    except Exception as e:
        logger.error(f"Failed to get reviewers for MR {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reviewers: {str(e)}")


@router.get("/mr/{mr_id}/risk")
async def get_mr_risk(
    mr_id: int = Path(..., description="Merge request ID")
) -> Dict[str, Any]:
    """
    Get risk analysis for a merge request.
    
    Returns:
        Dictionary with risk score, band, and reasons
    """
    try:
        # Check rate limit
        if not check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Get risk score
        risk_result = await risk_service.calculate_risk(mr_id)
        
        # Get risk features for debugging
        risk_features = risk_service.get_risk_features(mr_id)
        
        return {
            "mr_id": mr_id,
            "risk": risk_result,
            "features": risk_features
        }
        
    except Exception as e:
        logger.error(f"Failed to get risk for MR {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get risk: {str(e)}")


@router.get("/mr/{mr_id}/stats")
async def get_mr_stats(
    mr_id: int = Path(..., description="Merge request ID")
) -> Dict[str, Any]:
    """
    Get statistics for a merge request.
    
    Returns:
        Dictionary with MR statistics
    """
    try:
        # Check rate limit
        if not check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        sql = """
        SELECT 
          mr_id,
          project_id,
          title,
          author_id,
          created_at,
          state,
          additions,
          deletions,
          last_pipeline_status,
          last_pipeline_age_min,
          notes_count_24_h,
          approvals_left
        FROM `{bigquery_client.project_id}.{bigquery_client.dataset_modeled}.mr_activity_view`
        WHERE mr_id = @mr_id
        LIMIT 1
        """
        
        results = bigquery_client.query(sql, mr_id=mr_id)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Merge request {mr_id} not found")
        
        mr_data = results[0]
        
        # Get risk score
        risk_result = await risk_service.calculate_risk(mr_id)
        
        # Get reviewer suggestions
        suggestions = await reviewer_service.suggest_reviewers(mr_id)
        
        # Get summary stats
        summary_stats = summary_service.get_summary_stats()
        
        return {
            "mr_id": mr_id,
            "basic_info": mr_data,
            "risk": risk_result,
            "reviewers": suggestions,
            "summary_cache_stats": summary_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats for MR {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/{mr_id}/test-suggestions")
async def get_test_suggestions(
    mr_id: int = Path(..., description="Merge request ID")
) -> Dict[str, Any]:
    """
    Get AI-powered test suggestions for a merge request.
    
    Returns:
        Dictionary with test suggestions including unit tests, integration tests,
        edge cases, and performance tests
    """
    try:
        # Rate limiting
        if not _check_rate_limit(f"test_suggestions_{mr_id}"):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Get test suggestions
        suggestions = await test_suggestion_service.suggest_tests(mr_id)
        
        if suggestions.get("fallback"):
            logger.warning(f"Test suggestions fallback for MR {mr_id}: {suggestions.get('error')}")
        
        return {
            "mr_id": mr_id,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get test suggestions for MR {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get test suggestions: {str(e)}")
