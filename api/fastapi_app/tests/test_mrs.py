'''
Tests for merge request list endpoints.
'''

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_mr_list_data():
    """Mock MR list data from BigQuery."""
    return [
        {
            "mr_id": 1,
            "project_id": 4,
            "title": "Test MR 1",
            "author_id": 1,
            "assignee_id": 2,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "state": "opened",
            "age_hours": 24.5,
            "last_pipeline_status": "success",
            "notes_count_24h": 2,
            "approvals_left": 1,
            "additions": 50,
            "deletions": 10,
            "source_branch": "feature/test-1",
            "target_branch": "main",
            "web_url": "http://example.com/mr/1",
            "merged_at": None,
            "closed_at": None,
        },
        {
            "mr_id": 2,
            "project_id": 4,
            "title": "Test MR 2",
            "author_id": 2,
            "assignee_id": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "state": "opened",
            "age_hours": 48.0,
            "last_pipeline_status": "failed",
            "notes_count_24h": 5,
            "approvals_left": 2,
            "additions": 200,
            "deletions": 50,
            "source_branch": "feature/test-2",
            "target_branch": "main",
            "web_url": "http://example.com/mr/2",
            "merged_at": None,
            "closed_at": None,
        }
    ]


def test_mrs_list_endpoint(client, mock_mr_list_data):
    """Test MR list endpoint."""
    with patch('routers.mrs.bigquery_client.query') as mock_query, \
         patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk:
        
        mock_query.return_value = mock_mr_list_data
        mock_risk.side_effect = [
            {"combined_band": "Low", "combined_score": 25},
            {"combined_band": "Medium", "combined_score": 45}
        ]

        response = client.get("/api/v1/mrs")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert len(data["items"]) == 2
        assert data["items"][0]["mr_id"] == 1
        assert data["items"][1]["mr_id"] == 2
        assert data["items"][0]["risk_band"] == "Low"
        assert data["items"][1]["risk_band"] == "Medium"


def test_mrs_list_with_filters(client, mock_mr_list_data):
    """Test MR list endpoint with filters."""
    with patch('routers.mrs.bigquery_client.query') as mock_query, \
         patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk:

        mock_query.return_value = [mock_mr_list_data[0]]
        mock_risk.return_value = {"combined_band": "Low", "combined_score": 25}

        response = client.get("/api/v1/mrs?state=opened&limit=1")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["mr_id"] == 1


def test_mrs_list_empty(client):
    """Test MR list endpoint with no data."""
    with patch('routers.mrs.bigquery_client.query') as mock_query:
        mock_query.return_value = []
        
        response = client.get("/api/v1/mrs")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert len(data["items"]) == 0


def test_mrs_list_error(client):
    """Test MR list endpoint with error."""
    with patch('routers.mrs.bigquery_client.query') as mock_query:
        mock_query.side_effect = Exception("Database error")
        
        response = client.get("/api/v1/mrs")
        assert response.status_code == 500
        data = response.json()
        assert "database error" in data["detail"].lower()

def test_blockers_top_endpoint(client, mock_mr_list_data):
    """Test top blockers endpoint."""
    with patch('routers.mrs.bigquery_client.query') as mock_query, \
         patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk:

        mock_query.return_value = mock_mr_list_data
        mock_risk.side_effect = [
            {"combined_band": "Low", "combined_score": 25},
            {"combined_band": "Medium", "combined_score": 45}
        ]

        response = client.get("/api/v1/blockers/top")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2

def test_blockers_top_with_limit(client, mock_mr_list_data):
    """Test top blockers endpoint with limit."""
    with patch('routers.mrs.bigquery_client.query') as mock_query, \
         patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk:

        mock_query.return_value = [mock_mr_list_data[0]]
        mock_risk.return_value = {"combined_band": "Low", "combined_score": 25}
        
        response = client.get("/api/v1/blockers/top?limit=1")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1

def test_blockers_top_empty(client):
    """Test top blockers endpoint with no blockers."""
    with patch('routers.mrs.bigquery_client.query') as mock_query:
        mock_query.return_value = []
        
        response = client.get("/api/v1/blockers/top")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 0

def test_blockers_top_error(client):
    """Test top blockers endpoint with error."""
    with patch('routers.mrs.bigquery_client.query') as mock_query:
        mock_query.side_effect = Exception("Database error")
        
        response = client.get("/api/v1/blockers/top")
        assert response.status_code == 500
        data = response.json()
        assert "database error" in data["detail"].lower()