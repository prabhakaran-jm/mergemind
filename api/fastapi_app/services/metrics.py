"""
Metrics collection service for MergeMind API.
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Thread-safe metrics collector."""
    
    def __init__(self, window_size: int = 1000):
        """Initialize metrics collector."""
        self.window_size = window_size
        self._lock = threading.RLock()
        
        # Request metrics
        self.request_count = 0
        self.error_count = 0
        self.total_duration = 0.0
        
        # Recent requests (for percentile calculations)
        self.recent_requests = deque(maxlen=window_size)
        
        # Endpoint-specific metrics
        self.endpoint_metrics = defaultdict(lambda: {
            "count": 0,
            "errors": 0,
            "total_duration": 0.0,
            "recent_durations": deque(maxlen=100)
        })
        
        # Error tracking
        self.error_types = defaultdict(int)
        self.error_endpoints = defaultdict(int)
        
        # Start time for uptime calculation
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, method: str, status_code: int, 
                      duration: float, error: Optional[Exception] = None):
        """Record a request metric."""
        with self._lock:
            # Update global metrics
            self.request_count += 1
            self.total_duration += duration
            
            if status_code >= 400:
                self.error_count += 1
            
            # Update endpoint metrics
            endpoint_key = f"{method} {endpoint}"
            ep_metrics = self.endpoint_metrics[endpoint_key]
            ep_metrics["count"] += 1
            ep_metrics["total_duration"] += duration
            ep_metrics["recent_durations"].append(duration)
            
            if status_code >= 400:
                ep_metrics["errors"] += 1
            
            # Record error details
            if error:
                error_type = type(error).__name__
                self.error_types[error_type] += 1
                self.error_endpoints[endpoint_key] += 1
            
            # Add to recent requests
            self.recent_requests.append({
                "timestamp": time.time(),
                "endpoint": endpoint_key,
                "status_code": status_code,
                "duration": duration
            })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        with self._lock:
            uptime = time.time() - self.start_time
            
            # Calculate rates
            request_rate = self.request_count / uptime if uptime > 0 else 0
            error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
            
            # Calculate percentiles
            if self.recent_requests:
                durations = [req["duration"] for req in self.recent_requests]
                durations.sort()
                n = len(durations)
                
                p50 = durations[int(n * 0.5)] if n > 0 else 0
                p95 = durations[int(n * 0.95)] if n > 0 else 0
                p99 = durations[int(n * 0.99)] if n > 0 else 0
            else:
                p50 = p95 = p99 = 0
            
            # Get top endpoints
            top_endpoints = sorted(
                self.endpoint_metrics.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:10]
            
            # Get top errors
            top_errors = sorted(
                self.error_types.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                "uptime_seconds": uptime,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": round(error_rate, 4),
                "request_rate_per_second": round(request_rate, 2),
                "avg_duration_ms": round(
                    (self.total_duration / self.request_count * 1000) if self.request_count > 0 else 0, 2
                ),
                "p50_duration_ms": round(p50 * 1000, 2),
                "p95_duration_ms": round(p95 * 1000, 2),
                "p99_duration_ms": round(p99 * 1000, 2),
                "top_endpoints": [
                    {
                        "endpoint": endpoint,
                        "count": metrics["count"],
                        "errors": metrics["errors"],
                        "avg_duration_ms": round(
                            (metrics["total_duration"] / metrics["count"] * 1000) if metrics["count"] > 0 else 0, 2
                        )
                    }
                    for endpoint, metrics in top_endpoints
                ],
                "top_errors": [
                    {"error_type": error_type, "count": count}
                    for error_type, count in top_errors
                ]
            }
    
    def get_endpoint_metrics(self, endpoint: str, method: str) -> Dict[str, Any]:
        """Get metrics for a specific endpoint."""
        with self._lock:
            endpoint_key = f"{method} {endpoint}"
            metrics = self.endpoint_metrics[endpoint_key]
            
            if metrics["count"] == 0:
                return {"endpoint": endpoint_key, "count": 0}
            
            # Calculate percentiles for this endpoint
            if metrics["recent_durations"]:
                durations = list(metrics["recent_durations"])
                durations.sort()
                n = len(durations)
                
                p50 = durations[int(n * 0.5)] if n > 0 else 0
                p95 = durations[int(n * 0.95)] if n > 0 else 0
                p99 = durations[int(n * 0.99)] if n > 0 else 0
            else:
                p50 = p95 = p99 = 0
            
            return {
                "endpoint": endpoint_key,
                "count": metrics["count"],
                "errors": metrics["errors"],
                "error_rate": round(metrics["errors"] / metrics["count"], 4),
                "avg_duration_ms": round(metrics["total_duration"] / metrics["count"] * 1000, 2),
                "p50_duration_ms": round(p50 * 1000, 2),
                "p95_duration_ms": round(p95 * 1000, 2),
                "p99_duration_ms": round(p99 * 1000, 2),
            }
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self.request_count = 0
            self.error_count = 0
            self.total_duration = 0.0
            self.recent_requests.clear()
            self.endpoint_metrics.clear()
            self.error_types.clear()
            self.error_endpoints.clear()
            self.start_time = time.time()


# Global metrics collector
metrics_collector = MetricsCollector()


class MetricsService:
    """Service for metrics collection and reporting."""
    
    def __init__(self):
        """Initialize metrics service."""
        self.collector = metrics_collector
    
    def record_request(self, endpoint: str, method: str, status_code: int, 
                      duration: float, error: Optional[Exception] = None):
        """Record a request metric."""
        self.collector.record_request(endpoint, method, status_code, duration, error)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return self.collector.get_summary()
    
    def get_endpoint_metrics(self, endpoint: str, method: str) -> Dict[str, Any]:
        """Get metrics for a specific endpoint."""
        return self.collector.get_endpoint_metrics(endpoint, method)
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.collector.reset()
    
    def check_slo_violations(self) -> Dict[str, Any]:
        """Check for SLO violations."""
        summary = self.get_summary()
        
        violations = []
        
        # Check error rate (SLO: < 1%)
        if summary["error_rate"] > 0.01:
            violations.append({
                "metric": "error_rate",
                "value": summary["error_rate"],
                "threshold": 0.01,
                "severity": "high"
            })
        
        # Check P95 latency (SLO: < 2s)
        if summary["p95_duration_ms"] > 2000:
            violations.append({
                "metric": "p95_latency",
                "value": summary["p95_duration_ms"],
                "threshold": 2000,
                "severity": "medium"
            })
        
        # Check P99 latency (SLO: < 5s)
        if summary["p99_duration_ms"] > 5000:
            violations.append({
                "metric": "p99_latency",
                "value": summary["p99_duration_ms"],
                "threshold": 5000,
                "severity": "high"
            })
        
        return {
            "violations": violations,
            "summary": summary,
            "status": "healthy" if not violations else "degraded"
        }


# Global metrics service
metrics_service = MetricsService()
