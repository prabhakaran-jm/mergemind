"""
Tests for GitLab Fivetran Connector
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from ingestion.fivetran_connector.connector import GitLabConnector


class TestGitLabConnector:
    """Test cases for GitLab connector."""
    
    @pytest.fixture
    def connector(self):
        """Create connector instance for testing."""
        with patch.dict('os.environ', {
            'GITLAB_TOKEN': 'test-token',
            'GITLAB_PROJECT_IDS': '100,101'
        }):
            return GitLabConnector()
    
    def test_connector_initialization(self, connector):
        """Test connector initialization."""
        assert connector.gitlab_token == 'test-token'
        assert connector.gitlab_base_url == 'https://gitlab.com'
        assert connector.project_ids == [100, 101]
    
    def test_get_project_ids(self, connector):
        """Test project ID parsing."""
        assert connector._get_project_ids() == [100, 101]
    
    def test_schema_definition(self, connector):
        """Test schema definition."""
        schema = connector.get_schema()
        
        # Check that all expected tables are present
        table_names = [table.name for table in schema]
        expected_tables = ['merge_requests', 'mr_notes', 'pipelines', 'projects', 'users']
        
        for table_name in expected_tables:
            assert table_name in table_names
        
        # Check merge_requests table structure
        mr_table = next(table for table in schema if table.name == 'merge_requests')
        assert len(mr_table.columns) == 22  # Expected number of columns
    
    @patch('requests.get')
    def test_make_request_success(self, mock_get, connector):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {'id': 1, 'name': 'test'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = connector._make_request('https://gitlab.com/api/v4/test')
        
        assert result == {'id': 1, 'name': 'test'}
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_make_request_failure(self, mock_get, connector):
        """Test API request failure."""
        mock_get.side_effect = Exception('API Error')
        
        with pytest.raises(Exception):
            connector._make_request('https://gitlab.com/api/v4/test')
    
    def test_normalize_timestamp(self, connector):
        """Test timestamp normalization."""
        # Valid timestamp
        result = connector._normalize_timestamp('2024-01-15T10:30:00Z')
        assert result == '2024-01-15T10:30:00Z'
        
        # None timestamp
        result = connector._normalize_timestamp(None)
        assert result is None
        
        # Invalid timestamp
        result = connector._normalize_timestamp('invalid')
        assert result == 'invalid'  # Should return as-is
    
    def test_classify_note_type(self, connector):
        """Test note type classification."""
        # Approval notes
        assert connector._classify_note_type('Approved!') == 'approval'
        assert connector._classify_note_type('LGTM') == 'approval'
        assert connector._classify_note_type('looks good to me') == 'approval'
        
        # Review notes
        assert connector._classify_note_type('I reviewed this') == 'review'
        
        # Comments
        assert connector._classify_note_type('This is a comment') == 'comment'
        assert connector._classify_note_type('a' * 150) == 'comment'  # Long text
    
    def test_extract_mr_data(self, connector):
        """Test MR data extraction."""
        mr_data = {
            'id': 123,
            'title': 'Test MR',
            'description': 'Test description',
            'author': {'id': 456},
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T11:00:00Z',
            'merged_at': None,
            'closed_at': None,
            'state': 'opened',
            'source_branch': 'feature/test',
            'target_branch': 'main',
            'web_url': 'https://gitlab.com/test/mr/123',
            'sha': 'abc123',
            'merge_commit_sha': None,
            'changes_count': {'additions': 50, 'deletions': 10},
            'approvals_left': 2,
            'labels': ['frontend', 'bug'],
            'work_in_progress': False,
            'merge_status': 'can_be_merged',
            'has_conflicts': False,
            'blocking_discussions_resolved': True
        }
        
        result = connector._extract_mr_data(mr_data, 100)
        
        assert result['mr_id'] == 123
        assert result['project_id'] == 100
        assert result['title'] == 'Test MR'
        assert result['author_id'] == 456
        assert result['additions'] == 50
        assert result['deletions'] == 10
        assert result['approvals_left'] == 2
        assert result['labels'] == '["frontend", "bug"]'
    
    def test_extract_note_data(self, connector):
        """Test note data extraction."""
        note_data = {
            'id': 789,
            'author': {'id': 456},
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z',
            'body': 'Approved!',
            'system': False,
            'resolved': False,
            'resolvable': True
        }
        
        result = connector._extract_note_data(note_data, 100, 123)
        
        assert result['note_id'] == 789
        assert result['project_id'] == 100
        assert result['mr_id'] == 123
        assert result['author_id'] == 456
        assert result['body'] == 'Approved!'
        assert result['note_type'] == 'approval'
        assert result['system'] is False
    
    def test_extract_pipeline_data(self, connector):
        """Test pipeline data extraction."""
        pipeline_data = {
            'id': 999,
            'status': 'success',
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:35:00Z',
            'started_at': '2024-01-15T10:30:00Z',
            'finished_at': '2024-01-15T10:35:00Z',
            'duration': 300,
            'web_url': 'https://gitlab.com/test/pipeline/999',
            'ref': 'main',
            'sha': 'abc123'
        }
        
        result = connector._extract_pipeline_data(pipeline_data, 100, 123)
        
        assert result['pipeline_id'] == 999
        assert result['project_id'] == 100
        assert result['mr_id'] == 123
        assert result['status'] == 'success'
        assert result['duration'] == 300
    
    def test_extract_project_data(self, connector):
        """Test project data extraction."""
        project_data = {
            'id': 100,
            'name': 'Test Project',
            'path': 'test-project',
            'path_with_namespace': 'group/test-project',
            'description': 'A test project',
            'created_at': '2024-01-01T00:00:00Z',
            'last_activity_at': '2024-01-15T10:30:00Z',
            'visibility': 'private',
            'web_url': 'https://gitlab.com/group/test-project',
            'default_branch': 'main',
            'archived': False,
            'forked_from_project': None
        }
        
        result = connector._extract_project_data(project_data)
        
        assert result['project_id'] == 100
        assert result['name'] == 'Test Project'
        assert result['path'] == 'test-project'
        assert result['visibility'] == 'private'
        assert result['archived'] is False
    
    def test_extract_user_data(self, connector):
        """Test user data extraction."""
        user_data = {
            'id': 456,
            'name': 'John Doe',
            'username': 'johndoe',
            'email': 'john@example.com',
            'created_at': '2024-01-01T00:00:00Z',
            'last_activity_on': '2024-01-15',
            'state': 'active',
            'avatar_url': 'https://gitlab.com/avatar.jpg',
            'web_url': 'https://gitlab.com/johndoe',
            'is_admin': False,
            'can_create_group': True,
            'can_create_project': True
        }
        
        result = connector._extract_user_data(user_data)
        
        assert result['user_id'] == 456
        assert result['name'] == 'John Doe'
        assert result['username'] == 'johndoe'
        assert result['email'] == 'john@example.com'
        assert result['state'] == 'active'
        assert result['is_admin'] is False
    
    @patch.object(GitLabConnector, '_get_merge_requests')
    def test_read_merge_requests(self, mock_get_mrs, connector):
        """Test reading merge requests."""
        mock_mrs = [
            {
                'id': 123,
                'title': 'Test MR',
                'author': {'id': 456},
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T11:00:00Z',
                'merged_at': None,
                'closed_at': None,
                'state': 'opened',
                'source_branch': 'feature/test',
                'target_branch': 'main',
                'web_url': 'https://gitlab.com/test/mr/123',
                'sha': 'abc123',
                'merge_commit_sha': None,
                'changes_count': {'additions': 50, 'deletions': 10},
                'approvals_left': 2,
                'labels': ['frontend'],
                'work_in_progress': False,
                'merge_status': 'can_be_merged',
                'has_conflicts': False,
                'blocking_discussions_resolved': True
            }
        ]
        mock_get_mrs.return_value = mock_mrs
        
        results = list(connector.read('merge_requests'))
        
        assert len(results) == 2  # One MR per project
        assert results[0]['mr_id'] == 123
        assert results[0]['title'] == 'Test MR'
    
    @patch.object(GitLabConnector, '_get_merge_requests')
    @patch.object(GitLabConnector, '_get_mr_notes')
    def test_read_mr_notes(self, mock_get_notes, mock_get_mrs, connector):
        """Test reading MR notes."""
        mock_mrs = [{'id': 123, 'author': {'id': 456}}]
        mock_get_mrs.return_value = mock_mrs
        
        mock_notes = [
            {
                'id': 789,
                'author': {'id': 456},
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T10:30:00Z',
                'body': 'Approved!',
                'system': False,
                'resolved': False,
                'resolvable': True
            }
        ]
        mock_get_notes.return_value = mock_notes
        
        results = list(connector.read('mr_notes'))
        
        assert len(results) == 2  # One note per project
        assert results[0]['note_id'] == 789
        assert results[0]['body'] == 'Approved!'
    
    def test_read_unknown_table(self, connector):
        """Test reading unknown table."""
        with pytest.raises(ValueError, match="Unknown table"):
            list(connector.read('unknown_table'))


if __name__ == '__main__':
    pytest.main([__file__])
