"""
Health check router for MergeMind API.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import os
import logging

from services.bigquery_client import bigquery_client
from services.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/healthz")
async def health_check():
    """
    Health check endpoint.
    Returns basic service status and environment info.
    """
    try:
        settings = get_settings()
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "environment": settings.environment,
            "project_id": settings.gcp_project_id
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Verifies that the service is ready to accept requests.
    """
    try:
        settings = get_settings()
        checks = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ready"
        }
        
        # Test BigQuery connection
        try:
            bq_healthy = bigquery_client.test_connection()
            checks["bigquery"] = "healthy" if bq_healthy else "unhealthy"
        except Exception as e:
            logger.warning(f"BigQuery health check failed: {e}")
            checks["bigquery"] = "unhealthy"
        
        # Check if all critical services are healthy
        if checks.get("bigquery") != "healthy":
            raise HTTPException(status_code=503, detail="Service not ready")
        
        return checks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")
