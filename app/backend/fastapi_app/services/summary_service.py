"""
Summary service for merge request diffs.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.bigquery_client import bigquery_client
from services.gitlab_client import gitlab_client
from services.user_service import user_service
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from ai.summarizer.summarize import diff_summarizer

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for generating merge request summaries."""
    
    def __init__(self):
        """Initialize summary service."""
        self.bq_client = bigquery_client
        self.gitlab_client = gitlab_client
        self.summarizer = diff_summarizer
        self.user_service = user_service
    
    async def generate_summary(self, mr_id: int) -> Dict[str, Any]:
        """
        Generate summary for a merge request.
        
        Args:
            mr_id: Merge request ID
            
        Returns:
            Dictionary with summary, risks, and tests
        """
        try:
            # Get MR data from BigQuery
            mr_data = self._get_mr_data(mr_id)
            
            if not mr_data:
                logger.warning(f"No MR data found for {mr_id}")
                return {
                    "summary": ["No merge request data available"],
                    "risks": ["Unable to assess risks without MR data"],
                    "tests": ["Unable to suggest tests without MR data"]
                }
            
            # Extract GitLab IID from web_url
            web_url = mr_data.get("web_url", "")
            logger.info(f"Attempting to extract IID from web_url: {web_url}")
            gitlab_iid = self._extract_gitlab_iid(web_url)
            if not gitlab_iid:
                logger.warning(f"Could not extract GitLab IID from web_url for MR {mr_id}")
                return {
                    "summary": ["No diff content available for analysis"],
                    "risks": ["Unable to assess risks without diff content"],
                    "tests": ["Unable to suggest tests without diff content"]
                }
            
            # Get diff from GitLab using the correct IID
            diff_content = await self.gitlab_client.get_merge_request_diff(
                project_id=mr_data["project_id"],
                mr_id=gitlab_iid
            )
            
            if not diff_content:
                logger.warning(f"No diff content found for MR {mr_id}")
                return {
                    "summary": ["No diff content available for analysis"],
                    "risks": ["Unable to assess risks without diff content"],
                    "tests": ["Unable to suggest tests without diff content"]
                }
            
            # Generate summary
            summary_result = self.summarizer.summarize_diff(
                mr_id=mr_id,
                title=mr_data.get("title", ""),
                description=mr_data.get("description", ""),
                files=self._extract_files_from_diff(diff_content),
                additions=mr_data.get("additions", 0),
                deletions=mr_data.get("deletions", 0),
                diff_snippets=diff_content,
                sha=mr_data.get("sha")
            )
            
            logger.info(f"Generated summary for MR {mr_id}")
            return summary_result
            
        except Exception as e:
            logger.error(f"Failed to generate summary for MR {mr_id}: {e}")
            return {
                "summary": [f"Summary generation failed: {str(e)}"],
                "risks": ["Unable to assess risks due to processing error"],
                "tests": ["Unable to suggest tests due to processing error"]
            }
    
    def _get_mr_data(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Get MR data from BigQuery."""
        try:
            sql = f"""
            SELECT 
              raw.id as mr_id,
              raw.project_id,
              raw.title,
              raw.author_id,
              raw.created_at,
              raw.state,
              raw.additions,
              raw.deletions,
              COALESCE(raw.last_pipeline_status, 'unknown') as last_pipeline_status,
              COALESCE(raw.last_pipeline_age_min, 0) as last_pipeline_age_min,
              raw.notes_count_24_h,
              raw.approvals_left,
              raw.web_url
            FROM `{self.bq_client.project_id}.{self.bq_client.dataset_raw}.merge_requests` raw
            LEFT JOIN `{self.bq_client.project_id}.{self.bq_client.dataset_modeled}.merge_risk_features` risk
              ON raw.id = risk.mr_id
            WHERE raw.id = @mr_id
            LIMIT 1
            """
            
            results = self.bq_client.query(sql, mr_id=mr_id)
            
            if results:
                return results[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get MR data for {mr_id}: {e}")
            return None
    
    def _extract_files_from_diff(self, diff_content: str) -> list:
        """Extract file paths from diff content."""
        try:
            files = []
            lines = diff_content.split('\n')
            
            for line in lines:
                if line.startswith('--- ') or line.startswith('+++ '):
                    file_path = line[4:].strip()
                    if file_path and file_path not in files:
                        files.append(file_path)
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to extract files from diff: {e}")
            return []
    
    def get_cached_summary(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Get cached summary if available."""
        return self.summarizer.get_cached_summary(mr_id)
    
    def invalidate_summary_cache(self, mr_id: int):
        """Invalidate cached summary."""
        self.summarizer.invalidate_cache(mr_id)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary service statistics."""
        return self.summarizer.get_cache_stats()
    
    async def get_mr_context(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive MR context.
        
        Args:
            mr_id: Merge request ID
            
        Returns:
            Dictionary with MR context
        """
        try:
            # Get MR data
            mr_data = self._get_mr_data(mr_id)
            
            if not mr_data:
                return None
            
            # Get additional context from GitLab
            gitlab_mr = await self.gitlab_client.get_merge_request(
                project_id=mr_data["project_id"],
                mr_id=mr_id
            )
            
            # Get author name
            author_name = self.user_service.get_user_name(mr_data["author_id"])
            
            # Combine data
            context = {
                "mr_id": mr_id,
                "project_id": mr_data["project_id"],
                "title": mr_data["title"],
                "author_id": mr_data["author_id"],
                "author_name": author_name,
                "state": mr_data["state"],
                "created_at": mr_data["created_at"],
                "additions": mr_data["additions"],
                "deletions": mr_data["deletions"],
                "web_url": mr_data.get("web_url", ""),
                "last_pipeline_status": mr_data["last_pipeline_status"],
                "last_pipeline_age_min": mr_data["last_pipeline_age_min"],
                "notes_count_24_h": mr_data["notes_count_24_h"],
                "approvals_left": mr_data["approvals_left"]
            }
            
            # Add GitLab-specific data if available
            if gitlab_mr:
                context.update({
                    "description": gitlab_mr.get("description", ""),
                    "labels": [label["name"] for label in gitlab_mr.get("labels", [])],
                    "sha": gitlab_mr.get("sha"),
                    "web_url": gitlab_mr.get("web_url"),
                    "source_branch": gitlab_mr.get("source_branch"),
                    "target_branch": gitlab_mr.get("target_branch")
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get MR context for {mr_id}: {e}")
            return None
    
    def _extract_gitlab_iid(self, web_url: str) -> Optional[int]:
        """Extract GitLab IID from web URL."""
        try:
            if not web_url:
                return None
            
            # Extract the IID from URLs like:
            # https://35.202.37.189.sslip.io/root/mergemind-integration-service/-/merge_requests/5
            import re
            match = re.search(r'/merge_requests/(\d+)', web_url)
            if match:
                return int(match.group(1))
            
            return None
        except Exception as e:
            logger.error(f"Failed to extract GitLab IID from URL {web_url}: {e}")
            return None


# Global instance
summary_service = SummaryService()
