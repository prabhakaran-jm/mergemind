"""
Diff summarization service using Vertex AI.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from services.vertex_client import vertex_client
from ai.summarizer.cache import SummaryCache

logger = logging.getLogger(__name__)


class DiffSummarizer:
    """Service for summarizing merge request diffs."""
    
    def __init__(self):
        """Initialize summarizer with cache."""
        self.cache = SummaryCache()
        self.vertex_client = vertex_client
    
    def summarize_diff(self, mr_id: int, title: str, description: str, 
                     files: list, additions: int, deletions: int, 
                     diff_snippets: str, sha: str = None) -> Dict[str, Any]:
        """
        Summarize a merge request diff.
        
        Args:
            mr_id: Merge request ID
            title: MR title
            description: MR description
            files: List of modified files
            additions: Number of lines added
            deletions: Number of lines deleted
            diff_snippets: Diff content
            sha: Git commit SHA (for caching)
            
        Returns:
            Dictionary with summary, risks, and tests
        """
        try:
            # Create cache key
            cache_key = f"{mr_id}_{sha}" if sha else str(mr_id)
            
            # Check cache first
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached summary for MR {mr_id}")
                return cached_result
            
            # Generate new summary
            logger.info(f"Generating new summary for MR {mr_id}")
            result = self.vertex_client.summarize_diff(
                title=title,
                description=description,
                files=files,
                additions=additions,
                deletions=deletions,
                diff_snippets=diff_snippets
            )
            
            # Cache the result
            self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to summarize diff for MR {mr_id}: {e}")
            return {
                "summary": [f"Summarization failed: {str(e)}"],
                "risks": ["Unable to assess risks due to processing error"],
                "tests": ["Unable to suggest tests due to processing error"]
            }
    
    def get_cached_summary(self, mr_id: int, sha: str = None) -> Optional[Dict[str, Any]]:
        """Get cached summary if available."""
        cache_key = f"{mr_id}_{sha}" if sha else str(mr_id)
        return self.cache.get(cache_key)
    
    def invalidate_cache(self, mr_id: int, sha: str = None):
        """Invalidate cached summary."""
        cache_key = f"{mr_id}_{sha}" if sha else str(mr_id)
        self.cache.delete(cache_key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


# Global instance
diff_summarizer = DiffSummarizer()
