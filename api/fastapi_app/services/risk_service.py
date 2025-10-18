"""
Risk scoring service for merge requests.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.bigquery_client import bigquery_client
from services.gitlab_client import gitlab_client
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from ai.scoring.rules import score, validate_features
from ai.scoring.ai_risk_assessor import ai_risk_assessor

logger = logging.getLogger(__name__)


class RiskService:
    """Service for calculating merge request risk scores."""
    
    def __init__(self):
        """Initialize risk service."""
        self.bq_client = bigquery_client
        self.gitlab_client = gitlab_client
        self.ai_assessor = ai_risk_assessor
    
    async def calculate_risk(self, mr_id: int, use_ai: bool = True) -> Dict[str, Any]:
        """
        Calculate risk score for a merge request.
        
        Args:
            mr_id: Merge request ID
            use_ai: Whether to use AI-powered risk assessment
            
        Returns:
            Dictionary with risk score, band, and reasons
        """
        try:
            # Get risk features from BigQuery
            features = self._get_risk_features(mr_id)
            
            if not features:
                logger.warning(f"No risk features found for MR {mr_id}")
                return {
                    "score": 0,
                    "band": "Low",
                    "reasons": ["No risk features available"]
                }
            
            # Validate features
            if not validate_features(features):
                logger.warning(f"Invalid risk features for MR {mr_id}")
                return {
                    "score": 0,
                    "band": "Low",
                    "reasons": ["Invalid risk features"]
                }
            
            # Calculate traditional risk score
            traditional_result = score(features)
            
            # Add AI-powered risk assessment if requested
            ai_result = None
            if use_ai:
                try:
                    ai_result = await self._calculate_ai_risk(mr_id, features)
                except Exception as e:
                    logger.warning(f"AI risk assessment failed for MR {mr_id}: {e}")
                    ai_result = None
            
            # Combine results
            result = {
                "traditional": traditional_result,
                "ai": ai_result,
                "combined_score": traditional_result["score"],
                "combined_band": traditional_result["band"],
                "reasons": traditional_result["reasons"]
            }
            
            # If AI assessment is available, use it to enhance the result
            if ai_result and not ai_result.get("fallback", False):
                result["ai_enhanced"] = True
                result["ai_insights"] = ai_result.get("all_issues", [])
                result["ai_recommendations"] = ai_result.get("all_recommendations", [])
                
                # Adjust score based on AI assessment
                ai_score = ai_result.get("overall_score", 50)
                traditional_score = traditional_result["score"]
                
                # Weighted combination: 70% traditional, 30% AI
                combined_score = (traditional_score * 0.7) + (ai_score * 0.3)
                result["combined_score"] = round(combined_score, 1)
                
                # Determine combined band
                if combined_score <= 39:
                    result["combined_band"] = "Low"
                elif combined_score <= 69:
                    result["combined_band"] = "Medium"
                else:
                    result["combined_band"] = "High"
            
            logger.info(f"Risk calculated for MR {mr_id}: {result['combined_band']} ({result['combined_score']})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate risk for MR {mr_id}: {e}")
            return {
                "score": 0,
                "band": "Low",
                "reasons": [f"Risk calculation failed: {str(e)}"]
            }
    
    def _get_risk_features(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Get risk features from raw BigQuery data."""
        try:
            # Get risk features from transformed table
            sql = """
            SELECT 
              mr_id,
              project_id,
              age_hours,
              notes_count_24h,
              last_pipeline_status_is_fail,
              approvals_left,
              change_size_bucket,
              author_recent_fail_rate_7d,
              repo_merge_conflict_rate_14d,
              work_in_progress,
              labels_sensitive
            FROM `mergemind.merge_risk_features`
            WHERE mr_id = @mr_id
            LIMIT 1
            """
            
            results = self.bq_client.query(sql, mr_id=mr_id)
            
            if results:
                # Return the risk features directly from the transformed table
                return results[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get risk features for MR {mr_id}: {e}")
            return None
    
    async def _calculate_ai_risk(self, mr_id: int, features: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate AI-powered risk assessment."""
        try:
            # Get MR details from BigQuery
            mr_details = self._get_mr_details(mr_id)
            if not mr_details:
                logger.warning(f"No MR details found for AI assessment: {mr_id}")
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
            
            # Perform AI risk assessment
            ai_result = self.ai_assessor.assess_risk(
                title=mr_details.get("title", ""),
                description="",  # Description not available in current view
                files=files,
                additions=additions,
                deletions=deletions,
                diff_content=diff_content,
                mr_context=features
            )
            
            return ai_result
            
        except Exception as e:
            logger.error(f"AI risk calculation failed for MR {mr_id}: {e}")
            return {"fallback": True, "error": str(e)}
    
    def _get_mr_details(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Get MR details from BigQuery."""
        try:
            sql = """
            SELECT 
              id as mr_id,
              project_id,
              title,
              additions,
              deletions,
              state,
              created_at,
              updated_at
            FROM `mergemind_raw.merge_requests`
            WHERE id = @mr_id
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
    
    def get_risk_features(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Get raw risk features for debugging."""
        return self._get_risk_features(mr_id)
    
    def update_risk_score(self, mr_id: int, score: int, band: str) -> bool:
        """
        Update risk score in the database.
        
        Args:
            mr_id: Merge request ID
            score: Risk score
            band: Risk band
            
        Returns:
            True if successful, False otherwise
        """
        try:
            sql = """
            UPDATE `mergemind.merge_risk_features`
            SET 
              risk_score_rule = @score,
              risk_label = @band,
              updated_at = CURRENT_TIMESTAMP()
            WHERE mr_id = @mr_id
            """
            
            self.bq_client.query(sql, mr_id=mr_id, score=score, band=band)
            
            logger.info(f"Updated risk score for MR {mr_id}: {band} ({score})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update risk score for MR {mr_id}: {e}")
            return False
    
    def get_risk_statistics(self) -> Dict[str, Any]:
        """Get risk statistics across all merge requests."""
        try:
            sql = """
            SELECT 
              risk_label,
              COUNT(*) as count,
              AVG(risk_score_rule) as avg_score,
              MIN(risk_score_rule) as min_score,
              MAX(risk_score_rule) as max_score
            FROM `mergemind.merge_risk_features`
            GROUP BY risk_label
            ORDER BY avg_score DESC
            """
            
            results = self.bq_client.query(sql)
            
            stats = {
                "by_band": {},
                "total": 0
            }
            
            for row in results:
                band = row["risk_label"]
                stats["by_band"][band] = {
                    "count": row["count"],
                    "avg_score": round(row["avg_score"], 2),
                    "min_score": row["min_score"],
                    "max_score": row["max_score"]
                }
                stats["total"] += row["count"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get risk statistics: {e}")
            return {"by_band": {}, "total": 0}


# Global instance
risk_service = RiskService()
