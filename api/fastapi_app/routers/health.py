"""
Health check router for MergeMind API.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import os

router = APIRouter()


@router.get("/healthz")
async def health_check():
    """
    Health check endpoint.
    Returns basic service status and environment info.
    """
    try:
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Verifies that the service is ready to accept requests.
    """
    # TODO: Add checks for external dependencies (BigQuery, GitLab, etc.)
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }
