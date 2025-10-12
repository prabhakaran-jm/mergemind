"""
Tests for service layer components.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from services.bigquery_client import BigQueryClient
from services.gitlab_client import GitLabClient
from services.vertex_client import VertexAIClient
from services.reviewer_service import ReviewerService
from services.risk_service import RiskService
from services.summary_service import SummaryService
from services.user_service import UserService
from services.metrics import MetricsService


class TestBigQueryClient:
    """Test BigQuery client service."""
    
    def test_init_success(self):
        """Test successful initialization."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('google.cloud.bigquery.Client'):
                client = BigQueryClient()
                assert client.project_id == 'test-project'
                assert client.dataset_raw == 'mergemind_raw'
                assert client.dataset_modeled == 'mergemind'
    
    def test_init_missing_project(self):
        """Test initialization with missing project ID."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GCP_PROJECT_ID environment variable is required"):
                BigQueryClient()
    
    def test_query_success(self):
        """Test successful query execution."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('google.cloud.bigquery.Client') as mock_client:
                # Mock query result
                mock_row = MagicMock()
                mock_row.__iter__ = lambda x: iter([('test_value', 1)])
                mock_row.keys.return_value = ['test_value']
                mock_row.__getitem__ = lambda x, y: 1 if y == 'test_value' else None
                
                mock_query_job = MagicMock()
                mock_query_job.result.return_value = [mock_row]
                mock_client.return_value.query.return_value = mock_query_job
                
                client = BigQueryClient()
                result = client.query("SELECT 1 as test_value")
                
                assert len(result) == 1
                assert result[0]['test_value'] == 1
    
    def test_query_with_params(self):
        """Test query with parameters."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('google.cloud.bigquery.Client') as mock_client:
                mock_query_job = MagicMock()
                mock_query_job.result.return_value = []
                mock_client.return_value.query.return_value = mock_query_job
                
                client = BigQueryClient()
                client.query("SELECT * FROM table WHERE id = @id", id=123)
                
                # Verify query was called with formatted SQL
                mock_client.return_value.query.assert_called_once()
                call_args = mock_client.return_value.query.call_args[0][0]
                assert "123" in call_args
    
    def test_table_exists_true(self):
        """Test table existence check - table exists."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('google.cloud.bigquery.Client') as mock_client:
                mock_client.return_value.get_table.return_value = MagicMock()
                
                client = BigQueryClient()
                result = client.table_exists("dataset", "table")
                
                assert result is True
    
    def test_table_exists_false(self):
        """Test table existence check - table doesn't exist."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('google.cloud.bigquery.Client') as mock_client:
                from google.cloud.exceptions import NotFound
                mock_client.return_value.get_table.side_effect = NotFound("Table not found")
                
                client = BigQueryClient()
                result = client.table_exists("dataset", "table")
                
                assert result is False
    
    def test_test_connection_success(self):
        """Test connection test - success."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('google.cloud.bigquery.Client') as mock_client:
                mock_row = MagicMock()
                mock_row.__iter__ = lambda x: iter([('test_value', 1)])
                mock_row.keys.return_value = ['test_value']
                mock_row.__getitem__ = lambda x, y: 1 if y == 'test_value' else None
                
                mock_query_job = MagicMock()
                mock_query_job.result.return_value = [mock_row]
                mock_client.return_value.query.return_value = mock_query_job
                
                client = BigQueryClient()
                result = client.test_connection()
                
                assert result is True
    
    def test_test_connection_failure(self):
        """Test connection test - failure."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('google.cloud.bigquery.Client') as mock_client:
                mock_client.return_value.query.side_effect = Exception("Connection failed")
                
                client = BigQueryClient()
                result = client.test_connection()
                
                assert result is False


class TestGitLabClient:
    """Test GitLab client service."""
    
    def test_init_success(self):
        """Test successful initialization."""
        with patch.dict('os.environ', {'GITLAB_TOKEN': 'test-token'}):
            client = GitLabClient()
            assert client.token == 'test-token'
            assert client.base_url == 'https://gitlab.com'
            assert 'Authorization' in client.headers
    
    def test_init_no_token(self):
        """Test initialization without token."""
        with patch.dict('os.environ', {}, clear=True):
            client = GitLabClient()
            assert client.token is None
            assert client.headers == {}
    
    @pytest.mark.asyncio
    async def test_get_merge_request_success(self):
        """Test successful MR retrieval."""
        with patch.dict('os.environ', {'GITLAB_TOKEN': 'test-token'}):
            client = GitLabClient()
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"id": 1, "title": "Test MR"}
                
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await client.get_merge_request(4, 1)
                
                assert result["id"] == 1
                assert result["title"] == "Test MR"
    
    @pytest.mark.asyncio
    async def test_get_merge_request_not_found(self):
        """Test MR retrieval - not found."""
        with patch.dict('os.environ', {'GITLAB_TOKEN': 'test-token'}):
            client = GitLabClient()
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 404
                
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await client.get_merge_request(4, 999)
                
                assert result is None
    
    def test_test_connection_success(self):
        """Test connection test - success."""
        with patch.dict('os.environ', {'GITLAB_TOKEN': 'test-token'}):
            client = GitLabClient()
            
            with patch('httpx.Client') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                
                mock_client.return_value.__enter__.return_value.get.return_value = mock_response
                
                result = client.test_connection()
                
                assert result is True
    
    def test_test_connection_failure(self):
        """Test connection test - failure."""
        with patch.dict('os.environ', {'GITLAB_TOKEN': 'test-token'}):
            client = GitLabClient()
            
            with patch('httpx.Client') as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Connection failed")
                
                result = client.test_connection()
                
                assert result is False


class TestVertexAIClient:
    """Test Vertex AI client service."""
    
    def test_init_success(self):
        """Test successful initialization."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('vertexai.init'), \
                 patch('vertexai.generative_models.GenerativeModel'):
                client = VertexAIClient()
                assert client.project_id == 'test-project'
                assert client.location == 'europe-west2'
    
    def test_init_missing_project(self):
        """Test initialization with missing project ID."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GCP_PROJECT_ID environment variable is required"):
                VertexAIClient()
    
    def test_generate_text_success(self):
        """Test successful text generation."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('vertexai.init'), \
                 patch('vertexai.generative_models.GenerativeModel') as mock_model:
                
                mock_response = MagicMock()
                mock_response.text = "Generated text response"
                mock_model.return_value.generate_content.return_value = mock_response
                
                client = VertexAIClient()
                result = client.generate_text("Test prompt")
                
                assert result == "Generated text response"
    
    def test_generate_text_failure(self):
        """Test text generation failure."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('vertexai.init'), \
                 patch('vertexai.generative_models.GenerativeModel') as mock_model:
                
                mock_model.return_value.generate_content.side_effect = Exception("Generation failed")
                
                client = VertexAIClient()
                
                with pytest.raises(Exception, match="Generation failed"):
                    client.generate_text("Test prompt")
    
    def test_summarize_diff_success(self):
        """Test successful diff summarization."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('vertexai.init'), \
                 patch('vertexai.generative_models.GenerativeModel') as mock_model:
                
                mock_response = MagicMock()
                mock_response.text = '{"summary": ["Test summary"], "risks": ["Test risk"], "tests": ["Test test"]}'
                mock_model.return_value.generate_content.return_value = mock_response
                
                client = VertexAIClient()
                result = client.summarize_diff(
                    title="Test MR",
                    description="Test description",
                    files=["file1.py"],
                    additions=10,
                    deletions=5,
                    diff_snippets="diff content"
                )
                
                assert "summary" in result
                assert "risks" in result
                assert "tests" in result
    
    def test_summarize_diff_empty_content(self):
        """Test diff summarization with empty content."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('vertexai.init'), \
                 patch('vertexai.generative_models.GenerativeModel'):
                
                client = VertexAIClient()
                result = client.summarize_diff(
                    title="Test MR",
                    description="Test description",
                    files=[],
                    additions=0,
                    deletions=0,
                    diff_snippets=""
                )
                
                assert "Insufficient context for analysis" in result["summary"][0]
    
    def test_test_connection_success(self):
        """Test connection test - success."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('vertexai.init'), \
                 patch('vertexai.generative_models.GenerativeModel') as mock_model:
                
                mock_response = MagicMock()
                mock_response.text = "Test response"
                mock_model.return_value.generate_content.return_value = mock_response
                
                client = VertexAIClient()
                result = client.test_connection()
                
                assert result is True
    
    def test_test_connection_failure(self):
        """Test connection test - failure."""
        with patch.dict('os.environ', {'GCP_PROJECT_ID': 'test-project'}):
            with patch('vertexai.init'), \
                 patch('vertexai.generative_models.GenerativeModel') as mock_model:
                
                mock_model.return_value.generate_content.side_effect = Exception("Connection failed")
                
                client = VertexAIClient()
                result = client.test_connection()
                
                assert result is False


