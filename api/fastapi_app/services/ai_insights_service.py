"""
AI Insights Service for MergeMind

This service generates comprehensive AI insights by combining data from the mergemind dataset
with Gemini AI analysis. It provides enhanced insights beyond basic summaries.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from google.cloud import bigquery
from .vertex_client import vertex_client
from .bigquery_client import bigquery_client

logger = logging.getLogger(__name__)


class AIInsightsService:
    """Service for generating AI-powered insights from transformed data."""
    
    def __init__(self):
        self.bq_client = bigquery_client
        self.vertex_client = vertex_client
        self.project_id = bigquery_client.project_id
        
    async def generate_comprehensive_insights(self, mr_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive AI insights for a merge request.
        
        Args:
            mr_id: Merge request ID
            
        Returns:
            Dictionary containing comprehensive AI insights
        """
        try:
            logger.info(f"Generating comprehensive AI insights for MR {mr_id}")
            
            # 1. Gather all relevant data from mergemind dataset
            mr_data = await self._gather_mr_data(mr_id)
            if not mr_data:
                # Return fallback insights if no data found
                return {
                    "mr_id": mr_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "ai_insights": {
                        "summary": f"AI analysis for merge request {mr_id}",
                        "risk_assessment": "Unable to assess risk - limited data available",
                        "code_quality": "Unable to assess code quality - no diff content available",
                        "technical_debt": "Unable to assess technical debt - insufficient data"
                    },
                    "recommendations": [
                        {
                            "type": "data",
                            "priority": "medium",
                            "title": "Data Collection Needed",
                            "description": "This merge request needs more data to provide comprehensive AI insights",
                            "action": "Ensure the merge request has been processed by the data pipeline"
                        }
                    ],
                    "trends": {
                        "message": "Trend analysis requires historical data"
                    },
                    "predictions": {
                        "message": "Predictive analysis requires more data points"
                    },
                    "confidence_score": 0.1,
                    "data_source": "fallback"
                }
            
            # 2. Get diff content from GitLab for comprehensive analysis
            diff_content = await self._get_diff_content(mr_data)
            if diff_content:
                mr_data["diff_content"] = diff_content
                mr_data["has_diff_content"] = True
            else:
                mr_data["has_diff_content"] = False
                logger.warning(f"No diff content available for MR {mr_id}")
            
            # 3. Generate AI insights using Gemini
            ai_insights = await self._generate_ai_insights(mr_data)
            
            # 4. Generate recommendations
            recommendations = await self._generate_recommendations(mr_data, ai_insights)
            
            # 5. Generate trend analysis
            trends = await self._generate_trend_analysis(mr_data)
            
            # 6. Generate predictive insights
            predictions = await self._generate_predictive_insights(mr_data)
            
            return {
                "mr_id": mr_id,
                "timestamp": datetime.utcnow().isoformat(),
                "ai_insights": ai_insights,
                "recommendations": recommendations,
                "trends": trends,
                "predictions": predictions,
                "data_freshness": mr_data.get("data_freshness").isoformat() if mr_data.get("data_freshness") and hasattr(mr_data.get("data_freshness"), 'isoformat') else str(mr_data.get("data_freshness", "")),
                "confidence_score": self._calculate_confidence_score(mr_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive insights for MR {mr_id}: {e}")
            return {"error": f"Failed to generate insights: {str(e)}"}
    
    async def _gather_mr_data(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Gather all relevant data for a merge request from mergemind dataset."""
        try:
            # First try to get basic MR data from mr_activity_view
            basic_query = f"""
            SELECT 
                mr_id,
                project_id,
                title,
                author_id,
                state,
                last_pipeline_status,
                last_pipeline_age_min,
                notes_count_24_h,
                approvals_left,
                additions,
                deletions,
                age_hours,
                source_branch,
                target_branch,
                web_url,
                assignee_id,
                created_at,
                updated_at,
                merged_at,
                closed_at,
                work_in_progress,
                labels,
                CURRENT_TIMESTAMP() as data_freshness
            FROM `{self.project_id}.mergemind.mr_activity_view`
            WHERE mr_id = {mr_id}
            """
            
            results = self.bq_client.query(basic_query)
            
            if results:
                mr_data = results[0]
                
                # Add default values for missing fields
                mr_data.update({
                    'change_size_bucket': 'unknown',
                    'work_in_progress': False,
                    'labels_sensitive': False,
                    'risk_score_rule': 0,
                    'risk_label': 'Unknown',
                    'cycle_time_hours': None,
                    'co_reviewers': []
                })
                
                logger.info(f"Successfully gathered MR data for {mr_id}")
                return mr_data
                
            # If no data found, return None
            logger.warning(f"No data found for MR {mr_id} in mr_activity_view")
            return None
            
        except Exception as e:
            logger.error(f"Failed to gather MR data for {mr_id}: {e}")
            return None
    
    async def _generate_ai_insights(self, mr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI insights using Gemini based on MR data."""
        try:
            # Prepare context for Gemini
            context = self._prepare_gemini_context(mr_data)
            
            # Generate insights using Gemini
            prompt = f"""
            As an AI code review expert, analyze this merge request data and provide comprehensive insights:
            
            {json.dumps(context, indent=2, default=self._json_serializer)}
            """
            
            # Add diff content if available
            if mr_data.get("has_diff_content") and mr_data.get("diff_content"):
                prompt += f"""
            
            Code Changes (Diff):
            {mr_data["diff_content"][:2000]}  # Limit to first 2000 chars to avoid token limits
            """
            
            prompt += """
            
            Please provide:
            1. Code Quality Assessment (architecture, patterns, best practices)
            2. Risk Analysis (security, performance, maintainability)
            3. Review Priority (urgency, complexity, impact)
            4. Technical Debt Indicators
            5. Performance Implications
            6. Security Considerations
            
            Format your response as structured JSON with clear categories and actionable insights.
            """
            
            response = self.vertex_client.generate_text(prompt)
            
            # Parse and structure the response
            insights = self._parse_gemini_response(response)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate AI insights: {e}")
            return {"error": f"AI insights generation failed: {str(e)}"}
    
    async def _generate_recommendations(self, mr_data: Dict[str, Any], ai_insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on MR data and AI insights."""
        try:
            recommendations = []
            
            # Risk-based recommendations
            if mr_data.get("risk_label") == "High":
                recommendations.append({
                    "type": "risk_mitigation",
                    "priority": "high",
                    "title": "High Risk Merge Request",
                    "description": "This MR has high risk indicators. Consider additional review and testing.",
                    "actions": [
                        "Request review from senior developers",
                        "Add comprehensive tests",
                        "Consider breaking into smaller changes"
                    ]
                })
            
            # Pipeline-based recommendations
            if mr_data.get("last_pipeline_status") == "failed":
                recommendations.append({
                    "type": "pipeline_fix",
                    "priority": "high",
                    "title": "Pipeline Failure",
                    "description": "The pipeline is failing. Address issues before merging.",
                    "actions": [
                        "Check pipeline logs",
                        "Fix failing tests",
                        "Verify build configuration"
                    ]
                })
            
            # Age-based recommendations
            age_hours = mr_data.get("age_hours", 0)
            if age_hours > 72:  # 3 days
                recommendations.append({
                    "type": "stale_mr",
                    "priority": "medium",
                    "title": "Stale Merge Request",
                    "description": "This MR has been open for more than 3 days.",
                    "actions": [
                        "Check if still relevant",
                        "Update with latest changes",
                        "Consider closing if abandoned"
                    ]
                })
            
            # Size-based recommendations
            change_size = mr_data.get("change_size_bucket", "")
            if change_size in ["L", "XL"]:
                recommendations.append({
                    "type": "large_change",
                    "priority": "medium",
                    "title": "Large Change Detected",
                    "description": "This is a large change that may be difficult to review.",
                    "actions": [
                        "Consider breaking into smaller PRs",
                        "Schedule dedicated review time",
                        "Add detailed documentation"
                    ]
                })
            
            # AI-enhanced recommendations
            if ai_insights and not ai_insights.get("error"):
                ai_recommendations = self._extract_ai_recommendations(ai_insights)
                recommendations.extend(ai_recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    async def _generate_trend_analysis(self, mr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend analysis for the project and author."""
        try:
            project_id = mr_data.get("project_id")
            author_id = mr_data.get("author_id")
            
            # Get historical data for trend analysis
            trend_query = f"""
            WITH project_trends AS (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as mr_count,
                    AVG(cycle_time_hours) as avg_cycle_time,
                    AVG(risk_score_rule) as avg_risk_score
                FROM `{self.project_id}.mergemind.cycle_time_view`
                WHERE project_id = {project_id}
                AND DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ),
            author_trends AS (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as mr_count,
                    AVG(cycle_time_hours) as avg_cycle_time,
                    AVG(risk_score_rule) as avg_risk_score
                FROM `{self.project_id}.mergemind.cycle_time_view` c
                JOIN `{self.project_id}.mergemind.mr_activity_view` a ON c.mr_id = a.mr_id
                WHERE a.author_id = {author_id}
                AND DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            )
            SELECT 
                'project' as scope,
                ARRAY_AGG(STRUCT(date, mr_count, avg_cycle_time, avg_risk_score)) as trends
            FROM project_trends
            UNION ALL
            SELECT 
                'author' as scope,
                ARRAY_AGG(STRUCT(date, mr_count, avg_cycle_time, avg_risk_score)) as trends
            FROM author_trends
            """
            
            query_job = self.bq_client.query(trend_query)
            results = query_job.result()
            
            trends = {}
            for row in results:
                trends[row.scope] = row.trends
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to generate trend analysis: {e}")
            return {"error": f"Trend analysis failed: {str(e)}"}
    
    async def _generate_predictive_insights(self, mr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictive insights using historical data patterns."""
        try:
            # Use Gemini to analyze patterns and make predictions
            context = self._prepare_gemini_context(mr_data)
            
            prompt = f"""
            Based on this merge request data and historical patterns, provide predictive insights:
            
            {json.dumps(context, indent=2, default=self._json_serializer)}
            
            Predict:
            1. Estimated time to merge (based on similar MRs)
            2. Likelihood of requiring additional changes
            3. Potential bottlenecks or blockers
            4. Recommended review timeline
            5. Risk of introducing bugs
            
            Provide confidence levels for each prediction.
            """
            
            response = self.vertex_client.generate_text(prompt)
            predictions = self._parse_gemini_response(response)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to generate predictive insights: {e}")
            return {"error": f"Predictive insights failed: {str(e)}"}
    
    def _prepare_gemini_context(self, mr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare structured context for Gemini analysis."""
        return {
            "merge_request": {
                "id": mr_data.get("mr_id"),
                "title": mr_data.get("title"),
                "state": mr_data.get("state"),
                "age_hours": mr_data.get("age_hours"),
                "change_size": mr_data.get("change_size_bucket"),
                "additions": mr_data.get("additions"),
                "deletions": mr_data.get("deletions"),
                "work_in_progress": mr_data.get("work_in_progress"),
                "labels_sensitive": mr_data.get("labels_sensitive")
            },
            "risk_assessment": {
                "score": mr_data.get("risk_score_rule"),
                "label": mr_data.get("risk_label"),
                "pipeline_status": mr_data.get("last_pipeline_status"),
                "pipeline_age_min": mr_data.get("last_pipeline_age_min"),
                "approvals_left": mr_data.get("approvals_left"),
                "notes_count_24_h": mr_data.get("notes_count_24_h")
            },
            "historical_context": {
                "cycle_time_hours": mr_data.get("cycle_time_hours"),
                "co_reviewers": mr_data.get("co_reviewers", [])[:5]  # Top 5 reviewers
            }
        }
    
    def _parse_gemini_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response into structured format."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # If not JSON, structure the text response
            return {
                "raw_response": response,
                "structured": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except json.JSONDecodeError:
            return {
                "raw_response": response,
                "structured": False,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _extract_ai_recommendations(self, ai_insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract actionable recommendations from AI insights."""
        recommendations = []
        
        # This would parse the AI insights and extract specific recommendations
        # For now, return empty list as this depends on the AI response format
        return recommendations
    
    def _calculate_confidence_score(self, mr_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the insights based on data completeness."""
        try:
            required_fields = [
                "mr_id", "title", "state", "age_hours", "risk_score_rule",
                "additions", "deletions", "last_pipeline_status"
            ]
            
            available_fields = sum(1 for field in required_fields if mr_data.get(field) is not None)
            completeness = available_fields / len(required_fields)
            
            # Adjust based on data freshness
            data_freshness = mr_data.get("data_freshness")
            if data_freshness:
                try:
                    # Handle both datetime objects and ISO strings
                    if isinstance(data_freshness, str):
                        from datetime import datetime
                        data_freshness = datetime.fromisoformat(data_freshness.replace('Z', '+00:00'))
                    
                    freshness_hours = (datetime.utcnow() - data_freshness).total_seconds() / 3600
                    freshness_factor = max(0.5, 1.0 - (freshness_hours / 24))  # Decay over 24 hours
                    completeness *= freshness_factor
                except Exception as e:
                    logger.warning(f"Failed to process data freshness: {e}")
            
            return round(completeness, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence score: {e}")
            return 0.5  # Default moderate confidence
    
    async def _get_diff_content(self, mr_data: Dict[str, Any]) -> Optional[str]:
        """Get diff content from GitLab for comprehensive analysis."""
        try:
            # Extract GitLab IID from web_url
            gitlab_iid = self._extract_gitlab_iid(mr_data.get("web_url", ""))
            if not gitlab_iid:
                logger.warning(f"Could not extract GitLab IID from web_url")
                return None
            
            # Get diff from GitLab using the correct IID
            diff_content = await self.gitlab_client.get_merge_request_diff(
                project_id=mr_data["project_id"],
                mr_id=gitlab_iid
            )
            
            return diff_content
            
        except Exception as e:
            logger.error(f"Failed to get diff content: {e}")
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
    
    def _json_serializer(self, obj):
        """Custom JSON serializer to handle datetime objects."""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)


# Create service instance
ai_insights_service = AIInsightsService()
