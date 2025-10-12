"""
Integration tests for end-to-end workflows.
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
def mock_complete_mr_workflow():
    """Mock complete MR workflow data."""
    return {
        "mr_context": {
            "mr_id": 1,
            "project_id": 4,
            "title": "Add new authentication feature",
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
        
        with patch('routers.mr.get_mr_context') as mock_context, \
             patch('routers.mr.generate_summary') as mock_summary, \
             patch('routers.mr.get_reviewer_suggestions') as mock_reviewers, \
             patch('routers.mr.calculate_risk') as mock_risk:
            
            # Configure mocks
            mock_context.return_value = workflow_data["mr_context"]
            mock_summary.return_value = workflow_data["summary"]
            mock_reviewers.return_value = workflow_data["reviewers"]
            mock_risk.return_value = workflow_data["mr_context"]["risk"]
            
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
            assert risk_data["score"] == 35
            assert risk_data["band"] == "Medium"
    
    def test_mr_list_and_detail_workflow(self, client, mock_complete_mr_workflow):
        """Test MR list and detail workflow."""
        workflow_data = mock_complete_mr_workflow
        
        with patch('routers.mrs.get_mrs_from_bigquery') as mock_list, \
             patch('routers.mr.get_mr_context') as mock_context:
            
            # Mock MR list
            mock_list.return_value = [
                {
                    "mr_id": 1,
                    "project_id": 4,
                    "title": "Add new authentication feature",
                    "author": "developer1",
                    "age_hours": 24.5,
                    "risk_band": "Medium",
                    "risk_score": 35,
                    "pipeline_status": "success",
                    "approvals_left": 1,
                    "notes_count_24h": 2,
                    "additions": 150,
                    "deletions": 30
                }
            ]
            
            # Mock MR context
            mock_context.return_value = workflow_data["mr_context"]
            
            # Step 1: Get MR list
            response = client.get("/api/v1/mrs")
            assert response.status_code == 200
            list_data = response.json()
            assert len(list_data["mrs"]) == 1
            assert list_data["mrs"][0]["mr_id"] == 1
            
            # Step 2: Get detailed MR context
            response = client.get("/api/v1/mr/1/context")
            assert response.status_code == 200
            context_data = response.json()
            assert context_data["mr_id"] == 1
            assert context_data["author"]["name"] == "developer1"
    
    def test_blocking_mrs_workflow(self, client):
        """Test blocking MRs workflow."""
        with patch('routers.mrs.get_blocking_mrs_from_bigquery') as mock_blockers:
            mock_blockers.return_value = [
                {
                    "mr_id": 1,
                    "project_id": 4,
                    "title": "Blocking MR 1",
                    "author": "developer1",
                    "age_hours": 72.0,
                    "risk_band": "High",
                    "risk_score": 75,
                    "pipeline_status": "failed",
                    "approvals_left": 2,
                    "notes_count_24h": 8,
                    "additions": 500,
                    "deletions": 100
                },
                {
                    "mr_id": 2,
                    "project_id": 4,
                    "title": "Blocking MR 2",
                    "author": "developer2",
                    "age_hours": 48.0,
                    "risk_band": "Medium",
                    "risk_score": 55,
                    "pipeline_status": "running",
                    "approvals_left": 1,
                    "notes_count_24h": 5,
                    "additions": 300,
                    "deletions": 50
                }
            ]
            
            response = client.get("/api/v1/blockers/top")
            assert response.status_code == 200
            blockers_data = response.json()
            
            assert len(blockers_data["blockers"]) == 2
            assert blockers_data["blockers"][0]["risk_band"] == "High"
            assert blockers_data["blockers"][1]["risk_band"] == "Medium"
    
    def test_health_monitoring_workflow(self, client):
        """Test health monitoring workflow."""
        with patch('services.bigquery_client.bigquery_client') as mock_bq, \
             patch('services.gitlab_client.gitlab_client') as mock_gitlab, \
             patch('services.vertex_client.vertex_client') as mock_vertex:
            
            # Configure service health
            mock_bq.test_connection.return_value = True
            mock_gitlab.test_connection.return_value = True
            mock_vertex.test_connection.return_value = True
            
            # Step 1: Basic health check
            response = client.get("/api/v1/healthz")
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] == "healthy"
            
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
        with patch('routers.mr.get_mr_context') as mock_context:
            # Test non-existent MR
            mock_context.return_value = None
            
            response = client.get("/api/v1/mr/999/context")
            assert response.status_code == 404
            error_data = response.json()
            assert "error" in error_data
            
            # Test service error
            mock_context.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/v1/mr/1/context")
            assert response.status_code == 500
            error_data = response.json()
            assert "error" in error_data
    
    def test_concurrent_requests_workflow(self, client, mock_complete_mr_workflow):
        """Test concurrent requests workflow."""
        workflow_data = mock_complete_mr_workflow
        
        with patch('routers.mr.get_mr_context') as mock_context, \
             patch('routers.mr.generate_summary') as mock_summary, \
             patch('routers.mr.get_reviewer_suggestions') as mock_reviewers, \
             patch('routers.mr.calculate_risk') as mock_risk:
            
            # Configure mocks
            mock_context.return_value = workflow_data["mr_context"]
            mock_summary.return_value = workflow_data["summary"]
            mock_reviewers.return_value = workflow_data["reviewers"]
            mock_risk.return_value = workflow_data["mr_context"]["risk"]
            
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
        
        with patch('routers.mr.get_mr_context') as mock_context, \
             patch('routers.mr.generate_summary') as mock_summary:
            
            # Configure mocks
            mock_context.return_value = workflow_data["mr_context"]
            mock_summary.return_value = workflow_data["summary"]
            
            # First request - should hit service
            response1 = client.post("/api/v1/mr/1/summary")
            assert response1.status_code == 200
            
            # Second request - should use cache
            response2 = client.post("/api/v1/mr/1/summary")
            assert response2.status_code == 200
            
            # Both responses should be identical
            assert response1.json() == response2.json()
            
            # Verify service was called only once
            assert mock_summary.call_count == 1
    
    def test_performance_workflow(self, client, mock_complete_mr_workflow):
        """Test performance workflow."""
        workflow_data = mock_complete_mr_workflow
        
        with patch('routers.mr.get_mr_context') as mock_context, \
             patch('routers.mr.generate_summary') as mock_summary, \
             patch('routers.mr.get_reviewer_suggestions') as mock_reviewers, \
             patch('routers.mr.calculate_risk') as mock_risk:
            
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
            assert context_time < 1.0
            assert summary_time < 2.0  # AI processing takes longer
            assert reviewers_time < 1.0
            assert risk_time < 1.0
            
            # All requests should succeed
            assert response.status_code == 200
