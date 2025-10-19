"""
MergeMind FastAPI Application
Main entry point for the MergeMind API service.
"""

from fastapi import FastAPI, Request, Response
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

# Configure CORS origins from environment variables
def get_cors_origins():
    """Get CORS origins from environment variables with sensible defaults."""
    # Check for individual origin environment variables
    origins = []
    
    # Add custom domain if set
    custom_domain = os.getenv("CUSTOM_DOMAIN")
    if custom_domain:
        origins.append(f"https://{custom_domain}")
        origins.append(f"https://www.{custom_domain}")
    
    # Add Cloud Run URL if set
    cloud_run_url = os.getenv("CLOUD_RUN_URL")
    if cloud_run_url:
        origins.append(cloud_run_url)
    
    # If no origins are set via env vars, use defaults for development
    if not origins:
        origins = [
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",   # Alternative dev port
        ]
    
    return origins

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add observability middleware
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(MetricsMiddleware)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add HSTS header for HTTPS (Cloud Run serves over HTTPS)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Add other security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

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
