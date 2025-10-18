"""
Pytest configuration and fixtures for MergeMind API tests.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set test environment variables
os.environ.update({
    "GCP_PROJECT_ID": "test-project",
    "BQ_DATASET_RAW": "test_raw",
    "BQ_DATASET_MODELED": "test_modeled",
    "VERTEX_LOCATION": "us-central1",
    "GITLAB_BASE_URL": "https://test.gitlab.com",
    "GITLAB_TOKEN": "test-token",
    "API_BASE_URL": "http://localhost:8080",
    "LOG_LEVEL": "DEBUG"
})


@pytest.fixture(scope="session")
def test_client():
    """Create test client for the entire test session."""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client."""
    with patch('services.bigquery_client.bigquery_client') as mock:
        mock.test_connection.return_value = True
        mock.query.return_value = []
        mock.table_exists.return_value = True
        yield mock


@pytest.fixture
def mock_gitlab_client():
    """Mock GitLab client."""
    with patch('services.gitlab_client.gitlab_client') as mock:
        mock.test_connection.return_value = True
        yield mock


@pytest.fixture
def mock_vertex_client():
    """Mock Vertex AI client."""
    with patch('services.vertex_client.vertex_client') as mock:
        mock.test_connection.return_value = True
        mock.generate_text.return_value = "Generated text"
        mock.summarize_diff.return_value = {
            "summary": ["Test summary"],
            "risks": ["Test risk"],
            "tests": ["Test test"]
        }
        yield mock


@pytest.fixture
def mock_reviewer_service():
    """Mock reviewer service."""
    with patch('services.reviewer_service.reviewer_service') as mock:
        mock.suggest_reviewers.return_value = [
            {
                "user_id": 2,
                "name": "test_reviewer",
                "score": 0.8,
                "reason": "Good match"
            }
        ]
        yield mock


@pytest.fixture
def mock_risk_service():
    """Mock risk service."""
    with patch('services.risk_service.risk_service') as mock:
        mock.calculate_risk.return_value = {
            "score": 25,
            "band": "Low",
            "reasons": ["Small change"]
        }
        yield mock


@pytest.fixture
def mock_summary_service():
    """Mock summary service."""
    with patch('services.summary_service.summary_service') as mock:
        mock.generate_summary.return_value = {
            "summary": ["Test summary"],
            "risks": ["Test risk"],
            "tests": ["Test test"]
        }
        yield mock


@pytest.fixture
def mock_user_service():
    """Mock user service."""
    with patch('services.user_service.user_service') as mock:
        mock.get_user_name.return_value = "test_user"
        mock.get_user_info.return_value = {
            "user_id": 1,
            "username": "testuser",
            "name": "Test User",
            "email": "test@example.com"
        }
        yield mock


@pytest.fixture
def mock_metrics_service():
    """Mock metrics service."""
    with patch('services.metrics.metrics_service') as mock:
        mock.get_summary.return_value = {
            "uptime_seconds": 3600,
            "request_count": 100,
            "error_count": 0,
            "error_rate": 0.0,
            "request_rate_per_second": 0.03,
            "avg_duration_ms": 50.0,
            "p50_duration_ms": 45.0,
            "p95_duration_ms": 100.0,
            "p99_duration_ms": 200.0,
            "top_endpoints": [],
            "top_errors": []
        }
        mock.check_slo_violations.return_value = {
            "violations": [],
            "summary": {},
            "status": "healthy"
        }
        yield mock


@pytest.fixture
def mock_all_services(mock_bigquery_client, mock_gitlab_client, mock_vertex_client,
                     mock_reviewer_service, mock_risk_service, mock_summary_service,
                     mock_user_service, mock_metrics_service):
    """Mock all external services."""
    return {
        "bigquery": mock_bigquery_client,
        "gitlab": mock_gitlab_client,
        "vertex": mock_vertex_client,
        "reviewer": mock_reviewer_service,
        "risk": mock_risk_service,
        "summary": mock_summary_service,
        "user": mock_user_service,
        "metrics": mock_metrics_service
    }


@pytest.fixture
def sample_mr_data():
    """Sample MR data for testing."""
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
def sample_mr_list():
    """Sample MR list data for testing."""
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


@pytest.fixture
def sample_summary():
    """Sample AI summary data for testing."""
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
def sample_reviewers():
    """Sample reviewer suggestions for testing."""
    return [
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


@pytest.fixture
def sample_risk_features():
    """Sample risk features for testing."""
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


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure test environment variables are set
    test_env = {
        "GCP_PROJECT_ID": "test-project",
        "BQ_DATASET_RAW": "test_raw",
        "BQ_DATASET_MODELED": "test_modeled",
        "VERTEX_LOCATION": "us-central1",
        "GITLAB_BASE_URL": "https://test.gitlab.com",
        "GITLAB_TOKEN": "test-token",
        "API_BASE_URL": "http://localhost:8080",
        "LOG_LEVEL": "DEBUG"
    }
    
    with patch.dict(os.environ, test_env):
        yield


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add unit marker to all tests in test_services.py
        if "test_services" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to all tests in test_integration.py
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to integration tests
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
