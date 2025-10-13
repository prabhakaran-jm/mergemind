"""
AI-powered test suggestions for merge requests.
Analyzes code changes and suggests unit tests, integration tests, and edge cases.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.vertex_client import vertex_client

logger = logging.getLogger(__name__)


class AITestSuggester:
    """AI-powered test suggestion system for merge requests."""
    
    def __init__(self):
        """Initialize AI test suggester."""
        self.vertex_client = vertex_client
        logger.info("AI Test Suggester initialized")
    
    def suggest_tests(self, title: str, description: str, files: List[str], 
                     additions: int, deletions: int, diff_content: str,
                     mr_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate AI-powered test suggestions.
        
        Args:
            title: MR title
            description: MR description
            files: List of modified files
            additions: Number of lines added
            deletions: Number of lines deleted
            diff_content: Diff content
            mr_context: Additional MR context
            
        Returns:
            Dictionary with test suggestions
        """
        try:
            logger.info(f"Starting AI test suggestions for MR: {title}")
            
            # Generate unit test suggestions
            unit_tests = self._suggest_unit_tests(
                title, description, files, additions, deletions, diff_content
            )
            
            # Generate integration test suggestions
            integration_tests = self._suggest_integration_tests(
                title, description, files, additions, deletions, diff_content
            )
            
            # Generate edge case suggestions
            edge_cases = self._suggest_edge_cases(
                title, description, files, additions, deletions, diff_content
            )
            
            # Generate performance test suggestions
            performance_tests = self._suggest_performance_tests(
                title, description, files, additions, deletions, diff_content
            )
            
            # Combine all suggestions
            combined_suggestions = self._combine_test_suggestions(
                unit_tests, integration_tests, edge_cases, performance_tests, mr_context
            )
            
            logger.info(f"AI test suggestions completed for MR: {title}")
            return combined_suggestions
            
        except Exception as e:
            logger.error(f"AI test suggestions failed: {e}")
            return self._fallback_suggestions(e)
    
    def _suggest_unit_tests(self, title: str, description: str, files: List[str],
                           additions: int, deletions: int, diff_content: str) -> Dict[str, Any]:
        """Suggest unit tests based on code changes."""
        try:
            prompt = f"""
Analyze the following code changes and suggest unit tests:

Title: {title}
Description: {description}
Files: {', '.join(files[:10])}
Additions: {additions}, Deletions: {deletions}

Diff Content:
{diff_content[:2000]}

Please suggest unit tests for:
1. New functions/methods
2. Modified functions/methods
3. Edge cases and boundary conditions
4. Error handling scenarios
5. Input validation

Return a JSON response with:
{{
    "unit_tests": [
        {{
            "test_name": "test_name",
            "description": "test description",
            "test_type": "unit",
            "priority": "high/medium/low",
            "suggested_code": "pytest test code snippet",
            "file_to_test": "target_file.py",
            "function_to_test": "function_name"
        }}
    ],
    "coverage_areas": ["list of areas that need test coverage"],
    "testing_strategy": "overall testing approach"
}}
"""
            
            response = self.vertex_client.generate_text(
                prompt, max_tokens=1500, temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return self._parse_text_test_response(response, "unit_tests")
                
        except Exception as e:
            logger.error(f"Unit test suggestions failed: {e}")
            return {"error": str(e), "unit_tests": []}
    
    def _suggest_integration_tests(self, title: str, description: str, files: List[str],
                                  additions: int, deletions: int, diff_content: str) -> Dict[str, Any]:
        """Suggest integration tests based on code changes."""
        try:
            prompt = f"""
Analyze the following code changes and suggest integration tests:

Title: {title}
Description: {description}
Files: {', '.join(files[:10])}
Additions: {additions}, Deletions: {deletions}

Diff Content:
{diff_content[:2000]}

Please suggest integration tests for:
1. API endpoints
2. Database interactions
3. External service integrations
4. Component interactions
5. End-to-end workflows

Return a JSON response with:
{{
    "integration_tests": [
        {{
            "test_name": "test_name",
            "description": "test description",
            "test_type": "integration",
            "priority": "high/medium/low",
            "suggested_code": "pytest test code snippet",
            "components": ["list of components being tested"],
            "dependencies": ["list of external dependencies"]
        }}
    ],
    "integration_points": ["list of integration points to test"],
    "testing_approach": "integration testing strategy"
}}
"""
            
            response = self.vertex_client.generate_text(
                prompt, max_tokens=1500, temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return self._parse_text_test_response(response, "integration_tests")
                
        except Exception as e:
            logger.error(f"Integration test suggestions failed: {e}")
            return {"error": str(e), "integration_tests": []}
    
    def _suggest_edge_cases(self, title: str, description: str, files: List[str],
                           additions: int, deletions: int, diff_content: str) -> Dict[str, Any]:
        """Suggest edge case tests based on code changes."""
        try:
            prompt = f"""
Analyze the following code changes and suggest edge case tests:

Title: {title}
Description: {description}
Files: {', '.join(files[:10])}
Additions: {additions}, Deletions: {deletions}

Diff Content:
{diff_content[:2000]}

Please suggest edge case tests for:
1. Boundary conditions
2. Error scenarios
3. Invalid inputs
4. Resource constraints
5. Race conditions
6. Security vulnerabilities

Return a JSON response with:
{{
    "edge_cases": [
        {{
            "test_name": "test_name",
            "description": "test description",
            "test_type": "edge_case",
            "priority": "high/medium/low",
            "suggested_code": "pytest test code snippet",
            "scenario": "edge case scenario",
            "expected_behavior": "expected behavior description"
        }}
    ],
    "risk_areas": ["list of high-risk areas"],
    "edge_case_strategy": "edge case testing approach"
}}
"""
            
            response = self.vertex_client.generate_text(
                prompt, max_tokens=1500, temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return self._parse_text_test_response(response, "edge_cases")
                
        except Exception as e:
            logger.error(f"Edge case suggestions failed: {e}")
            return {"error": str(e), "edge_cases": []}
    
    def _suggest_performance_tests(self, title: str, description: str, files: List[str],
                                  additions: int, deletions: int, diff_content: str) -> Dict[str, Any]:
        """Suggest performance tests based on code changes."""
        try:
            prompt = f"""
Analyze the following code changes and suggest performance tests:

Title: {title}
Description: {description}
Files: {', '.join(files[:10])}
Additions: {additions}, Deletions: {deletions}

Diff Content:
{diff_content[:2000]}

Please suggest performance tests for:
1. Algorithm efficiency
2. Memory usage
3. Database query performance
4. API response times
5. Concurrent operations
6. Resource utilization

Return a JSON response with:
{{
    "performance_tests": [
        {{
            "test_name": "test_name",
            "description": "test description",
            "test_type": "performance",
            "priority": "high/medium/low",
            "suggested_code": "pytest test code snippet",
            "metric": "performance metric to measure",
            "threshold": "performance threshold"
        }}
    ],
    "performance_concerns": ["list of performance concerns"],
    "testing_tools": ["suggested testing tools"]
}}
"""
            
            response = self.vertex_client.generate_text(
                prompt, max_tokens=1500, temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return self._parse_text_test_response(response, "performance_tests")
                
        except Exception as e:
            logger.error(f"Performance test suggestions failed: {e}")
            return {"error": str(e), "performance_tests": []}
    
    def _combine_test_suggestions(self, unit_tests: Dict[str, Any],
                                integration_tests: Dict[str, Any],
                                edge_cases: Dict[str, Any],
                                performance_tests: Dict[str, Any],
                                mr_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Combine all test suggestions into final result."""
        try:
            # Extract all test suggestions
            all_tests = []
            
            # Add unit tests
            unit_test_list = unit_tests.get("unit_tests", [])
            for test in unit_test_list:
                test["category"] = "unit"
                all_tests.append(test)
            
            # Add integration tests
            integration_test_list = integration_tests.get("integration_tests", [])
            for test in integration_test_list:
                test["category"] = "integration"
                all_tests.append(test)
            
            # Add edge cases
            edge_case_list = edge_cases.get("edge_cases", [])
            for test in edge_case_list:
                test["category"] = "edge_case"
                all_tests.append(test)
            
            # Add performance tests
            performance_test_list = performance_tests.get("performance_tests", [])
            for test in performance_test_list:
                test["category"] = "performance"
                all_tests.append(test)
            
            # Prioritize tests
            priority_order = {"high": 3, "medium": 2, "low": 1}
            all_tests.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 1), reverse=True)
            
            # Calculate summary statistics
            total_tests = len(all_tests)
            high_priority = len([t for t in all_tests if t.get("priority") == "high"])
            medium_priority = len([t for t in all_tests if t.get("priority") == "medium"])
            low_priority = len([t for t in all_tests if t.get("priority") == "low"])
            
            return {
                "all_tests": all_tests[:20],  # Limit to top 20 suggestions
                "summary": {
                    "total_tests": total_tests,
                    "high_priority": high_priority,
                    "medium_priority": medium_priority,
                    "low_priority": low_priority
                },
                "unit_tests": unit_tests,
                "integration_tests": integration_tests,
                "edge_cases": edge_cases,
                "performance_tests": performance_tests,
                "suggestions_timestamp": datetime.now().isoformat(),
                "mr_context": mr_context
            }
            
        except Exception as e:
            logger.error(f"Test suggestion combination failed: {e}")
            return self._fallback_suggestions(e)
    
    def _parse_text_test_response(self, text: str, test_type: str) -> Dict[str, Any]:
        """Parse text response into structured format."""
        try:
            # Simple text parsing for fallback
            lines = text.split('\n')
            tests = []
            
            current_test = {}
            for line in lines:
                line = line.strip()
                if line.startswith('Test:'):
                    if current_test:
                        tests.append(current_test)
                    current_test = {"test_name": line.replace('Test:', '').strip()}
                elif line.startswith('Description:'):
                    current_test["description"] = line.replace('Description:', '').strip()
                elif line.startswith('Priority:'):
                    current_test["priority"] = line.replace('Priority:', '').strip().lower()
                elif line.startswith('Code:'):
                    current_test["suggested_code"] = line.replace('Code:', '').strip()
            
            if current_test:
                tests.append(current_test)
            
            return {
                test_type: tests[:5],  # Limit to 5 suggestions
                "parsed_from_text": True
            }
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return {"error": str(e), test_type: []}
    
    def _fallback_suggestions(self, error: Exception) -> Dict[str, Any]:
        """Provide fallback suggestions when AI analysis fails."""
        return {
            "all_tests": [],
            "summary": {
                "total_tests": 0,
                "high_priority": 0,
                "medium_priority": 0,
                "low_priority": 0
            },
            "error": str(error),
            "fallback": True,
            "suggestions_timestamp": datetime.now().isoformat(),
            "message": "AI test suggestions unavailable, using fallback"
        }


# Global instance
ai_test_suggester = AITestSuggester()
