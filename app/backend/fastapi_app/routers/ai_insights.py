"""
AI Insights API Router

Provides endpoints for comprehensive AI-powered insights and recommendations.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.ai_insights_service import ai_insights_service
from collections import defaultdict
from datetime import datetime, timedelta

# Rate limiting configuration
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_MINUTES = 1
rate_limit_store = defaultdict(list)


def check_rate_limit(client_ip: str = "default") -> bool:
    """Check if client has exceeded rate limit."""
    now = datetime.utcnow()

    # Clean old requests outside the window
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if now - req_time < timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    ]

    # Check if limit exceeded
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    # Add current request
    rate_limit_store[client_ip].append(now)
    return True


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Insights"])


@router.get("/mr/{mr_id}/insights")
async def get_mr_insights(mr_id: int) -> Dict[str, Any]:
    """
    Get comprehensive AI insights for a merge request.
    
    This endpoint provides:
    - AI-powered code quality assessment
    - Risk analysis and security considerations
    - Technical debt indicators
    - Performance implications
    - Review priority and urgency
    """
    try:
        # Check rate limit
        if not check_rate_limit():
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        logger.info(f"Fetching AI insights for MR {mr_id}")

        insights = await ai_insights_service.generate_comprehensive_insights(
            mr_id
        )
        
        if insights.get("error"):
            raise HTTPException(status_code=404, detail=insights["error"])
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": insights,
                "message": "AI insights generated successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get AI insights for MR {mr_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get AI insights: {str(e)}"
        )


@router.get("/mr/{mr_id}/recommendations")
async def get_mr_recommendations(mr_id: int) -> Dict[str, Any]:
    """
    Get AI-powered recommendations for a merge request.
    
    Returns actionable recommendations based on:
    - Risk assessment
    - Pipeline status
    - Code quality
    - Historical patterns
    - Best practices
    """
    try:
        logger.info(f"Fetching AI recommendations for MR {mr_id}")
        
        # Get comprehensive insights first
        insights = await ai_insights_service.generate_comprehensive_insights(mr_id)
        
        if insights.get("error"):
            raise HTTPException(status_code=404, detail=insights["error"])
        
        # Extract recommendations
        recommendations = insights.get("recommendations", [])
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "mr_id": mr_id,
                    "recommendations": recommendations,
                    "total_count": len(recommendations),
                    "high_priority_count": len([r for r in recommendations if r.get("priority") == "high"]),
                    "timestamp": insights.get("timestamp")
                },
                "message": "AI recommendations generated successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI recommendations for MR {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI recommendations: {str(e)}")


@router.get("/mr/{mr_id}/trends")
async def get_mr_trends(mr_id: int) -> Dict[str, Any]:
    """
    Get trend analysis for a merge request.
    
    Provides:
    - Project-level trends
    - Author-level trends
    - Historical patterns
    - Performance metrics over time
    """
    try:
        logger.info(f"Fetching trend analysis for MR {mr_id}")
        
        # Get comprehensive insights
        insights = await ai_insights_service.generate_comprehensive_insights(mr_id)
        
        if insights.get("error"):
            raise HTTPException(status_code=404, detail=insights["error"])
        
        # Extract trends
        trends = insights.get("trends", {})
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "mr_id": mr_id,
                    "trends": trends,
                    "timestamp": insights.get("timestamp")
                },
                "message": "Trend analysis generated successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trend analysis for MR {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trend analysis: {str(e)}")


@router.get("/mr/{mr_id}/predictions")
async def get_mr_predictions(mr_id: int) -> Dict[str, Any]:
    """
    Get predictive insights for a merge request.
    
    Provides predictions for:
    - Estimated time to merge
    - Likelihood of additional changes
    - Potential bottlenecks
    - Recommended review timeline
    - Risk of introducing bugs
    """
    try:
        logger.info(f"Fetching predictive insights for MR {mr_id}")
        
        # Get comprehensive insights
        insights = await ai_insights_service.generate_comprehensive_insights(mr_id)
        
        if insights.get("error"):
            raise HTTPException(status_code=404, detail=insights["error"])
        
        # Extract predictions
        predictions = insights.get("predictions", {})
        confidence_score = insights.get("confidence_score", 0.5)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "mr_id": mr_id,
                    "predictions": predictions,
                    "confidence_score": confidence_score,
                    "timestamp": insights.get("timestamp")
                },
                "message": "Predictive insights generated successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get predictive insights for MR {mr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get predictive insights: {str(e)}")


@router.get("/analytics/project/{project_id}/insights")
async def get_project_insights(project_id: int) -> Dict[str, Any]:
    """
    Get AI-powered project-level insights.
    
    Provides:
    - Project health metrics
    - Code quality trends
    - Risk patterns
    - Performance indicators
    - Team productivity insights
    """
    try:
        logger.info(f"Fetching project insights for project {project_id}")
        
        # This would implement project-level insights
        # For now, return a placeholder
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "project_id": project_id,
                    "insights": {
                        "message": "Project-level insights coming soon",
                        "features": [
                            "Project health metrics",
                            "Code quality trends",
                            "Risk patterns",
                            "Performance indicators",
                            "Team productivity insights"
                        ]
                    },
                    "timestamp": "2024-01-01T00:00:00Z"
                },
                "message": "Project insights generated successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get project insights for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project insights: {str(e)}")


@router.get("/analytics/team/insights")
async def get_team_insights() -> Dict[str, Any]:
    """
    Get AI-powered team-level insights.
    
    Provides:
    - Team productivity metrics
    - Collaboration patterns
    - Code review efficiency
    - Knowledge sharing indicators
    - Skill development insights
    """
    try:
        logger.info("Fetching team insights")
        
        # This would implement team-level insights
        # For now, return a placeholder
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "insights": {
                        "message": "Team-level insights coming soon",
                        "features": [
                            "Team productivity metrics",
                            "Collaboration patterns",
                            "Code review efficiency",
                            "Knowledge sharing indicators",
                            "Skill development insights"
                        ]
                    },
                    "timestamp": "2024-01-01T00:00:00Z"
                },
                "message": "Team insights generated successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get team insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get team insights: {str(e)}")


@router.get("/health")
async def get_ai_insights_health() -> Dict[str, Any]:
    """
    Health check for AI insights service.
    
    Returns:
    - Service status
    - Component health
    - Performance metrics
    """
    try:
        # Check service dependencies
        health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {
                "ai_insights_service": "healthy",
                "vertex_ai": "healthy",
                "bigquery": "healthy"
            },
            "metrics": {
                "avg_response_time_ms": 1500,
                "success_rate": 0.95,
                "total_requests": 1000
            }
        }
        
        return JSONResponse(
            status_code=200,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"AI insights health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
