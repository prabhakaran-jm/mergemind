"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_services():
    """Mock external services."""
    with patch('services.bigquery_client.bigquery_client') as mock_bq, \
         patch('services.gitlab_client.gitlab_client') as mock_gitlab, \
         patch('services.vertex_client.vertex_client') as mock_vertex:
        
        # Configure mocks
        mock_bq.test_connection.return_value = True
        mock_gitlab.test_connection.return_value = True
        mock_vertex.test_connection.return_value = True
        
        yield {
            'bigquery': mock_bq,
            'gitlab': mock_gitlab,
            'vertex': mock_vertex
        }


def test_healthz_endpoint(client):
    """Test basic health check endpoint."""
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_ready_endpoint(client, mock_services):
    """Test readiness check endpoint."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data


def test_ready_endpoint_with_failed_service(client):
    """Test readiness check when service fails."""
    with patch('services.bigquery_client.bigquery_client') as mock_bq:
        mock_bq.test_connection.return_value = False
        
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert "bigquery" in data["failed_services"]


def test_detailed_health_endpoint(client, mock_services):
    """Test detailed health check endpoint."""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert "services" in data
    assert "metrics" in data
    
    # Check service status
    services = data["services"]
    assert services["bigquery"]["status"] == "healthy"
    assert services["gitlab"]["status"] == "healthy"
    assert services["vertex"]["status"] == "healthy"


def test_detailed_health_with_failed_services(client):
    """Test detailed health check with failed services."""
    with patch('services.bigquery_client.bigquery_client') as mock_bq, \
         patch('services.gitlab_client.gitlab_client') as mock_gitlab, \
         patch('services.vertex_client.vertex_client') as mock_vertex:
        
        mock_bq.test_connection.return_value = False
        mock_gitlab.test_connection.return_value = True
        mock_vertex.test_connection.return_value = False
        
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        
        services = data["services"]
        assert services["bigquery"]["status"] == "unhealthy"
        assert services["gitlab"]["status"] == "healthy"
        assert services["vertex"]["status"] == "unhealthy"


def test_metrics_endpoint(client):
    """Test metrics endpoint."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    
    assert "uptime_seconds" in data
    assert "request_count" in data
    assert "error_count" in data
    assert "error_rate" in data
    assert "request_rate_per_second" in data
    assert "avg_duration_ms" in data
    assert "p50_duration_ms" in data
    assert "p95_duration_ms" in data
    assert "p99_duration_ms" in data
    assert "top_endpoints" in data
    assert "top_errors" in data


def test_slo_metrics_endpoint(client):
    """Test SLO metrics endpoint."""
    response = client.get("/api/v1/metrics/slo")
    assert response.status_code == 200
    data = response.json()
    
    assert "violations" in data
    assert "summary" in data
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]


def test_reset_metrics_endpoint(client):
    """Test metrics reset endpoint."""
    response = client.post("/api/v1/metrics/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Metrics reset successfully"


def test_endpoint_metrics(client):
    """Test endpoint-specific metrics."""
    # Make a request to generate metrics
    client.get("/api/v1/healthz")
    
    response = client.get("/api/v1/metrics/endpoint/healthz")
    assert response.status_code == 200
    data = response.json()
    
    assert "endpoint" in data
    assert "count" in data
    assert data["count"] >= 1


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
