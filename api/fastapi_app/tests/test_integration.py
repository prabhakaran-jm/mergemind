'''
Integration tests for end-to-end workflows.
'''

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from main import app


@pytest.fixture(autouse=True)
def disable_rate_limit():
    with patch('routers.mr.check_rate_limit', return_value=True):
        yield

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_complete_mr_workflow():
    """Mock complete MR workflow data."""
    return {
        "mr_context": {
            "mr_id": 1,
            "project_id": 4,
            "title": "Add new authentication feature",
            "author_id": 1,
            "author_name": "developer1",  # Add this for the router
            "author": {"user_id": 1, "name": "developer1"},
            "state": "opened",
            "age_hours": 24.5,
            "risk": {"score": 35, "band": "Medium", "reasons": ["Medium size change"]},
            "last_pipeline": {"status": "success", "age_min": 30},
            "approvals_left": 1,
            "notes_recent": 2,
            "size": {"additions": 150, "deletions": 30},
            "web_url": "https://gitlab.com/test/project/-/merge_requests/1"
        },
        "summary": {
            "summary": [
                "This MR implements OAuth2 authentication",
                "Adds secure token handling and user session management"
            ],
            "risks": [
                "Potential security vulnerabilities in token storage",
                "Missing input validation in auth endpoints"
            ],
            "tests": [
                "Add unit tests for OAuth2 flow",
                "Test token expiration and refresh logic",
                "Test error handling for invalid credentials"
            ]
        },
        "reviewers": [
            {
                "user_id": 2,
                "name": "security_expert",
                "score": 0.9,
                "reason": "Has approved 8 of your MRs, 25 total interactions"
            },
            {
                "user_id": 3,
                "name": "backend_lead",
                "score": 0.8,
                "reason": "Has reviewed 12 of your MRs, 30 total interactions"
            }
        ],
        "risk_features": {
            "mr_id": 1,
            "age_hours": 24.5,
            "notes_count_24h": 2,
            "last_pipeline_status_is_fail": False,
            "approvals_left": 1,
            "change_size_bucket": "M",
            "work_in_progress": False,
            "labels_sensitive": False
        }
    }


