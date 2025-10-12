"""
Tests for merge request endpoints.
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
def mock_mr_data():
    """Mock MR data."""
    return {
        "mr_id": 1,
        "project_id": 4,
        "title": "Test MR",
        "author_id": 1,
        "state": "opened",
        "age_hours": 24.5,
        "risk": {
            "score": 25,
            "band": "Low",
            "reasons": ["Small change"]
        },
        "last_pipeline": {
            "status": "success",
            "age_min": 30
        },
        "approvals_left": 1,
        "notes_recent": 2,
        "size": {
            "additions": 50,
            "deletions": 10
        },
        "web_url": "https://gitlab.com/test/project/-/merge_requests/1"
    }


@pytest.fixture
def mock_mr_list():
    """Mock MR list data."""
    return [
        {
            "mr_id": 1,
            "project_id": 4,
            "title": "Test MR 1",
            "author": "testuser1",
            "age_hours": 24.5,
            "risk_band": "Low",
            "risk_score": 25,
            "pipeline_status": "success",
            "approvals_left": 1,
            "notes_count_24h": 2,
            "additions": 50,
            "deletions": 10
        },
        {
            "mr_id": 2,
            "project_id": 4,
            "title": "Test MR 2",
            "author": "testuser2",
            "age_hours": 48.0,
            "risk_band": "Medium",
            "risk_score": 45,
            "pipeline_status": "failed",
            "approvals_left": 2,
            "notes_count_24h": 5,
            "additions": 200,
            "deletions": 50
        }
    ]


def test_mrs_list_endpoint(client, mock_mr_list):
    """Test MR list endpoint."""
    with patch('routers.mrs.get_mrs_from_bigquery') as mock_get_mrs:
        mock_get_mrs.return_value = mock_mr_list
        
        response = client.get("/api/v1/mrs")
        assert response.status_code == 200
        data = response.json()
        
        assert "mrs" in data
        assert len(data["mrs"]) == 2
        assert data["mrs"][0]["mr_id"] == 1
        assert data["mrs"][1]["mr_id"] == 2


def test_mrs_list_with_filters(client, mock_mr_list):
    """Test MR list endpoint with filters."""
    with patch('routers.mrs.get_mrs_from_bigquery') as mock_get_mrs:
        mock_get_mrs.return_value = mock_mr_list
        
        response = client.get("/api/v1/mrs?risk_band=Low&limit=1")
        assert response.status_code == 200
        data = response.json()
        
        assert "mrs" in data
        assert len(data["mrs"]) == 1
        assert data["mrs"][0]["risk_band"] == "Low"


def test_mrs_list_empty(client):
    """Test MR list endpoint with no data."""
    with patch('routers.mrs.get_mrs_from_bigquery') as mock_get_mrs:
        mock_get_mrs.return_value = []
        
        response = client.get("/api/v1/mrs")
        assert response.status_code == 200
        data = response.json()
        
        assert "mrs" in data
        assert len(data["mrs"]) == 0


def test_mrs_list_error(client):
    """Test MR list endpoint with error."""
    with patch('routers.mrs.get_mrs_from_bigquery') as mock_get_mrs:
        mock_get_mrs.side_effect = Exception("Database error")
        
        response = client.get("/api/v1/mrs")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


def test_blockers_top_endpoint(client, mock_mr_list):
    """Test top blockers endpoint."""
    with patch('routers.mrs.get_blocking_mrs_from_bigquery') as mock_get_blockers:
        mock_get_blockers.return_value = mock_mr_list
        
        response = client.get("/api/v1/blockers/top")
        assert response.status_code == 200
        data = response.json()
        
        assert "blockers" in data
        assert len(data["blockers"]) == 2


def test_blockers_top_with_limit(client, mock_mr_list):
    """Test top blockers endpoint with limit."""
    with patch('routers.mrs.get_blocking_mrs_from_bigquery') as mock_get_blockers:
        mock_get_blockers.return_value = mock_mr_list[:1]
        
        response = client.get("/api/v1/blockers/top?limit=1")
        assert response.status_code == 200
        data = response.json()
        
        assert "blockers" in data
        assert len(data["blockers"]) == 1


def test_blockers_top_empty(client):
    """Test top blockers endpoint with no blockers."""
    with patch('routers.mrs.get_blocking_mrs_from_bigquery') as mock_get_blockers:
        mock_get_blockers.return_value = []
        
        response = client.get("/api/v1/blockers/top")
        assert response.status_code == 200
        data = response.json()
        
        assert "blockers" in data
        assert len(data["blockers"]) == 0


def test_blockers_top_error(client):
    """Test top blockers endpoint with error."""
    with patch('routers.mrs.get_blocking_mrs_from_bigquery') as mock_get_blockers:
        mock_get_blockers.side_effect = Exception("Database error")
        
        response = client.get("/api/v1/blockers/top")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
