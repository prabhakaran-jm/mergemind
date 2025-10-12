"""
Reviewer suggestion service for merge requests.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.bigquery_client import bigquery_client
from services.user_service import user_service
from ai.reviewers.suggest import ReviewerSuggester

logger = logging.getLogger(__name__)


class ReviewerService:
    """Service for suggesting reviewers for merge requests."""
    
    def __init__(self):
        """Initialize reviewer service."""
        self.bq_client = bigquery_client
        self.user_service = user_service
        self.suggester = ReviewerSuggester(bigquery_client, user_service)
    
    def suggest_reviewers(self, mr_id: int) -> List[Dict[str, Any]]:
        """
        Suggest reviewers for a merge request.
        
        Args:
            mr_id: Merge request ID
            
        Returns:
            List of reviewer suggestions
        """
        try:
            # Get MR context
            mr_context = self._get_mr_context(mr_id)
            
            if not mr_context:
                logger.warning(f"No context found for MR {mr_id}")
                return []
            
            # Get suggestions
            suggestions = self.suggester.suggest(mr_context)
            
            logger.info(f"Suggested {len(suggestions)} reviewers for MR {mr_id}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest reviewers for MR {mr_id}: {e}")
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
              labels,
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
              notes_count_24h
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
