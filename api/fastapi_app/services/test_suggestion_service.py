"""
Test suggestion service for merge requests.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.bigquery_client import bigquery_client
from services.gitlab_client import gitlab_client
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from ai.testing.test_suggester import ai_test_suggester

logger = logging.getLogger(__name__)


class TestSuggestionService:
    """Service for generating test suggestions for merge requests."""
    
    def __init__(self):
        """Initialize test suggestion service."""
        self.bq_client = bigquery_client
        self.gitlab_client = gitlab_client
        self.ai_suggester = ai_test_suggester
    
    async def suggest_tests(self, mr_id: int) -> Dict[str, Any]:
        """
        Generate test suggestions for a merge request.
        
        Args:
            mr_id: Merge request ID
            
        Returns:
            Dictionary with test suggestions
        """
        try:
            # Get MR details from BigQuery
            mr_details = self._get_mr_details(mr_id)
            if not mr_details:
                logger.warning(f"No MR details found for test suggestions: {mr_id}")
                return {
                    "error": "No MR details available",
                    "fallback": True
                }
            
            # Get diff content from GitLab
            project_id = mr_details.get("project_id")
            if not project_id:
                logger.warning(f"No project ID found for MR {mr_id}")
                return {
                    "error": "No project ID available",
                    "fallback": True
                }
            
            try:
                diff_content = await self.gitlab_client.get_merge_request_diff(project_id, mr_id)
                if not diff_content:
                    logger.warning(f"No diff content available for MR {mr_id}")
                    return {
                        "error": "No diff content available",
                        "fallback": True
                    }
            except Exception as e:
                logger.warning(f"Failed to get diff content for MR {mr_id}: {e}")
                return {
                    "error": f"Failed to get diff content: {str(e)}",
                    "fallback": True
                }
            
            # Extract file information from diff
            files = self._extract_files_from_diff(diff_content)
            additions = mr_details.get("additions", 0)
            deletions = mr_details.get("deletions", 0)
            
            # Generate test suggestions using AI
            suggestions = self.ai_suggester.suggest_tests(
                title=mr_details.get("title", ""),
                description="",  # Description not available in current view
                files=files,
                additions=additions,
                deletions=deletions,
                diff_content=diff_content,
                mr_context=mr_details
            )
            
            logger.info(f"Test suggestions generated for MR {mr_id}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate test suggestions for MR {mr_id}: {e}")
            return {
                "error": str(e),
                "fallback": True
            }
    
    def _get_mr_details(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Get MR details from BigQuery."""
        try:
            sql = """
            SELECT 
              mr_id,
              project_id,
              title,
              additions,
              deletions,
              state,
              created_at,
              updated_at
            FROM `mergemind.mr_activity_view`
            WHERE mr_id = @mr_id
            LIMIT 1
            """
            
            results = self.bq_client.query(sql, mr_id=mr_id)
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Failed to get MR details for {mr_id}: {e}")
            return None
    
    def _extract_files_from_diff(self, diff_content: str) -> list:
        """Extract file names from diff content."""
        try:
            files = []
            lines = diff_content.split('\n')
            
            for line in lines:
                if line.startswith('diff --git'):
                    # Extract file path from diff --git line
                    parts = line.split()
                    if len(parts) >= 4:
                        file_path = parts[3].replace('b/', '')
                        if file_path not in files:
                            files.append(file_path)
                elif line.startswith('+++') or line.startswith('---'):
                    # Extract file path from +++ or --- line
                    if '/' in line:
                        file_path = line.split('/')[-1].strip()
                        if file_path and file_path not in files:
                            files.append(file_path)
            
            return files[:20]  # Limit to first 20 files
            
        except Exception as e:
            logger.error(f"Failed to extract files from diff: {e}")
            return []
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get test suggestion statistics across all merge requests."""
        try:
            sql = """
            SELECT 
              COUNT(*) as total_mrs,
              COUNT(CASE WHEN state = 'opened' THEN 1 END) as open_mrs,
              COUNT(CASE WHEN state = 'merged' THEN 1 END) as merged_mrs,
              COUNT(CASE WHEN state = 'closed' THEN 1 END) as closed_mrs
            FROM `mergemind.mr_activity_view`
            """
            
            results = self.bq_client.query(sql)
            
            if results:
                stats = results[0]
                return {
                    "total_mrs": stats["total_mrs"],
                    "open_mrs": stats["open_mrs"],
                    "merged_mrs": stats["merged_mrs"],
                    "closed_mrs": stats["closed_mrs"],
                    "suggestion_coverage": "Available for MRs with diff content"
                }
            else:
                return {"error": "No statistics available"}
                
        except Exception as e:
            logger.error(f"Failed to get test statistics: {e}")
            return {"error": str(e)}


# Global instance
test_suggestion_service = TestSuggestionService()