class TestReviewerService:
    """Test reviewer service."""
    
    def test_init(self):
        """Test service initialization."""
        with patch('services.bigquery_client.bigquery_client'), \
             patch('services.user_service.user_service'):
            service = ReviewerService()
            assert service.bq_client is not None
            assert service.user_service is not None
    
    def test_suggest_reviewers_success(self):
        """Test successful reviewer suggestions."""
        with patch('services.bigquery_client.bigquery_client') as mock_bq, \
             patch('services.user_service.user_service') as mock_user, \
             patch('ai.reviewers.suggest.ReviewerSuggester') as mock_suggester:
            
            mock_suggester.return_value.suggest.return_value = [
                {"user_id": 2, "name": "reviewer1", "score": 0.8, "reason": "Good match"}
            ]
            
            service = ReviewerService()
            result = service.suggest_reviewers(1)
            
            assert len(result) == 1
            assert result[0]["name"] == "reviewer1"
    
    def test_suggest_reviewers_no_context(self):
        """Test reviewer suggestions with no MR context."""
        with patch('services.bigquery_client.bigquery_client') as mock_bq, \
             patch('services.user_service.user_service') as mock_user, \
             patch('ai.reviewers.suggest.ReviewerSuggester') as mock_suggester:
            
            mock_bq.query.return_value = []  # No context found
            
            service = ReviewerService()
            result = service.suggest_reviewers(999)
            
            assert result == []


