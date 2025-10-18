"""
AI-powered risk assessment for merge requests.
Analyzes code patterns, security issues, and complexity using Vertex AI.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.vertex_client import vertex_client

logger = logging.getLogger(__name__)


class AIRiskAssessor:
    """AI-powered risk assessment for merge requests."""
    
    def __init__(self):
        """Initialize AI risk assessor."""
        self.vertex_client = vertex_client
        logger.info("AI Risk Assessor initialized")
    
    def assess_risk(self, title: str, description: str, files: List[str], 
                   additions: int, deletions: int, diff_content: str,
                   mr_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform AI-powered risk assessment.
        
        Args:
            title: MR title
            description: MR description
            files: List of modified files
            additions: Number of lines added
            deletions: Number of lines deleted
            diff_content: Diff content
            mr_context: Additional MR context
            
        Returns:
            Dictionary with AI risk assessment
        """
        try:
            logger.info(f"Starting AI risk assessment for MR: {title}")
            
            # Generate AI risk analysis
            risk_analysis = self._analyze_code_patterns(
                title, description, files, additions, deletions, diff_content
            )
            
            # Analyze security risks
            security_risks = self._analyze_security_risks(
                files, diff_content, mr_context
            )
            
            # Analyze complexity risks
            complexity_risks = self._analyze_complexity_risks(
                files, additions, deletions, diff_content
            )
            
            # Combine assessments
            combined_assessment = self._combine_assessments(
                risk_analysis, security_risks, complexity_risks, mr_context
            )
            
            logger.info(f"AI risk assessment completed for MR: {title}")
            return combined_assessment
            
        except Exception as e:
            logger.error(f"AI risk assessment failed: {e}")
            return self._fallback_assessment(e)
    
    def _analyze_code_patterns(self, title: str, description: str, files: List[str],
                              additions: int, deletions: int, diff_content: str) -> Dict[str, Any]:
        """Analyze code patterns for risks."""
        try:
            prompt = f"""
Analyze the following merge request for code pattern risks:

Title: {title}
Description: {description}
Files: {', '.join(files[:10])}
Additions: {additions}, Deletions: {deletions}

Diff Content:
{diff_content[:2000]}

Please analyze for:
1. Code quality issues
2. Potential bugs or logic errors
3. Performance concerns
4. Maintainability issues
5. Architecture concerns

Return a JSON response with:
{{
    "code_quality_score": 0-100,
    "potential_bugs": ["list of potential bugs"],
    "performance_concerns": ["list of performance issues"],
    "maintainability_issues": ["list of maintainability problems"],
    "architecture_concerns": ["list of architectural issues"],
    "overall_pattern_risk": "Low/Medium/High"
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
                return self._parse_text_risk_response(response, "code_patterns")
                
        except Exception as e:
            logger.error(f"Code pattern analysis failed: {e}")
            return {"error": str(e), "overall_pattern_risk": "Unknown"}
    
    def _analyze_security_risks(self, files: List[str], diff_content: str,
                               mr_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze security risks."""
        try:
            prompt = f"""
Analyze the following code changes for security risks:

Files: {', '.join(files[:10])}

Diff Content:
{diff_content[:2000]}

Please analyze for:
1. SQL injection vulnerabilities
2. XSS vulnerabilities
3. Authentication/authorization issues
4. Input validation problems
5. Sensitive data exposure
6. Cryptographic issues
7. Access control problems

Return a JSON response with:
{{
    "security_score": 0-100,
    "vulnerabilities": ["list of security vulnerabilities"],
    "risk_factors": ["list of risk factors"],
    "recommendations": ["list of security recommendations"],
    "overall_security_risk": "Low/Medium/High"
}}
"""
            
            response = self.vertex_client.generate_text(
                prompt, max_tokens=1000, temperature=0.2
            )
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return self._parse_text_risk_response(response, "security")
                
        except Exception as e:
            logger.error(f"Security risk analysis failed: {e}")
            return {"error": str(e), "overall_security_risk": "Unknown"}
    
    def _analyze_complexity_risks(self, files: List[str], additions: int, deletions: int,
                                diff_content: str) -> Dict[str, Any]:
        """Analyze complexity risks."""
        try:
            prompt = f"""
Analyze the following code changes for complexity risks:

Files: {', '.join(files[:10])}
Additions: {additions}, Deletions: {deletions}

Diff Content:
{diff_content[:2000]}

Please analyze for:
1. Cyclomatic complexity
2. Code duplication
3. Large functions/methods
4. Deep nesting
5. Complex conditionals
6. Tight coupling
7. Code readability issues

Return a JSON response with:
{{
    "complexity_score": 0-100,
    "complexity_issues": ["list of complexity problems"],
    "readability_concerns": ["list of readability issues"],
    "maintenance_difficulty": "Low/Medium/High",
    "overall_complexity_risk": "Low/Medium/High"
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
                return self._parse_text_risk_response(response, "complexity")
                
        except Exception as e:
            logger.error(f"Complexity risk analysis failed: {e}")
            return {"error": str(e), "overall_complexity_risk": "Unknown"}
    
    def _combine_assessments(self, pattern_analysis: Dict[str, Any],
                           security_analysis: Dict[str, Any],
                           complexity_analysis: Dict[str, Any],
                           mr_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Combine all risk assessments into final result."""
        try:
            # Extract scores
            pattern_score = pattern_analysis.get("code_quality_score", 50)
            security_score = security_analysis.get("security_score", 50)
            complexity_score = complexity_analysis.get("complexity_score", 50)
            
            # Calculate weighted overall score
            weights = {
                "pattern": 0.3,
                "security": 0.4,
                "complexity": 0.3
            }
            
            overall_score = (
                pattern_score * weights["pattern"] +
                security_score * weights["security"] +
                complexity_score * weights["complexity"]
            )
            
            # Determine overall risk level
            if overall_score <= 30:
                overall_risk = "Low"
            elif overall_score <= 70:
                overall_risk = "Medium"
            else:
                overall_risk = "High"
            
            # Combine all findings
            all_issues = []
            all_issues.extend(pattern_analysis.get("potential_bugs", []))
            all_issues.extend(security_analysis.get("vulnerabilities", []))
            all_issues.extend(complexity_analysis.get("complexity_issues", []))
            
            all_recommendations = []
            all_recommendations.extend(pattern_analysis.get("recommendations", []))
            all_recommendations.extend(security_analysis.get("recommendations", []))
            all_recommendations.extend(complexity_analysis.get("recommendations", []))
            
            return {
                "overall_score": round(overall_score, 1),
                "overall_risk": overall_risk,
                "pattern_analysis": pattern_analysis,
                "security_analysis": security_analysis,
                "complexity_analysis": complexity_analysis,
                "all_issues": all_issues[:10],  # Limit to top 10
                "all_recommendations": all_recommendations[:10],  # Limit to top 10
                "assessment_timestamp": datetime.now().isoformat(),
                "mr_context": mr_context
            }
            
        except Exception as e:
            logger.error(f"Assessment combination failed: {e}")
            return self._fallback_assessment(e)
    
    def _parse_text_risk_response(self, text: str, analysis_type: str) -> Dict[str, Any]:
        """Parse text response into structured format."""
        try:
            # Simple text parsing for fallback
            lines = text.split('\n')
            issues = []
            recommendations = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    issues.append(line.lstrip('- *').strip())
                elif 'recommend' in line.lower() or 'suggest' in line.lower():
                    recommendations.append(line)
            
            return {
                f"{analysis_type}_score": 50,  # Default score
                f"overall_{analysis_type}_risk": "Medium",
                "issues": issues[:5],
                "recommendations": recommendations[:5]
            }
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return {"error": str(e), f"overall_{analysis_type}_risk": "Unknown"}
    
    def _fallback_assessment(self, error: Exception) -> Dict[str, Any]:
        """Provide fallback assessment when AI analysis fails."""
        return {
            "overall_score": 50.0,
            "overall_risk": "Medium",
            "error": str(error),
            "fallback": True,
            "assessment_timestamp": datetime.now().isoformat(),
            "message": "AI risk assessment unavailable, using fallback"
        }


# Global instance
ai_risk_assessor = AIRiskAssessor()
