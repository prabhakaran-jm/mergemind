"""
Structured logging middleware for MergeMind API.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with structured logging."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request completion
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "client_ip": request.client.host if request.client else None,
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request error
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "client_ip": request.client.host if request.client else None,
                }
            )
            
            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for basic metrics collection."""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.total_duration = 0.0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with metrics collection."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Update metrics
            self.request_count += 1
            self.total_duration += duration
            
            if response.status_code >= 400:
                self.error_count += 1
            
            # Log metrics periodically
            if self.request_count % 100 == 0:
                avg_duration = self.total_duration / self.request_count
                error_rate = self.error_count / self.request_count
                
                logger.info(
                    "Metrics summary",
                    extra={
                        "request_count": self.request_count,
                        "error_count": self.error_count,
                        "error_rate": round(error_rate, 4),
                        "avg_duration_ms": round(avg_duration * 1000, 2),
                        "total_duration_ms": round(self.total_duration * 1000, 2),
                    }
                )
            
            return response
            
        except Exception as e:
            # Update error metrics
            self.error_count += 1
            self.request_count += 1
            
            raise


def get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", "unknown")
