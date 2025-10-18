"""
Reviewer suggestion service for merge requests.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.bigquery_client import bigquery_client
from services.user_service import user_service
from services.gitlab_client import gitlab_client
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from ai.reviewers.suggest import ReviewerSuggester
from ai.reviewers.ai_reviewer_suggester import ai_reviewer_suggester

logger = logging.getLogger(__name__)


class ReviewerService:
    """Service for suggesting reviewers for merge requests."""
    
    def __init__(self):
        """Initialize reviewer service."""
        self.bq_client = bigquery_client
        self.user_service = user_service
        self.gitlab_client = gitlab_client
        self.suggester = ReviewerSuggester(bigquery_client, user_service)
        self.ai_suggester = ai_reviewer_suggester
    
    async def suggest_reviewers(self, mr_id: int, use_ai: bool = True) -> Dict[str, Any]:
        """
        Suggest reviewers for a merge request.
        
        Args:
            mr_id: Merge request ID
            use_ai: Whether to use AI-powered suggestions
            
        Returns:
            Dictionary with reviewer suggestions
        """
        try:
            # Get MR context
            mr_context = self._get_mr_context(mr_id)
            
            if not mr_context:
                logger.warning(f"No context found for MR {mr_id}")
                return {
                    "suggestions": [],
                    "error": "No MR context available",
                    "fallback": True
                }
            
            # Get traditional suggestions
            traditional_suggestions = self.suggester.suggest(mr_context)
            
            # Get AI-powered suggestions if requested
            ai_suggestions = None
            if use_ai:
                try:
                    ai_suggestions = await self._get_ai_suggestions(mr_id, mr_context)
                except Exception as e:
                    logger.warning(f"AI reviewer suggestions failed for MR {mr_id}: {e}")
                    ai_suggestions = None
            
            # Combine results
            result = {
                "traditional": traditional_suggestions,
                "ai": ai_suggestions,
                "suggestions": traditional_suggestions,
                "ai_enhanced": False
            }
            
            # If AI suggestions are available, use them to enhance the result
            if ai_suggestions and not ai_suggestions.get("fallback", False):
                result["ai_enhanced"] = True
                result["ai_suggestions"] = ai_suggestions.get("suggestions", [])
                result["ai_analysis"] = ai_suggestions.get("ai_analysis", {})
                
                # Combine traditional and AI suggestions
                combined_suggestions = traditional_suggestions + ai_suggestions.get("suggestions", [])
                result["suggestions"] = combined_suggestions[:5]  # Limit to top 5
            
            logger.info(f"Suggested {len(result['suggestions'])} reviewers for MR {mr_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to suggest reviewers for MR {mr_id}: {e}")
            return {
                "suggestions": [],
                "error": str(e),
                "fallback": True
            }
    
    async def _get_ai_suggestions(self, mr_id: int, mr_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered reviewer suggestions."""
        try:
            # Get MR details from BigQuery
            mr_details = self._get_mr_details(mr_id)
            if not mr_details:
                logger.warning(f"No MR details found for AI suggestions: {mr_id}")
                return {"fallback": True, "error": "No MR details available"}
            
            # Get diff content from GitLab
            project_id = mr_details.get("project_id")
            if not project_id:
                logger.warning(f"No project ID found for MR {mr_id}")
                return {"fallback": True, "error": "No project ID available"}
            
            try:
                diff_content = await self.gitlab_client.get_merge_request_diff(project_id, mr_id)
                if not diff_content:
                    logger.warning(f"No diff content available for MR {mr_id}")
                    return {"fallback": True, "error": "No diff content available"}
            except Exception as e:
                logger.warning(f"Failed to get diff content for MR {mr_id}: {e}")
                return {"fallback": True, "error": f"Failed to get diff content: {str(e)}"}
            
            # Extract file information from diff
            files = self._extract_files_from_diff(diff_content)
            additions = mr_details.get("additions", 0)
            deletions = mr_details.get("deletions", 0)
            
            # Get available reviewers (stub for now)
            available_reviewers = self._get_available_reviewers(mr_context)
            
            # Generate AI suggestions
            ai_result = self.ai_suggester.suggest_reviewers(
                title=mr_details.get("title", ""),
                description="",  # Description not available in current view
                files=files,
                additions=additions,
                deletions=deletions,
                diff_content=diff_content,
                mr_context=mr_context,
                available_reviewers=available_reviewers
            )
            
            return ai_result
            
        except Exception as e:
            logger.error(f"AI reviewer suggestions failed for MR {mr_id}: {e}")
            return {"fallback": True, "error": str(e)}
    
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
            FROM `ai-accelerate-mergemind.mergemind.mr_activity_view`
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
    
    def _get_available_reviewers(self, mr_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available reviewers (stub implementation)."""
        try:
            # Get co-reviewers as available reviewers
            author_id = mr_context.get("author_id")
            if not author_id:
                return []
            
            co_reviewers = self.get_co_reviewers(author_id, limit=10)
            
            # Convert to available reviewers format
            available_reviewers = []
            for reviewer in co_reviewers:
                available_reviewers.append({
                    "user_id": reviewer["reviewer_id"],
                    "name": self.user_service.get_user_name(reviewer["reviewer_id"]),
                    "current_load": 0,  # Stub value
                    "expertise": [],  # Stub value
                    "availability": "available",
                    "interaction_count": reviewer["interaction_count"],
                    "approval_count": reviewer["approval_count"]
                })
            
            return available_reviewers
            
        except Exception as e:
            logger.error(f"Failed to get available reviewers: {e}")
            return []
    
    def _get_mr_context(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Get MR context for reviewer suggestion."""
        try:
            sql = """
            SELECT 
              mr_id,
              project_id,
              author_id,
              title,
              state,
              created_at,
              additions,
              deletions
            FROM `mergemind.mr_activity_view`
            WHERE mr_id = @mr_id
            LIMIT 1
            """
            
            results = self.bq_client.query(sql, mr_id=mr_id)
            
            if results:
                return results[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get MR context for {mr_id}: {e}")
            return None
    
    def get_reviewer_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get reviewer history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of results
            
        Returns:
            List of review history entries
        """
        try:
            sql = """
            SELECT 
              mr_id,
              project_id,
              title,
              author_id,
              created_at,
              state,
              approvals_left,
              notes_count_24_h
            FROM `mergemind.mr_activity_view`
            WHERE mr_id IN (
              SELECT DISTINCT mr_id 
              FROM `mergemind_raw.mr_notes` 
              WHERE author_id = @user_id
              ORDER BY created_at DESC
              LIMIT @limit
            )
            ORDER BY created_at DESC
            LIMIT @limit
            """
            
            results = self.bq_client.query(sql, user_id=user_id, limit=limit)
            return results
            
        except Exception as e:
            logger.error(f"Failed to get reviewer history for user {user_id}: {e}")
            return []
    
    def get_reviewer_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get reviewer statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with reviewer statistics
        """
        try:
            sql = """
            SELECT 
              COUNT(*) as total_reviews,
              COUNTIF(note_type = 'approval') as approvals,
              COUNTIF(note_type = 'review') as reviews,
              COUNTIF(note_type = 'comment') as comments,
              COUNTIF(created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)) as recent_reviews
            FROM `mergemind_raw.mr_notes`
            WHERE author_id = @user_id
            """
            
            results = self.bq_client.query(sql, user_id=user_id)
            
            if results:
                return results[0]
            else:
                return {
                    "total_reviews": 0,
                    "approvals": 0,
                    "reviews": 0,
                    "comments": 0,
                    "recent_reviews": 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get reviewer stats for user {user_id}: {e}")
            return {
                "total_reviews": 0,
                "approvals": 0,
                "reviews": 0,
                "comments": 0,
                "recent_reviews": 0
            }
    
    def get_co_reviewers(self, author_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get co-reviewers for an author.
        
        Args:
            author_id: Author user ID
            limit: Maximum number of results
            
        Returns:
            List of co-reviewer entries
        """
        try:
            sql = """
            SELECT 
              reviewer_id,
              interaction_count,
              approval_count,
              review_count,
              final_weight,
              rank_by_weight
            FROM `mergemind.co_review_graph`
            WHERE author_id = @author_id
            ORDER BY final_weight DESC
            LIMIT @limit
            """
            
            results = self.bq_client.query(sql, author_id=author_id, limit=limit)
            return results
            
        except Exception as e:
            logger.error(f"Failed to get co-reviewers for author {author_id}: {e}")
            return []


# Global instance
reviewer_service = ReviewerService()