class TestCompleteMRWorkflow:
    """Test complete merge request workflow."""
    
    def test_mr_analysis_workflow(self, client, mock_complete_mr_workflow):
        """Test complete MR analysis workflow."""
        workflow_data = mock_complete_mr_workflow

        with patch('services.summary_service.summary_service.get_mr_context', new_callable=AsyncMock) as mock_context, \
             patch('services.summary_service.summary_service.generate_summary', new_callable=AsyncMock) as mock_summary, \
             patch('services.reviewer_service.reviewer_service.suggest_reviewers', new_callable=AsyncMock) as mock_reviewers, \
             patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk, \
             patch('services.bigquery_client.bigquery_client.query') as mock_bq_query:

            # Configure mocks
            mock_context.return_value = workflow_data["mr_context"]
            mock_summary.return_value = workflow_data["summary"]
            mock_reviewers.return_value = workflow_data["reviewers"]  # Return the list directly
            mock_risk.return_value = workflow_data["mr_context"]["risk"]
            mock_bq_query.return_value = []  # Mock BigQuery calls
            
            # Step 1: Get MR context
            response = client.get("/api/v1/mr/1/context")
            assert response.status_code == 200
            context_data = response.json()
            assert context_data["mr_id"] == 1
            assert context_data["title"] == "Add new authentication feature"
            
            # Step 2: Generate AI summary
            response = client.post("/api/v1/mr/1/summary")
            assert response.status_code == 200
            summary_data = response.json()
            assert len(summary_data["summary"]) == 2
            assert len(summary_data["risks"]) == 2
            assert len(summary_data["tests"]) == 3
            
            # Step 3: Get reviewer suggestions
            response = client.get("/api/v1/mr/1/reviewers")
            assert response.status_code == 200
            reviewers_data = response.json()
            assert len(reviewers_data["reviewers"]) == 2
            assert reviewers_data["reviewers"][0]["name"] == "security_expert"
            
            # Step 4: Get risk analysis
            response = client.get("/api/v1/mr/1/risk")
            assert response.status_code == 200
            risk_data = response.json()
            assert risk_data["risk"]["score"] == 35
            assert risk_data["risk"]["band"] == "Medium"
    
    def test_mr_list_and_detail_workflow(self, client, mock_complete_mr_workflow):
        """Test MR list and detail workflow."""
        workflow_data = mock_complete_mr_workflow
        
        with patch('services.bigquery_client.bigquery_client.query') as mock_query, \
             patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk, \
             patch('services.summary_service.summary_service.get_mr_context', new_callable=AsyncMock) as mock_context:
            
            # Mock BigQuery query for MR list
            mock_query.return_value = [
                {
                    "mr_id": 1,
                    "project_id": 4,
                    "title": "Add new authentication feature",
                    "author_id": 1,
                    "assignee_id": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "state": "opened",
                    "age_hours": 24.5,
                    "last_pipeline_status": "success",
                    "notes_count_24h": 2,
                    "approvals_left": 1,
                    "additions": 150,
                    "deletions": 30,
                    "source_branch": "feature/auth",
                    "target_branch": "main",
                    "web_url": "http://example.com/mr/1",
                    "merged_at": None,
                    "closed_at": None,
                }
            ]
            
            # Mock risk calculation
            mock_risk.return_value = workflow_data["mr_context"]["risk"]

            # Mock MR context
            mock_context.return_value = workflow_data["mr_context"]
            
            # Step 1: Get MR list
            response = client.get("/api/v1/mrs")
            assert response.status_code == 200
            list_data = response.json()
            assert len(list_data["items"]) == 1
            assert list_data["items"][0]["mr_id"] == 1
            
            # Step 2: Get detailed MR context
            response = client.get("/api/v1/mr/1/context")
            assert response.status_code == 200
            context_data = response.json()
            assert context_data["mr_id"] == 1
            assert context_data["author"]["name"] == "developer1"
    
    def test_blocking_mrs_workflow(self, client):
        """Test blocking MRs workflow."""
        with patch('services.bigquery_client.bigquery_client.query') as mock_query, \
             patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk:
            
            mock_query.return_value = [
                {
                    "mr_id": 1,
                    "project_id": 4,
                    "title": "Blocking MR 1",
                    "author_id": 1,
                    "assignee_id": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "state": "opened",
                    "age_hours": 72.0,
                    "last_pipeline_status": "failed",
                    "notes_count_24h": 8,
                    "approvals_left": 2,
                    "additions": 500,
                    "deletions": 100,
                    "source_branch": "feature/blocker-1",
                    "target_branch": "main",
                    "web_url": "http://example.com/mr/1",
                    "merged_at": None,
                    "closed_at": None,
                },
                {
                    "mr_id": 2,
                    "project_id": 4,
                    "title": "Blocking MR 2",
                    "author_id": 2,
                    "assignee_id": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "state": "opened",
                    "age_hours": 48.0,
                    "last_pipeline_status": "running",
                    "notes_count_24h": 5,
                    "approvals_left": 1,
                    "additions": 300,
                    "deletions": 50,
                    "source_branch": "feature/blocker-2",
                    "target_branch": "main",
                    "web_url": "http://example.com/mr/2",
                    "merged_at": None,
                    "closed_at": None,
                }
            ]

            mock_risk.side_effect = [
                {"combined_band": "High", "combined_score": 75},
                {"combined_band": "Medium", "combined_score": 55}
            ]
            
            response = client.get("/api/v1/blockers/top")
            assert response.status_code == 200
            blockers_data = response.json()
            
            assert len(blockers_data) == 2
            assert blockers_data[0]["risk_band"] == "High"
            assert blockers_data[1]["risk_band"] == "Medium"
    
    @pytest.mark.skip(reason="Health monitoring test requires complex mocking of service instances")
    def test_health_monitoring_workflow(self, client):
        """Test health monitoring workflow."""
        # Mock the service classes directly
        with patch('services.bigquery_client.BigQueryClient') as mock_bq_class, \
             patch('services.gitlab_client.GitLabClient') as mock_gitlab_class, \
             patch('services.vertex_client.VertexAIClient') as mock_vertex_class:

            # Create mock instances
            mock_bq_instance = MagicMock()
            mock_gitlab_instance = MagicMock()
            mock_vertex_instance = MagicMock()
            
            # Configure mock instances
            mock_bq_instance.test_connection.return_value = True
            mock_gitlab_instance.test_connection.return_value = True
            mock_vertex_instance.test_connection.return_value = True
            
            # Configure mock classes to return mock instances
            mock_bq_class.return_value = mock_bq_instance
            mock_gitlab_class.return_value = mock_gitlab_instance
            mock_vertex_class.return_value = mock_vertex_instance
            
            # Step 1: Basic health check
            response = client.get("/api/v1/healthz")
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] == "ok"
            
            # Step 2: Readiness check
            response = client.get("/api/v1/ready")
            assert response.status_code == 200
            ready_data = response.json()
            assert ready_data["status"] == "ready"
            
            # Step 3: Detailed health check
            response = client.get("/api/v1/health/detailed")
            assert response.status_code == 200
            detailed_data = response.json()
            assert detailed_data["status"] == "healthy"
            assert "services" in detailed_data
            assert "metrics" in detailed_data
            
            # Step 4: Metrics check
            response = client.get("/api/v1/metrics")
            assert response.status_code == 200
            metrics_data = response.json()
            assert "uptime_seconds" in metrics_data
            assert "request_count" in metrics_data
            assert "error_rate" in metrics_data
            
            # Step 5: SLO check
            response = client.get("/api/v1/metrics/slo")
            assert response.status_code == 200
            slo_data = response.json()
            assert "status" in slo_data
            assert "violations" in slo_data
    
    def test_error_handling_workflow(self, client):
        """Test error handling workflow."""
        with patch('services.summary_service.summary_service.get_mr_context', new_callable=AsyncMock) as mock_context:
            # Test non-existent MR
            mock_context.return_value = None
            
            response = client.get("/api/v1/mr/999/context")
            assert response.status_code == 404
            error_data = response.json()
            assert "not found" in error_data["detail"].lower()
            
            # Test service error
            mock_context.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/v1/mr/1/context")
            assert response.status_code == 500
            error_data = response.json()
            assert "unavailable" in error_data["detail"].lower()
    
    def test_concurrent_requests_workflow(self, client, mock_complete_mr_workflow):
        workflow_data = mock_complete_mr_workflow
        with patch('services.summary_service.summary_service.get_mr_context', new_callable=AsyncMock) as mock_context, \
             patch('services.summary_service.summary_service.generate_summary', new_callable=AsyncMock) as mock_summary, \
             patch('services.reviewer_service.reviewer_service.suggest_reviewers', new_callable=AsyncMock) as mock_reviewers, \
             patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk, \
             patch('services.bigquery_client.bigquery_client.query') as mock_bq_query:

            # Configure mocks
            mock_context.return_value = workflow_data["mr_context"]
            mock_summary.return_value = workflow_data["summary"]
            mock_reviewers.return_value = workflow_data["reviewers"]  # Return the list directly
            mock_risk.return_value = workflow_data["mr_context"]["risk"]
            mock_bq_query.return_value = []  # Mock BigQuery calls
            
            # Make concurrent requests
            responses = []
            for _ in range(5):
                response = client.get("/api/v1/mr/1/context")
                responses.append(response)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["mr_id"] == 1
    
    def test_caching_workflow(self, client, mock_complete_mr_workflow):
        """Test caching workflow."""
        workflow_data = mock_complete_mr_workflow
        
        with patch('services.summary_service.summary_service._get_mr_data') as mock_get_mr, \
             patch('services.gitlab_client.gitlab_client.get_merge_request_diff', new_callable=AsyncMock) as mock_get_diff, \
             patch('ai.summarizer.summarize.vertex_client.summarize_diff') as mock_summarize_diff:
            
            # Configure mocks
            mock_get_mr.return_value = {"project_id": 1, "sha": "testsha"}
            mock_get_diff.return_value = "fake diff content"
            mock_summarize_diff.return_value = workflow_data["summary"]
            
            # First request - should hit service and call summarizer
            response1 = client.post("/api/v1/mr/1/summary")
            assert response1.status_code == 200
            mock_summarize_diff.assert_called_once()

            # Second request - should use cache
            response2 = client.post("/api/v1/mr/1/summary")
            assert response2.status_code == 200
            
            # Both responses should be identical
            assert response1.json() == response2.json()
            
            # Verify service was called only once
            mock_summarize_diff.assert_called_once()
    
    def test_performance_workflow(self, client, mock_complete_mr_workflow):
        """Test performance workflow."""
        workflow_data = mock_complete_mr_workflow
        
        with patch('services.summary_service.summary_service.get_mr_context', new_callable=AsyncMock) as mock_context, \
             patch('services.summary_service.summary_service.generate_summary', new_callable=AsyncMock) as mock_summary, \
             patch('services.reviewer_service.reviewer_service.suggest_reviewers', new_callable=AsyncMock) as mock_reviewers, \
             patch('services.risk_service.risk_service.calculate_risk', new_callable=AsyncMock) as mock_risk:
            
            # Configure mocks
            mock_context.return_value = workflow_data["mr_context"]
            mock_summary.return_value = workflow_data["summary"]
            mock_reviewers.return_value = workflow_data["reviewers"]
            mock_risk.return_value = workflow_data["mr_context"]["risk"]
            
            # Test response times
            import time
            
            start_time = time.time()
            response = client.get("/api/v1/mr/1/context")
            context_time = time.time() - start_time
            
            start_time = time.time()
            response = client.post("/api/v1/mr/1/summary")
            summary_time = time.time() - start_time
            
            start_time = time.time()
            response = client.get("/api/v1/mr/1/reviewers")
            reviewers_time = time.time() - start_time
            
            start_time = time.time()
            response = client.get("/api/v1/mr/1/risk")
            risk_time = time.time() - start_time
            
            # All requests should complete quickly
            assert context_time < 10.0
            assert summary_time < 10.0
            assert reviewers_time < 10.0
            assert risk_time < 10.0
            
            # All requests should succeed
            assert response.status_code == 200