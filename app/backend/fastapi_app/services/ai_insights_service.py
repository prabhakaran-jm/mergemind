"""
AI Insights Service for MergeMind

This service generates comprehensive AI insights by combining data from the mergemind dataset
with Gemini AI analysis. It provides enhanced insights beyond basic summaries.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date, timezone
import json
import re

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
        self.dataset_modeled = bigquery_client.dataset_modeled
        self.dataset_raw = bigquery_client.dataset_raw
        
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
                    "timestamp": datetime.now(timezone.utc).isoformat(),
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
            
            # 3-6. Generate all AI components in parallel for faster response
            import asyncio
            
            # Run all AI generation tasks in parallel
            ai_insights_task = self._generate_ai_insights(mr_data)
            trends_task = self._generate_trend_analysis(mr_data)
            predictions_task = self._generate_predictive_insights(mr_data)
            
            # Wait for all tasks to complete
            ai_insights, trends, predictions = await asyncio.gather(
                ai_insights_task,
                trends_task, 
                predictions_task,
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(ai_insights, Exception):
                logger.error(f"AI insights generation failed: {ai_insights}")
                ai_insights = [{"type": "error", "title": "Error", "description": "Failed to generate insights", "confidence": 0.0, "priority": "low"}]
            
            if isinstance(trends, Exception):
                logger.error(f"Trends generation failed: {trends}")
                trends = {"error": f"Trend analysis failed: {str(trends)}"}
            
            if isinstance(predictions, Exception):
                logger.error(f"Predictions generation failed: {predictions}")
                predictions = {"error": f"Predictive insights failed: {str(predictions)}"}
            
            # Generate recommendations after AI insights are ready
            recommendations = await self._generate_recommendations(mr_data, ai_insights)
            
            return {
                "mr_id": mr_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ai_insights": ai_insights,
                "recommendations": recommendations,
                "trends": trends,
                "predictions": predictions,
                "data_freshness": self._json_serializer(mr_data.get("data_freshness")),
                "confidence_score": self._calculate_confidence_score(mr_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive insights for MR {mr_id}: {e}")
            return {"error": f"Failed to generate insights: {str(e)}"}
    
    async def _gather_mr_data(self, mr_id: int) -> Optional[Dict[str, Any]]:
        """Gather all relevant data for a merge request from mergemind dataset."""
        try:
            # Get basic MR data using JOIN between raw and modeled tables
            basic_query = f"""
            SELECT 
                raw.id as mr_id,
                raw.project_id,
                raw.title,
                raw.author_id,
                raw.state,
                COALESCE(raw.last_pipeline_status, 'unknown') as last_pipeline_status,
                COALESCE(raw.last_pipeline_age_min, 0) as last_pipeline_age_min,
                raw.notes_count_24_h,
                raw.approvals_left,
                raw.additions,
                raw.deletions,
                TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), raw.created_at, HOUR) as age_hours,
                raw.source_branch,
                raw.target_branch,
                raw.web_url,
                raw.assignee_id,
                raw.created_at,
                raw.updated_at,
                raw.merged_at,
                raw.closed_at,
                raw.work_in_progress,
                raw.labels,
                risk.risk_score_rule,
                risk.risk_label,
                risk.change_size_bucket,
                CURRENT_TIMESTAMP() as data_freshness
            FROM `{self.project_id}.{self.dataset_raw}.merge_requests` raw
            LEFT JOIN `{self.project_id}.{self.dataset_modeled}.merge_risk_features` risk
              ON raw.id = risk.mr_id
            WHERE raw.id = @mr_id
            """
            
            results = self.bq_client.query(basic_query, mr_id=mr_id)
            
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
                prompt += f"\n\nCode Changes (Diff):\n{mr_data['diff_content'][:2000]}  # Limit to first 2000 chars to avoid token limits\n"
            
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
            
            # Use higher token limit to prevent truncation of comprehensive insights
            response = self.vertex_client.generate_text(prompt, max_tokens=2500, temperature=0.7)

            # Parse and structure the response
            insights = self._parse_gemini_response(response)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate AI insights: {e}")
            return {"error": f"AI insights generation failed: {str(e)}"}
    
    async def _generate_recommendations(self, mr_data: Dict[str, Any], ai_insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on MR data and AI insights."""
        try:
            recommendations = []

            logger.info(f"Generating recommendations with MR data keys: {list(mr_data.keys())}")
            logger.info(f"MR data values - risk_label: {mr_data.get('risk_label')}, pipeline: {mr_data.get('last_pipeline_status')}, age_hours: {mr_data.get('age_hours')}, change_size: {mr_data.get('change_size_bucket')}")
            logger.info(f"AI insights type: {type(ai_insights)}, count: {len(ai_insights) if isinstance(ai_insights, list) else 'N/A'}")

            # Rule-based recommendations
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
            
            if mr_data.get("age_hours", 0) > 72:
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
            
            if mr_data.get("change_size_bucket", "") in ["L", "XL"]:
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
            # Only skip AI recommendations if ai_insights is a dict (error case) or empty
            if ai_insights and not isinstance(ai_insights, dict):
                # Process AI insights even if some have error type - just filter them out
                valid_insights = [i for i in ai_insights if i.get("type") != "error"]
                if valid_insights:
                    ai_recommendations = self._extract_ai_recommendations(valid_insights)
                    recommendations.extend(ai_recommendations)
                    logger.info(f"Added {len(ai_recommendations)} AI-enhanced recommendations")

            logger.info(f"Total recommendations generated: {len(recommendations)}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    async def _generate_trend_analysis(self, mr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend analysis for the project and author."""
        try:
            project_id = mr_data.get("project_id")
            author_id = mr_data.get("author_id")
            
            trend_query = f"""
            WITH project_trends AS (
                SELECT 
                    'project' as scope,
                    DATE(c.created_at) as date,
                    COUNT(*) as mr_count,
                    AVG(c.cycle_time_hours) as avg_cycle_time,
                    AVG(f.risk_score_rule) as avg_risk_score
                FROM `{self.project_id}.{self.dataset_modeled}.cycle_time_view` c
                JOIN `{self.project_id}.{self.dataset_modeled}.merge_risk_features` f ON c.mr_id = f.mr_id
                WHERE c.project_id = {project_id}
                AND DATE(c.created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY DATE(c.created_at)
            ),
            author_trends AS (
                SELECT 
                    'author' as scope,
                    DATE(c.created_at) as date,
                    COUNT(*) as mr_count,
                    AVG(c.cycle_time_hours) as avg_cycle_time,
                    AVG(f.risk_score_rule) as avg_risk_score
                FROM `{self.project_id}.{self.dataset_modeled}.cycle_time_view` c
                JOIN `{self.project_id}.{self.dataset_modeled}.mr_activity_view` a ON c.mr_id = a.mr_id
                JOIN `{self.project_id}.{self.dataset_modeled}.merge_risk_features` f ON c.mr_id = f.mr_id
                WHERE a.author_id = {author_id}
                AND DATE(c.created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY DATE(c.created_at)
            )
            SELECT 'project' as scope, ARRAY_AGG(STRUCT(date, mr_count, avg_cycle_time, avg_risk_score)) as trends FROM project_trends
            UNION ALL
            SELECT 'author' as scope, ARRAY_AGG(STRUCT(date, mr_count, avg_cycle_time, avg_risk_score)) as trends FROM author_trends
            """
            
            results = self.bq_client.query(trend_query)
            
            trends = {
                "project": {"trends": []},
                "author": {"trends": []}
            }

            if results:
                for row in results:
                    # BigQuery client returns dictionaries, not row objects
                    scope = row.get('scope') if isinstance(row, dict) else row.scope
                    trends_data = row.get('trends') if isinstance(row, dict) else row.trends

                    if scope and trends_data:
                        trends[scope] = {"trends": [self._json_serializer(trend) for trend in trends_data]}
            
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
            
            # Use higher token limit to prevent truncation of predictive insights
            response = self.vertex_client.generate_text(prompt, max_tokens=2500, temperature=0.7)

            # Return predictions in the format expected by UI
            return {
                "raw_response": response,
                "structured": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
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
    
    def _parse_gemini_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Gemini response into structured format."""
        try:
            # Try to extract JSON from markdown code blocks
            json_str = None
            if '```json' in response:
                match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
                if match:
                    json_str = match.group(1)
            elif response.strip().startswith('{'):
                json_str = response.strip()

            if json_str:
                try:
                    # Attempt to parse the extracted JSON string
                    parsed = json.loads(json_str)
                    return self._structure_ai_insights(parsed)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {e}. Trying to fix.")
                    # Try to fix common JSON errors (e.g., unescaped quotes)
                    fixed_json_str = re.sub(r'(?<!\\)"', r'\\"', json_str)
                    try:
                        parsed = json.loads(fixed_json_str)
                        return self._structure_ai_insights(parsed)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON even after fixing quotes.")
                        return self._extract_insights_from_text(json_str)

            # If not JSON, structure the text response
            return [{
                "type": "general",
                "title": "AI Analysis",
                "description": response[:500] + "..." if len(response) > 500 else response,
                "confidence": 0.6,
                "priority": "low"
            }]
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return [{
                "type": "general",
                "title": "AI Analysis",
                "description": "AI analysis completed but parsing failed.",
                "confidence": 0.5,
                "priority": "low"
            }]
    
    def _structure_ai_insights(self, parsed_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert parsed AI response into UI-expected format."""
        insights = []
        
        try:
            # Extract code quality insights
            if "code_quality_assessment" in parsed_response:
                cqa = parsed_response["code_quality_assessment"]
                
                if cqa.get("architecture"):
                    insights.append({
                        "type": "architecture",
                        "title": "Architecture Assessment",
                        "description": cqa["architecture"],
                        "confidence": 0.8,
                        "priority": "medium"
                    })
                
                if cqa.get("patterns_and_best_practices"):
                    insights.append({
                        "type": "patterns",
                        "title": "Patterns & Best Practices",
                        "description": cqa["patterns_and_best_practices"],
                        "confidence": 0.7,
                        "priority": "medium"
                    })
            
            # Extract risk analysis insights
            if "risk_analysis" in parsed_response:
                ra = parsed_response["risk_analysis"]
                
                if ra.get("security"):
                    insights.append({
                        "type": "security",
                        "title": "Security Assessment",
                        "description": ra["security"],
                        "confidence": 0.9,
                        "priority": "high"
                    })
                
                if ra.get("performance"):
                    insights.append({
                        "type": "performance",
                        "title": "Performance Impact",
                        "description": ra["performance"],
                        "confidence": 0.6,
                        "priority": "medium"
                    })
                
                if ra.get("maintainability"):
                    insights.append({
                        "type": "maintainability",
                        "title": "Maintainability",
                        "description": ra["maintainability"],
                        "confidence": 0.7,
                        "priority": "medium"
                    })
            
            # Extract technical debt indicators
            if "technical_debt_indicators" in parsed_response:
                for indicator in parsed_response["technical_debt_indicators"]:
                    priority = "low"
                    if indicator.get("severity", "").lower() in ["high", "medium"]:
                        priority = indicator["severity"].lower()
                    
                    insights.append({
                        "type": "technical_debt",
                        "title": indicator.get("indicator", "Technical Debt"),
                        "description": indicator.get("details", ""),
                        "confidence": 0.8,
                        "priority": priority
                    })
            
            # Extract performance implications
            if "performance_implications" in parsed_response:
                pi = parsed_response["performance_implications"]
                if pi.get("assessment"):
                    insights.append({
                        "type": "performance",
                        "title": "Performance Analysis",
                        "description": pi["assessment"],
                        "confidence": 0.7,
                        "priority": "medium"
                    })
            
            # Extract security considerations
            if "security_considerations" in parsed_response:
                sc = parsed_response["security_considerations"]
                if sc.get("assessment"):
                    insights.append({
                        "type": "security",
                        "title": "Security Considerations",
                        "description": sc["assessment"],
                        "confidence": 0.9,
                        "priority": "high"
                    })
            
        except Exception as e:
            logger.error(f"Failed to structure AI insights: {e}")
            # Return a fallback insight
            insights.append({
                "type": "general",
                "title": "AI Analysis",
                "description": "AI analysis completed but parsing failed. Raw response available.",
                "confidence": 0.5,
                "priority": "low"
            })
        
        return insights
    
    def _extract_insights_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract insights from text when JSON parsing fails."""
        insights = []
        
        try:
            # Extract insights based on text patterns
            if "security" in text.lower() and ("high" in text.lower() or "critical" in text.lower()):
                insights.append({
                    "type": "security",
                    "title": "Security Assessment",
                    "description": "Security concerns identified in the analysis.",
                    "confidence": 0.9,
                    "priority": "high"
                })
            
            if "performance" in text.lower() and ("slow" in text.lower() or "bottleneck" in text.lower()):
                insights.append({
                    "type": "performance",
                    "title": "Performance Impact",
                    "description": "Performance concerns identified in the analysis.",
                    "confidence": 0.7,
                    "priority": "medium"
                })
            
            if "architecture" in text.lower() and ("insufficient" in text.lower() or "unknown" in text.lower()):
                insights.append({
                    "type": "architecture",
                    "title": "Architecture Assessment",
                    "description": "Architecture analysis indicates insufficient information for proper assessment.",
                    "confidence": 0.6,
                    "priority": "medium"
                })
            
            if "technical_debt" in text.lower() or "debt" in text.lower():
                insights.append({
                    "type": "technical_debt",
                    "title": "Technical Debt",
                    "description": "Technical debt indicators identified in the analysis.",
                    "confidence": 0.8,
                    "priority": "medium"
                })
            
            # If no specific insights found, create a general one
            if not insights:
                insights.append({
                    "type": "general",
                    "title": "AI Analysis",
                    "description": text[:500] + "..." if len(text) > 500 else text,
                    "confidence": 0.7,
                    "priority": "medium"
                })
            
        except Exception as e:
            logger.error(f"Failed to extract insights from text: {e}")
            insights.append({
                "type": "general",
                "title": "AI Analysis",
                "description": "AI analysis completed but parsing failed.",
                "confidence": 0.5,
                "priority": "low"
            })
        
        return insights
    
    def _extract_ai_recommendations(self, ai_insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract actionable recommendations from AI insights."""
        recommendations = []
        
        try:
            logger.info(f"Processing {len(ai_insights)} AI insights for recommendations")
            for insight in ai_insights:
                insight_type = insight.get("type")
                priority = insight.get("priority")

                if insight_type == "security" and priority == "high":
                    recommendations.append({
                        "type": "security_review",
                        "priority": "high",
                        "title": "High-Priority Security Review Required",
                        "description": insight.get("description", "High-priority security concerns identified. Immediate review recommended."),
                        "actions": [
                            "Request security team review",
                            "Conduct vulnerability scanning",
                            "Review data handling practices and access controls"
                        ]
                    })
                
                elif insight_type in ["technical_debt", "maintainability"] and priority in ["high", "medium"]:
                    recommendations.append({
                        "type": "technical_debt",
                        "priority": priority,
                        "title": "Address Technical Debt",
                        "description": insight.get("description", "Technical debt identified that should be addressed to improve maintainability."),
                        "actions": [
                            "Refactor affected code to align with best practices",
                            "Add comprehensive unit and integration tests",
                            "Update documentation to reflect changes"
                        ]
                    })
                
                elif insight_type == "performance" and priority in ["high", "medium"]:
                    recommendations.append({
                        "type": "performance_optimization",
                        "priority": priority,
                        "title": "Performance Optimization Recommended",
                        "description": insight.get("description", "Performance concerns identified. Optimization is recommended to improve response times."),
                        "actions": [
                            "Profile the code to identify bottlenecks",
                            "Optimize algorithms and database queries",
                            "Implement caching for frequently accessed data"
                        ]
                    })
                
                elif insight_type in ["architecture", "patterns"] and priority in ["high", "medium"]:
                    recommendations.append({
                        "type": "architecture_review",
                        "priority": priority,
                        "title": "Architecture and Design Pattern Review",
                        "description": insight.get("description", "Architecture or design pattern concerns identified. A review is recommended to ensure scalability and maintainability."),
                        "actions": [
                            "Schedule a review with the architecture team",
                            "Evaluate alternative design patterns",
                            "Validate the scalability and long-term impact of the current design"
                        ]
                    })

                elif insight_type == "general":
                    # Handle general insights - create recommendations based on priority
                    if priority == "high":
                        recommendations.append({
                            "type": "urgent_review",
                            "priority": "high",
                            "title": "Urgent Review Required",
                            "description": insight.get("description", "AI analysis identified important concerns that require immediate attention."),
                            "actions": [
                                "Review the AI analysis findings carefully",
                                "Address any critical issues identified",
                                "Consult with team leads if needed"
                            ]
                        })
                    elif priority == "medium":
                        recommendations.append({
                            "type": "standard_review",
                            "priority": "medium",
                            "title": "Standard Review Recommended",
                            "description": insight.get("description", "AI analysis completed. A standard review is recommended to validate findings."),
                            "actions": [
                                "Review the merge request thoroughly",
                                "Verify code quality and adherence to standards",
                                "Check for potential improvements"
                            ]
                        })
                    else:  # low priority
                        recommendations.append({
                            "type": "general_review",
                            "priority": "low",
                            "title": "General Code Review",
                            "description": insight.get("description", "AI analysis completed. Consider a general code review to ensure quality."),
                            "actions": [
                                "Review code for correctness and best practices",
                                "Check for potential bugs or edge cases",
                                "Verify that functionality works as expected"
                            ]
                        })

        except Exception as e:
            logger.error(f"Failed to extract AI recommendations: {e}")
            recommendations.append({
                "type": "general_review",
                "priority": "low",
                "title": "Code Review Required",
                "description": "AI analysis encountered an error. A standard code review is recommended.",
                "actions": [
                    "Review code for correctness and best practices",
                    "Check for potential bugs or edge cases",
                    "Verify that functionality works as expected"
                ]
            })
        
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
                        data_freshness = datetime.fromisoformat(data_freshness.replace('Z', '+00:00'))
                    
                    if data_freshness.tzinfo is None:
                        data_freshness = data_freshness.replace(tzinfo=timezone.utc)

                    freshness_hours = (datetime.now(timezone.utc) - data_freshness).total_seconds() / 3600
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
            match = re.search(r'/merge_requests/(\\d+)', web_url)
            if match:
                return int(match.group(1))
            
            return None
        except Exception as e:
            logger.error(f"Failed to extract GitLab IID from URL {web_url}: {e}")
            return None
    
    def _json_serializer(self, obj):
        """Custom JSON serializer to handle datetime, date and other non-serializable objects."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            # Recursively serialize nested dictionaries
            return {k: self._json_serializer(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            # Recursively serialize nested lists/tuples
            return [self._json_serializer(item) for item in obj]
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        if isinstance(obj, bigquery.Row):
            return dict(obj)
        try:
            return str(obj)
        except (TypeError, ValueError):
            return None


# Create service instance
ai_insights_service = AIInsightsService()