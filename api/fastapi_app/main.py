"""
MergeMind FastAPI Application
Main entry point for the MergeMind API service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from contextlib import asynccontextmanager

from routers import health
from middleware.logging import StructuredLoggingMiddleware, MetricsMiddleware
from services.metrics import metrics_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    logger.info("Starting MergeMind API")
    yield
    logger.info("Shutting down MergeMind API")


# Create FastAPI app
app = FastAPI(
    title="MergeMind API",
    description="AI-powered GitLab merge request analysis and reviewer suggestions",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add observability middleware
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(MetricsMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])

# Import and include other routers
from routers import mrs, mr, metrics, ai_insights
app.include_router(mrs.router, prefix="/api/v1", tags=["merge-requests"])
app.include_router(mr.router, prefix="/api/v1", tags=["merge-request"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(ai_insights.router, prefix="/api/v1", tags=["ai-insights"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "MergeMind API", "version": "0.1.0"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("API_PORT", 8080)))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
