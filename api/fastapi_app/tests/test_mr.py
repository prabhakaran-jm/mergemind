"""
Tests for individual merge request endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_mr_context():
    """Mock MR context data."""
    return {
        "mr_id": 1,
        "project_id": 4,
        "title": "Test MR",
        "author": {
            "user_id": 1,
            "name": "testuser"
        },
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
def mock_summary():
    """Mock AI summary data."""
    return {
        "summary": [
            "This MR adds a new feature for user authentication",
            "The changes are minimal and well-structured"
        ],
        "risks": [
            "Potential security implications in auth flow",
            "Missing error handling in edge cases"
        ],
        "tests": [
            "Add unit tests for new auth methods",
            "Test error scenarios and edge cases"
        ]
    }


@pytest.fixture
def mock_reviewers():
    """Mock reviewer suggestions."""
    return {
        "reviewers": [
            {
                "user_id": 2,
                "name": "reviewer1",
                "score": 0.85,
                "reason": "Has approved 5 of your MRs, 12 total interactions"
            },
            {
                "user_id": 3,
                "name": "reviewer2",
                "score": 0.72,
                "reason": "Has reviewed 8 of your MRs, 15 total interactions"
            }
        ]
    }


@pytest.fixture
def mock_risk_features():
    """Mock risk features data."""
    return {
        "mr_id": 1,
        "project_id": 4,
        "age_hours": 24.5,
        "notes_count_24h": 2,
        "last_pipeline_status_is_fail": False,
        "approvals_left": 1,
        "change_size_bucket": "S",
        "work_in_progress": False,
        "labels_sensitive": False
    }


def test_mr_context_endpoint(client, mock_mr_context):
    """Test MR context endpoint."""
    with patch('routers.mr.get_mr_context') as mock_get_context:
        mock_get_context.return_value = mock_mr_context
        
        response = client.get("/api/v1/mr/1/context")
        assert response.status_code == 200
        data = response.json()
        
        assert data["mr_id"] == 1
        assert data["title"] == "Test MR"
        assert data["author"]["name"] == "testuser"
        assert data["risk"]["band"] == "Low"


def test_mr_context_not_found(client):
    """Test MR context endpoint with non-existent MR."""
    with patch('routers.mr.get_mr_context') as mock_get_context:
        mock_get_context.return_value = None
        
        response = client.get("/api/v1/mr/999/context")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


def test_mr_context_error(client):
    """Test MR context endpoint with error."""
    with patch('routers.mr.get_mr_context') as mock_get_context:
        mock_get_context.side_effect = Exception("Database error")
        
        response = client.get("/api/v1/mr/1/context")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


def test_mr_summary_endpoint(client, mock_summary):
    """Test MR summary endpoint."""
    with patch('routers.mr.generate_summary') as mock_generate:
        mock_generate.return_value = mock_summary
        
        response = client.post("/api/v1/mr/1/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "risks" in data
        assert "tests" in data
        assert len(data["summary"]) == 2
        assert len(data["risks"]) == 2
        assert len(data["tests"]) == 2


def test_mr_summary_not_found(client):
    """Test MR summary endpoint with non-existent MR."""
    with patch('routers.mr.generate_summary') as mock_generate:
        mock_generate.return_value = None
        
        response = client.post("/api/v1/mr/999/summary")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


def test_mr_summary_error(client):
    """Test MR summary endpoint with error."""
    with patch('routers.mr.generate_summary') as mock_generate:
        mock_generate.side_effect = Exception("AI service error")
        
        response = client.post("/api/v1/mr/1/summary")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


def test_mr_reviewers_endpoint(client, mock_reviewers):
    """Test MR reviewers endpoint."""
    with patch('routers.mr.get_reviewer_suggestions') as mock_get_reviewers:
        mock_get_reviewers.return_value = mock_reviewers["reviewers"]
        
        response = client.get("/api/v1/mr/1/reviewers")
        assert response.status_code == 200
        data = response.json()
        
        assert "reviewers" in data
        assert len(data["reviewers"]) == 2
        assert data["reviewers"][0]["name"] == "reviewer1"
        assert data["reviewers"][1]["name"] == "reviewer2"


def test_mr_reviewers_empty(client):
    """Test MR reviewers endpoint with no suggestions."""
    with patch('routers.mr.get_reviewer_suggestions') as mock_get_reviewers:
        mock_get_reviewers.return_value = []
        
        response = client.get("/api/v1/mr/1/reviewers")
        assert response.status_code == 200
        data = response.json()
        
        assert "reviewers" in data
        assert len(data["reviewers"]) == 0


def test_mr_reviewers_error(client):
    """Test MR reviewers endpoint with error."""
    with patch('routers.mr.get_reviewer_suggestions') as mock_get_reviewers:
        mock_get_reviewers.side_effect = Exception("Reviewer service error")
        
        response = client.get("/api/v1/mr/1/reviewers")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


def test_mr_risk_endpoint(client, mock_risk_features):
    """Test MR risk endpoint."""
    with patch('routers.mr.calculate_risk') as mock_calculate:
        mock_calculate.return_value = {
            "score": 25,
            "band": "Low",
            "reasons": ["Small change"]
        }
        
        response = client.get("/api/v1/mr/1/risk")
        assert response.status_code == 200
        data = response.json()
        
        assert "score" in data
        assert "band" in data
        assert "reasons" in data
        assert data["score"] == 25
        assert data["band"] == "Low"


def test_mr_risk_not_found(client):
    """Test MR risk endpoint with non-existent MR."""
    with patch('routers.mr.calculate_risk') as mock_calculate:
        mock_calculate.return_value = None
        
        response = client.get("/api/v1/mr/999/risk")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


def test_mr_risk_error(client):
    """Test MR risk endpoint with error."""
    with patch('routers.mr.calculate_risk') as mock_calculate:
        mock_calculate.side_effect = Exception("Risk calculation error")
        
        response = client.get("/api/v1/mr/1/risk")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


def test_mr_stats_endpoint(client, mock_mr_context):
    """Test MR stats endpoint."""
    with patch('routers.mr.get_mr_stats') as mock_get_stats:
        mock_get_stats.return_value = {
            "mr_id": 1,
            "total_notes": 5,
            "total_approvals": 1,
            "total_reviews": 3,
            "cycle_time_hours": 48.5,
            "last_activity": "2024-01-01T12:00:00Z"
        }
        
        response = client.get("/api/v1/mr/1/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "mr_id" in data
        assert "total_notes" in data
        assert "total_approvals" in data
        assert "cycle_time_hours" in data


def test_mr_stats_not_found(client):
    """Test MR stats endpoint with non-existent MR."""
    with patch('routers.mr.get_mr_stats') as mock_get_stats:
        mock_get_stats.return_value = None
        
        response = client.get("/api/v1/mr/999/stats")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


def test_mr_stats_error(client):
    """Test MR stats endpoint with error."""
    with patch('routers.mr.get_mr_stats') as mock_get_stats:
        mock_get_stats.side_effect = Exception("Stats calculation error")
        
        response = client.get("/api/v1/mr/1/stats")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