class TestRiskService:
    """Test risk service."""
    
    def test_init(self):
        """Test service initialization."""
        with patch('services.bigquery_client.bigquery_client'):
            service = RiskService()
            assert service.bq_client is not None
    
    def test_calculate_risk_success(self):
        """Test successful risk calculation."""
        with patch('services.bigquery_client.bigquery_client') as mock_bq, \
             patch('ai.scoring.rules.score') as mock_score:
            
            mock_bq.query.return_value = [{
                "mr_id": 1,
                "age_hours": 24,
                "notes_count_24h": 2,
                "last_pipeline_status_is_fail": False,
                "approvals_left": 1,
                "change_size_bucket": "S",
                "work_in_progress": False,
                "labels_sensitive": False
            }]
            
            mock_score.return_value = {
                "score": 25,
                "band": "Low",
                "reasons": ["Small change"]
            }
            
            service = RiskService()
            result = service.calculate_risk(1)
            
            assert result["score"] == 25
            assert result["band"] == "Low"
    
    def test_calculate_risk_no_features(self):
        """Test risk calculation with no features."""
        with patch('services.bigquery_client.bigquery_client') as mock_bq:
            mock_bq.query.return_value = []  # No features found
            
            service = RiskService()
            result = service.calculate_risk(999)
            
            assert result["score"] == 0
            assert result["band"] == "Low"
            assert "No risk features available" in result["reasons"]


class TestUserService:
    """Test user service."""
    
    def test_init(self):
        """Test service initialization."""
        with patch('services.bigquery_client.bigquery_client'), \
             patch('services.gitlab_client.gitlab_client'):
            service = UserService()
            assert service.bq_client is not None
            assert service.gitlab_client is not None
            assert service._user_cache == {}
    
    def test_get_user_name_from_cache(self):
        """Test user name retrieval from cache."""
        with patch('services.bigquery_client.bigquery_client'), \
             patch('services.gitlab_client.gitlab_client'):
            service = UserService()
            service._user_cache[1] = "cached_user"
            
            result = service.get_user_name(1)
            
            assert result == "cached_user"
    
    def test_get_user_name_from_bigquery(self):
        """Test user name retrieval from BigQuery."""
        with patch('services.bigquery_client.bigquery_client') as mock_bq, \
             patch('services.gitlab_client.gitlab_client'):
            
            mock_bq.query.return_value = [{
                "user_id": 1,
                "username": "testuser",
                "name": "Test User"
            }]
            
            service = UserService()
            result = service.get_user_name(1)
            
            assert result == "Test User"
            assert 1 in service._user_cache
    
    def test_get_user_name_fallback(self):
        """Test user name retrieval fallback."""
        with patch('services.bigquery_client.bigquery_client') as mock_bq, \
             patch('services.gitlab_client.gitlab_client'):
            
            mock_bq.query.return_value = []  # No user found
            
            service = UserService()
            result = service.get_user_name(999)
            
            assert result == "User 999"
            assert 999 in service._user_cache
    
    def test_get_users_by_ids(self):
        """Test multiple user name retrieval."""
        with patch('services.bigquery_client.bigquery_client') as mock_bq, \
             patch('services.gitlab_client.gitlab_client'):
            
            mock_bq.query.return_value = []  # No users found
            
            service = UserService()
            result = service.get_users_by_ids([1, 2, 3])
            
            assert result == {1: "User 1", 2: "User 2", 3: "User 3"}


class TestMetricsService:
    """Test metrics service."""
    
    def test_init(self):
        """Test service initialization."""
        service = MetricsService()
        assert service.collector is not None
    
    def test_record_request(self):
        """Test request recording."""
        service = MetricsService()
        
        # Record a request
        service.record_request("/test", "GET", 200, 0.1)
        
        # Get summary
        summary = service.get_summary()
        
        assert summary["request_count"] == 1
        assert summary["error_count"] == 0
        assert summary["error_rate"] == 0
    
    def test_record_error_request(self):
        """Test error request recording."""
        service = MetricsService()
        
        # Record an error request
        service.record_request("/test", "GET", 500, 0.1, Exception("Test error"))
        
        # Get summary
        summary = service.get_summary()
        
        assert summary["request_count"] == 1
        assert summary["error_count"] == 1
        assert summary["error_rate"] == 1.0
    
    def test_check_slo_violations(self):
        """Test SLO violation checking."""
        service = MetricsService()
        
        # Record requests that violate SLOs
        for _ in range(10):
            service.record_request("/test", "GET", 500, 3.0)  # High latency, high error rate
        
        result = service.check_slo_violations()
        
        assert result["status"] == "degraded"
        assert len(result["violations"]) > 0
    
    def test_reset_metrics(self):
        """Test metrics reset."""
        service = MetricsService()
        
        # Record some requests
        service.record_request("/test", "GET", 200, 0.1)
        
        # Reset metrics
        service.reset_metrics()
        
        # Get summary
        summary = service.get_summary()
        
        assert summary["request_count"] == 0
        assert summary["error_count"] == 0
