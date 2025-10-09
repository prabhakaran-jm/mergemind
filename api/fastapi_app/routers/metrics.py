"""
Metrics and observability router.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import logging

from services.metrics import metrics_service
from middleware.logging import get_request_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics")
async def get_metrics(request: Request) -> Dict[str, Any]:
    """
    Get application metrics.
    
    Returns:
        Dictionary with metrics summary
    """
    try:
        request_id = get_request_id(request)
        
        # Get metrics summary
        summary = metrics_service.get_summary()
        
        logger.info(f"Metrics requested by {request_id}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/metrics/slo")
async def check_slo_violations(request: Request) -> Dict[str, Any]:
    """
    Check SLO violations.
    
    Returns:
        Dictionary with SLO violation status
    """
    try:
        request_id = get_request_id(request)
        
        # Check SLO violations
        slo_status = metrics_service.check_slo_violations()
        
        logger.info(f"SLO check requested by {request_id}, status: {slo_status['status']}")
        
        return slo_status
        
    except Exception as e:
        logger.error(f"Failed to check SLO violations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check SLO violations: {str(e)}")


@router.get("/metrics/endpoint/{endpoint}")
async def get_endpoint_metrics(endpoint: str, method: str = "GET", request: Request = None) -> Dict[str, Any]:
    """
    Get metrics for a specific endpoint.
    
    Args:
        endpoint: Endpoint path
        method: HTTP method
        
    Returns:
        Dictionary with endpoint metrics
    """
    try:
        request_id = get_request_id(request) if request else "unknown"
        
        # Get endpoint metrics
        metrics = metrics_service.get_endpoint_metrics(endpoint, method)
        
        logger.info(f"Endpoint metrics requested for {method} {endpoint} by {request_id}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get endpoint metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get endpoint metrics: {str(e)}")


@router.post("/metrics/reset")
async def reset_metrics(request: Request) -> Dict[str, str]:
    """
    Reset all metrics.
    
    Returns:
        Confirmation message
    """
    try:
        request_id = get_request_id(request)
        
        # Reset metrics
        metrics_service.reset_metrics()
        
        logger.info(f"Metrics reset by {request_id}")
        
        return {"message": "Metrics reset successfully"}
        
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")


@router.get("/health/detailed")
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """
    Detailed health check with metrics.
    
    Returns:
        Dictionary with detailed health status
    """
    try:
        request_id = get_request_id(request)
        
        # Get basic health info
        from services.bigquery_client import bigquery_client
        from services.gitlab_client import gitlab_client
        from services.vertex_client import vertex_client
        
        # Test connections
        bq_healthy = bigquery_client.test_connection()
        gitlab_healthy = gitlab_client.test_connection()
        vertex_healthy = vertex_client.test_connection()
        
        # Get metrics
        metrics_summary = metrics_service.get_summary()
        slo_status = metrics_service.check_slo_violations()
        
        # Determine overall health
        all_services_healthy = bq_healthy and gitlab_healthy and vertex_healthy
        no_slo_violations = slo_status["status"] == "healthy"
        
        overall_status = "healthy" if all_services_healthy and no_slo_violations else "degraded"
        
        health_info = {
            "status": overall_status,
            "timestamp": metrics_summary["uptime_seconds"],
            "services": {
                "bigquery": "healthy" if bq_healthy else "unhealthy",
                "gitlab": "healthy" if gitlab_healthy else "unhealthy",
                "vertex_ai": "healthy" if vertex_healthy else "unhealthy"
            },
            "metrics": metrics_summary,
            "slo_status": slo_status,
            "request_id": request_id
        }
        
        logger.info(f"Detailed health check by {request_id}, status: {overall_status}")
        
        return health_info
        
    except Exception as e:
        logger.error(f"Failed to perform detailed health check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform health check: {str(e)}")
