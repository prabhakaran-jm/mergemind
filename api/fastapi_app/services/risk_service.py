"""
Risk scoring service for merge requests.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.bigquery_client import bigquery_client
from ai.scoring.rules import score, validate_features

logger = logging.getLogger(__name__)


class RiskService:
    """Service for calculating merge request risk scores."""
    
    def __init__(self):
        """Initialize risk service."""
        self.bq_client = bigquery_client
    
    def calculate_risk(self, mr_id: int) -> Dict[str, Any]:
        """
        Calculate risk score for a merge request.
        
        Args:
            mr_id: Merge request ID
            
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
            
            # Calculate risk score
            risk_result = score(features)
            
            logger.info(f"Risk calculated for MR {mr_id}: {risk_result['band']} ({risk_result['score']})")
            return risk_result
            
        except Exception as e:
            logger.error(f"Failed to calculate risk for MR {mr_id}: {e}")
            return {
                "score": 0,
                "band": "Low",
                "reasons": [f"Risk calculation failed: {str(e)}"]
            }
    
    def _get_risk_features(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Get risk features from BigQuery."""
        try:
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
                return results[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get risk features for MR {mr_id}: {e}")
            return None
    
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
