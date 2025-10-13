"""
AI-powered reviewer suggestion system.
Analyzes code changes, reviewer expertise, and workload to suggest optimal reviewers.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.vertex_client import vertex_client

logger = logging.getLogger(__name__)


class AIReviewerSuggester:
    """AI-powered reviewer suggestion system."""
    
    def __init__(self):
        """Initialize AI reviewer suggester."""
        self.vertex_client = vertex_client
        logger.info("AI Reviewer Suggester initialized")
    
    def suggest_reviewers(self, title: str, description: str, files: List[str], 
                         additions: int, deletions: int, diff_content: str,
                         mr_context: Optional[Dict[str, Any]] = None,
                         available_reviewers: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate AI-powered reviewer suggestions.
        
        Args:
            title: MR title
            description: MR description
            files: List of modified files
            additions: Number of lines added
            deletions: Number of lines deleted
            diff_content: Diff content
            mr_context: Additional MR context
            available_reviewers: List of available reviewers with their profiles
            
        Returns:
            Dictionary with AI reviewer suggestions
        """
        try:
            logger.info(f"Starting AI reviewer suggestions for MR: {title}")
            
            # Analyze code expertise requirements
            expertise_analysis = self._analyze_expertise_requirements(
                title, description, files, additions, deletions, diff_content
            )
            
            # Analyze reviewer workload and availability
            workload_analysis = self._analyze_reviewer_workload(
                available_reviewers, mr_context
            )
            
            # Generate AI-powered suggestions
            ai_suggestions = self._generate_ai_suggestions(
                expertise_analysis, workload_analysis, mr_context
            )
            
            # Combine and rank suggestions
            combined_suggestions = self._combine_reviewer_suggestions(
                ai_suggestions, available_reviewers, mr_context
            )
            
            logger.info(f"AI reviewer suggestions completed for MR: {title}")
            return combined_suggestions
            
        except Exception as e:
            logger.error(f"AI reviewer suggestions failed: {e}")
            return self._fallback_suggestions(e)
    
    def _analyze_expertise_requirements(self, title: str, description: str, files: List[str],
                                       additions: int, deletions: int, diff_content: str) -> Dict[str, Any]:
        """Analyze code changes to determine expertise requirements."""
        try:
            prompt = f"""
Analyze the following code changes to determine reviewer expertise requirements:

Title: {title}
Description: {description}
Files: {', '.join(files[:10])}
Additions: {additions}, Deletions: {deletions}

Diff Content:
{diff_content[:2000]}

Please analyze for:
1. Required technical expertise (programming languages, frameworks, tools)
2. Domain knowledge areas (e.g., authentication, database, API, frontend)
3. Code complexity level (simple, moderate, complex)
4. Security considerations
5. Performance implications
6. Testing requirements

Return a JSON response with:
{{
    "required_expertise": ["list of required technical skills"],
    "domain_areas": ["list of domain knowledge areas"],
    "complexity_level": "simple/moderate/complex",
    "security_considerations": ["list of security aspects"],
    "performance_impact": "low/medium/high",
    "testing_focus": ["list of testing areas"],
    "expertise_score": 0-100
}}
"""
            
            response = self.vertex_client.generate_text(
                prompt, max_tokens=1000, temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return self._parse_text_expertise_response(response)
                
        except Exception as e:
            logger.error(f"Expertise analysis failed: {e}")
            return {"error": str(e), "required_expertise": [], "complexity_level": "moderate"}
    
    def _analyze_reviewer_workload(self, available_reviewers: Optional[List[Dict[str, Any]]],
                                  mr_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze reviewer workload and availability."""
        try:
            if not available_reviewers:
                return {"error": "No reviewers available", "workload_analysis": {}}
            
            # Analyze workload patterns
            workload_data = []
            for reviewer in available_reviewers:
                workload_data.append({
                    "user_id": reviewer.get("user_id"),
                    "name": reviewer.get("name", f"User {reviewer.get('user_id')}"),
                    "current_load": reviewer.get("current_load", 0),
                    "expertise": reviewer.get("expertise", []),
                    "availability": reviewer.get("availability", "available")
                })
            
            prompt = f"""
Analyze the following reviewer workload and availability data:

Reviewers: {workload_data}

Please analyze for:
1. Optimal reviewer selection based on workload
2. Workload distribution recommendations
3. Availability considerations
4. Expertise matching opportunities
5. Fairness in reviewer assignment

Return a JSON response with:
{{
    "workload_analysis": {{
        "overloaded_reviewers": ["list of overloaded reviewer IDs"],
        "available_reviewers": ["list of available reviewer IDs"],
        "optimal_distribution": "workload distribution strategy",
        "fairness_score": 0-100
    }},
    "recommendations": ["list of workload recommendations"],
    "priority_reviewers": ["list of priority reviewer IDs"]
}}
"""
            
            response = self.vertex_client.generate_text(
                prompt, max_tokens=800, temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return self._parse_text_workload_response(response)
                
        except Exception as e:
            logger.error(f"Workload analysis failed: {e}")
            return {"error": str(e), "workload_analysis": {}}
    
    def _generate_ai_suggestions(self, expertise_analysis: Dict[str, Any],
                                workload_analysis: Dict[str, Any],
                                mr_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI-powered reviewer suggestions."""
        try:
            prompt = f"""
Based on the following analysis, generate optimal reviewer suggestions:

Expertise Requirements:
{expertise_analysis}

Workload Analysis:
{workload_analysis}

MR Context:
{mr_context}

Please generate reviewer suggestions considering:
1. Technical expertise match
2. Domain knowledge alignment
3. Current workload and availability
4. Code complexity requirements
5. Security and performance considerations
6. Fairness and diversity

Return a JSON response with:
{{
    "suggested_reviewers": [
        {{
            "user_id": "reviewer_id",
            "name": "reviewer_name",
            "match_score": 0-100,
            "reasoning": "why this reviewer is suggested",
            "expertise_match": ["matching expertise areas"],
            "workload_impact": "low/medium/high",
            "priority": "high/medium/low"
        }}
    ],
    "suggestion_strategy": "overall suggestion strategy",
    "confidence_score": 0-100
}}
"""
            
            response = self.vertex_client.generate_text(
                prompt, max_tokens=1200, temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return self._parse_text_suggestion_response(response)
                
        except Exception as e:
            logger.error(f"AI suggestion generation failed: {e}")
            return {"error": str(e), "suggested_reviewers": []}
    
    def _combine_reviewer_suggestions(self, ai_suggestions: Dict[str, Any],
                                     available_reviewers: Optional[List[Dict[str, Any]]],
                                     mr_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine AI suggestions with available reviewers."""
        try:
            # Extract AI suggestions
            ai_reviewers = ai_suggestions.get("suggested_reviewers", [])
            
            # If no AI suggestions, create fallback suggestions
            if not ai_reviewers and available_reviewers:
                ai_reviewers = self._create_fallback_suggestions(available_reviewers)
            
            # Rank and prioritize suggestions
            ranked_suggestions = self._rank_suggestions(ai_reviewers, mr_context)
            
            # Calculate summary statistics
            total_suggestions = len(ranked_suggestions)
            high_priority = len([r for r in ranked_suggestions if r.get("priority") == "high"])
            medium_priority = len([r for r in ranked_suggestions if r.get("priority") == "medium"])
            low_priority = len([r for r in ranked_suggestions if r.get("priority") == "low"])
            
            return {
                "suggestions": ranked_suggestions[:5],  # Limit to top 5
                "summary": {
                    "total_suggestions": total_suggestions,
                    "high_priority": high_priority,
                    "medium_priority": medium_priority,
                    "low_priority": low_priority
                },
                "ai_analysis": ai_suggestions,
                "suggestions_timestamp": datetime.now().isoformat(),
                "mr_context": mr_context
            }
            
        except Exception as e:
            logger.error(f"Suggestion combination failed: {e}")
            return self._fallback_suggestions(e)
    
    def _create_fallback_suggestions(self, available_reviewers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create fallback suggestions when AI analysis fails."""
        suggestions = []
        
        for i, reviewer in enumerate(available_reviewers[:3]):
            suggestion = {
                "user_id": reviewer.get("user_id"),
                "name": reviewer.get("name", f"User {reviewer.get('user_id')}"),
                "match_score": 50,  # Default score
                "reasoning": "Fallback suggestion based on availability",
                "expertise_match": reviewer.get("expertise", []),
                "workload_impact": "medium",
                "priority": "medium"
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def _rank_suggestions(self, suggestions: List[Dict[str, Any]], 
                         mr_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank suggestions by priority and match score."""
        try:
            # Sort by priority and match score
            priority_order = {"high": 3, "medium": 2, "low": 1}
            
            def sort_key(suggestion):
                priority_score = priority_order.get(suggestion.get("priority", "low"), 1)
                match_score = suggestion.get("match_score", 0)
                return (priority_score, match_score)
            
            suggestions.sort(key=sort_key, reverse=True)
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggestion ranking failed: {e}")
            return suggestions
    
    def _parse_text_expertise_response(self, text: str) -> Dict[str, Any]:
        """Parse text response into structured format."""
        try:
            lines = text.split('\n')
            expertise = []
            domains = []
            
            for line in lines:
                line = line.strip()
                if 'expertise' in line.lower() or 'skill' in line.lower():
                    expertise.append(line)
                elif 'domain' in line.lower() or 'area' in line.lower():
                    domains.append(line)
            
            return {
                "required_expertise": expertise[:5],
                "domain_areas": domains[:5],
                "complexity_level": "moderate",
                "expertise_score": 50,
                "parsed_from_text": True
            }
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return {"error": str(e), "required_expertise": [], "complexity_level": "moderate"}
    
    def _parse_text_workload_response(self, text: str) -> Dict[str, Any]:
        """Parse text response into structured format."""
        try:
            lines = text.split('\n')
            recommendations = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    recommendations.append(line.lstrip('- *').strip())
            
            return {
                "workload_analysis": {
                    "overloaded_reviewers": [],
                    "available_reviewers": [],
                    "optimal_distribution": "balanced",
                    "fairness_score": 50
                },
                "recommendations": recommendations[:5],
                "priority_reviewers": [],
                "parsed_from_text": True
            }
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return {"error": str(e), "workload_analysis": {}}
    
    def _parse_text_suggestion_response(self, text: str) -> Dict[str, Any]:
        """Parse text response into structured format."""
        try:
            lines = text.split('\n')
            suggestions = []
            
            current_suggestion = {}
            for line in lines:
                line = line.strip()
                if line.startswith('Reviewer:'):
                    if current_suggestion:
                        suggestions.append(current_suggestion)
                    current_suggestion = {"name": line.replace('Reviewer:', '').strip()}
                elif line.startswith('Reason:'):
                    current_suggestion["reasoning"] = line.replace('Reason:', '').strip()
                elif line.startswith('Score:'):
                    current_suggestion["match_score"] = int(line.replace('Score:', '').strip())
            
            if current_suggestion:
                suggestions.append(current_suggestion)
            
            return {
                "suggested_reviewers": suggestions[:5],
                "suggestion_strategy": "text-based analysis",
                "confidence_score": 50,
                "parsed_from_text": True
            }
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return {"error": str(e), "suggested_reviewers": []}
    
    def _fallback_suggestions(self, error: Exception) -> Dict[str, Any]:
        """Provide fallback suggestions when AI analysis fails."""
        return {
            "suggestions": [],
            "summary": {
                "total_suggestions": 0,
                "high_priority": 0,
                "medium_priority": 0,
                "low_priority": 0
            },
            "error": str(error),
            "fallback": True,
            "suggestions_timestamp": datetime.now().isoformat(),
            "message": "AI reviewer suggestions unavailable, using fallback"
        }


# Global instance
ai_reviewer_suggester = AIReviewerSuggester()
