'''
Tests for the service layer.
'''

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Import the classes, not the global instances
from services.bigquery_client import BigQueryClient
from services.gitlab_client import GitLabClient
from services.vertex_client import VertexAIClient
from services.risk_service import RiskService
from services.reviewer_service import ReviewerService
from services.summary_service import SummaryService
from services.user_service import UserService
from services.metrics import MetricsService

# Fixtures to provide fresh instances for each test

@pytest.fixture
def bq_client(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("BQ_DATASET_RAW", "mergemind_raw")
    monkeypatch.setenv("BQ_DATASET_MODELED", "mergemind")
    with patch('google.cloud.bigquery.Client'):
        yield BigQueryClient()

@pytest.fixture
def gitlab_client(monkeypatch):
    monkeypatch.setenv("GITLAB_BASE_URL", "https://gitlab.com")
    monkeypatch.setenv("GITLAB_TOKEN", "test-token")
    return GitLabClient()

@pytest.fixture
def vertex_client(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("VERTEX_LOCATION", "us-central1")
    with patch('vertexai.generative_models.GenerativeModel'):
        yield VertexAIClient()


class TestBigQueryClient:
    def test_init_success(self, monkeypatch):
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        monkeypatch.setenv("BQ_DATASET_RAW", "test_raw")
        monkeypatch.setenv("BQ_DATASET_MODELED", "test_modeled")
        with patch('google.cloud.bigquery.Client'):
            client = BigQueryClient()
            assert client.project_id == "test-project"
            assert client.dataset_raw == "test_raw"

    def test_init_missing_project(self, monkeypatch):
        # Clear the environment variable that might be set by the test runner
        monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
        # Also clear it from os.environ directly to ensure it's removed
        if "GCP_PROJECT_ID" in os.environ:
            del os.environ["GCP_PROJECT_ID"]
        
        # Mock the Settings class to avoid Pydantic validation
        with patch('services.bigquery_client.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.gcp_project_id = None  # Simulate missing project ID
            mock_get_settings.return_value = mock_settings
            
            with pytest.raises(ValueError, match="GCP_PROJECT_ID environment variable is required"):
                with patch('google.cloud.bigquery.Client'):
                    BigQueryClient()

@pytest.mark.asyncio
class TestGitLabClient:
    async def test_get_merge_request_diff(self, gitlab_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"changes": [{"diff": "fake diff"}]}

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock, return_value=mock_response) as mock_get:
            diff = await gitlab_client.get_merge_request_diff(1, 1)
            # The method adds diff headers, so expect the formatted output
            assert diff == "--- \n+++ \nfake diff\n"

class TestVertexAIClient:
    def test_generate_text_success(self, vertex_client):
        # Mock the model's generate_content method
        with patch.object(vertex_client.model, 'generate_content') as mock_generate:
            mock_response = MagicMock()
            mock_response.text = 'Generated text'
            mock_generate.return_value = mock_response
            
            result = vertex_client.generate_text("Test prompt")
            assert result == "Generated text"

@pytest.mark.asyncio
class TestRiskService:
    @pytest.fixture
    def risk_service(self, bq_client, gitlab_client):
        with patch('services.risk_service.bigquery_client', bq_client), \
             patch('services.risk_service.gitlab_client', gitlab_client):
            yield RiskService()

    async def test_calculate_risk_success(self, risk_service):
        with patch.object(risk_service, '_get_risk_features') as mock_get_features, \
             patch('services.risk_service.score') as mock_score, \
             patch.object(risk_service, '_calculate_ai_risk', new_callable=AsyncMock) as mock_ai_risk:
            
            mock_get_features.return_value = {"last_pipeline_status_is_fail": False, "approvals_left": 1, "change_size_bucket": "S", "work_in_progress": False, "labels_sensitive": False, "age_hours": 1, "notes_count_24h": 1, "author_recent_fail_rate_7d": 0, "repo_merge_conflict_rate_14d": 0}
            mock_score.return_value = {"score": 50, "band": "Medium", "reasons": []}
            mock_ai_risk.return_value = {"overall_score": 60}

            result = await risk_service.calculate_risk(1)
            assert result["combined_score"] == 53.0
            assert result["combined_band"] == "Medium"

@pytest.mark.asyncio
class TestReviewerService:
    @pytest.fixture
    def reviewer_service(self, bq_client, gitlab_client):
        with patch('services.reviewer_service.bigquery_client', bq_client), \
             patch('services.reviewer_service.gitlab_client', gitlab_client):
            yield ReviewerService()

    async def test_suggest_reviewers_success(self, reviewer_service):
        with patch.object(reviewer_service, '_get_mr_context') as mock_get_context, \
             patch.object(reviewer_service.suggester, 'suggest') as mock_suggest, \
             patch.object(reviewer_service, '_get_ai_suggestions', new_callable=AsyncMock) as mock_ai_suggest:

            mock_get_context.return_value = {"author_id": 1}
            mock_suggest.return_value = [{"user_id": 2}]
            mock_ai_suggest.return_value = {"suggestions": [{"user_id": 3}]}

            result = await reviewer_service.suggest_reviewers(1)
            assert len(result["suggestions"]) == 2

@pytest.mark.asyncio
class TestSummaryService:
    @pytest.fixture
    def summary_service(self, bq_client, gitlab_client):
        with patch('services.summary_service.bigquery_client', bq_client), \
             patch('services.summary_service.gitlab_client', gitlab_client):
            yield SummaryService()

    async def test_generate_summary_success(self, summary_service):
        with patch.object(summary_service, '_get_mr_data') as mock_get_data, \
             patch.object(summary_service.gitlab_client, 'get_merge_request_diff', new_callable=AsyncMock) as mock_get_diff, \
             patch.object(summary_service.summarizer, 'summarize_diff') as mock_summarize:

            mock_get_data.return_value = {"project_id": 1, "sha": "abc"}
            mock_get_diff.return_value = "fake diff"
            mock_summarize.return_value = {"summary": "Test summary"}

            result = await summary_service.generate_summary(1)
            assert result["summary"] == "Test summary"

class TestUserService:
    @pytest.fixture
    def user_service(self, bq_client):
        with patch('services.user_service.bigquery_client', bq_client):
            yield UserService()

    def test_get_user_name(self, user_service):
        with patch.object(user_service, '_get_user_from_bigquery') as mock_get_user:
            mock_get_user.return_value = {"name": "Test User"}
            result = user_service.get_user_name(1)
            assert result == "Test User"

class TestMetricsService:
    def test_record_request(self):
        service = MetricsService()
        service.record_request("test_endpoint", "GET", 200, 0.1)
        assert service.collector.request_count == 1
