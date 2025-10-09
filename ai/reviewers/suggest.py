"""
Reviewer suggestion system based on co-review graph.
"""

from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReviewerCandidate:
    """Reviewer candidate with score and reasoning."""
    user_id: int
    name: str
    score: float
    reason: str


class ReviewerSuggester:
    """Suggests reviewers based on co-review graph and availability."""
    
    def __init__(self, bigquery_client):
        """Initialize with BigQuery client."""
        self.bq_client = bigquery_client
        
    def suggest(self, mr_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest reviewers for a merge request.
        
        Args:
            mr_context: Dictionary containing MR context including author, labels, activity, etc.
            
        Returns:
            List of up to 3 reviewer suggestions with reasons
        """
        try:
            author_id = mr_context.get("author_id")
            if not author_id:
                logger.warning("No author_id in MR context")
                return []
            
            # Get co-review graph data
            co_reviewers = self._get_co_reviewers(author_id)
            
            # Filter by availability (stub for now)
            available_reviewers = self._filter_by_availability(co_reviewers)
            
            # Get top 3 suggestions
            suggestions = self._rank_and_select(available_reviewers, mr_context)
            
            logger.info(f"Suggested {len(suggestions)} reviewers for MR by author {author_id}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting reviewers: {e}")
            return []
    
    def _get_co_reviewers(self, author_id: int) -> List[Dict[str, Any]]:
        """Get co-reviewers from the graph."""
        try:
            # Query the co-review graph
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
            LIMIT 10
            """
            
            results = self.bq_client.query(sql, author_id=author_id)
            
            # Convert to list of dictionaries
            co_reviewers = []
            for row in results:
                co_reviewers.append({
                    "user_id": row["reviewer_id"],
                    "interaction_count": row["interaction_count"],
                    "approval_count": row["approval_count"],
                    "review_count": row["review_count"],
                    "final_weight": row["final_weight"],
                    "rank": row["rank_by_weight"]
                })
            
            return co_reviewers
            
        except Exception as e:
            logger.error(f"Error getting co-reviewers: {e}")
            return []
    
    def _filter_by_availability(self, reviewers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter reviewers by availability (stub implementation)."""
        # TODO: Implement actual availability checking
        # For now, return all reviewers
        return reviewers
    
    def _rank_and_select(self, reviewers: List[Dict[str, Any]], mr_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank and select top reviewers."""
        suggestions = []
        
        for i, reviewer in enumerate(reviewers[:3]):  # Top 3
            # Get user name (stub for now)
            user_name = self._get_user_name(reviewer["user_id"])
            
            # Generate reason
            reason = self._generate_reason(reviewer, mr_context)
            
            suggestion = {
                "user_id": reviewer["user_id"],
                "name": user_name,
                "score": reviewer["final_weight"],
                "reason": reason
            }
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def _get_user_name(self, user_id: int) -> str:
        """Get user name by ID (stub implementation)."""
        # TODO: Query users table or GitLab API
        return f"User {user_id}"
    
    def _generate_reason(self, reviewer: Dict[str, Any], mr_context: Dict[str, Any]) -> str:
        """Generate human-readable reason for suggestion."""
        interaction_count = reviewer["interaction_count"]
        approval_count = reviewer["approval_count"]
        review_count = reviewer["review_count"]
        
        if approval_count > 0:
            return f"Has approved {approval_count} of your MRs, {interaction_count} total interactions"
        elif review_count > 0:
            return f"Has reviewed {review_count} of your MRs, {interaction_count} total interactions"
        else:
            return f"Has {interaction_count} interactions on your MRs"
    
    def get_reviewer_load(self, user_id: int) -> int:
        """Get current reviewer load (stub implementation)."""
        # TODO: Implement actual load calculation
        # For now, return stub value
        return 0


def suggest_reviewers(bigquery_client, mr_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convenience function to suggest reviewers.
    
    Args:
        bigquery_client: BigQuery client instance
        mr_context: MR context dictionary
        
    Returns:
        List of reviewer suggestions
    """
    suggester = ReviewerSuggester(bigquery_client)
    return suggester.suggest(mr_context)
