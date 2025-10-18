"""
Vertex AI client for text generation using Gemini 2.5 Flash Lite.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from .config import get_settings

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Client for Vertex AI text generation."""
    
    def __init__(self):
        """Initialize Vertex AI client."""
        settings = get_settings()
        self.project_id = settings.gcp_project_id
        self.location = settings.vertex_location
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # Initialize Gemini model
        self.model = GenerativeModel(settings.vertex_ai_model)
        
        logger.info(f"Vertex AI client initialized for project: {self.project_id}")
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Generate text using Gemini 2.5 Flash Lite.
        
        Args:
            prompt: Input prompt for text generation
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If text generation fails
        """
        try:
            logger.debug(f"Generating text with prompt length: {len(prompt)}")
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
            )
            
            if response.text:
                logger.info(f"Generated text response: {len(response.text)} characters")
                return response.text
            else:
                logger.warning("Empty response from Vertex AI")
                return ""
                
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise
    
    def summarize_diff(self, title: str, description: str, files: list, 
                      additions: int, deletions: int, diff_snippets: str) -> Dict[str, Any]:
        """
        Summarize a merge request diff using Gemini 2.5 Flash Lite.
        
        Args:
            title: Merge request title
            description: Merge request description
            files: List of modified files
            additions: Number of lines added
            deletions: Number of lines deleted
            diff_snippets: Trimmed diff content
            
        Returns:
            Dictionary with summary, risks, and tests
            
        Raises:
            Exception: If summarization fails
        """
        try:
            # Check if diff is empty or insufficient
            if not diff_snippets or not diff_snippets.strip():
                return {
                    "summary": ["Insufficient context for analysis"],
                    "risks": ["Unable to assess risks without diff content"],
                    "tests": ["Unable to suggest tests without diff content"]
                }
            
            # Load prompt template
            prompt_template = self._load_prompt_template("summarize_diff")
            
            # Format the prompt
            prompt = prompt_template.format(
                title=title or "Untitled",
                description=description or "No description provided",
                files=", ".join(files[:10]) if files else "No files listed",
                additions=additions,
                deletions=deletions,
                diff=diff_snippets[:2000]  # Limit diff size
            )
            
            # Generate summary
            response_text = self.generate_text(prompt, max_tokens=800, temperature=0.3)
            
            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                # Fallback: parse text response
                return self._parse_text_response(response_text)
                
        except Exception as e:
            logger.error(f"Diff summarization failed: {e}")
            return {
                "summary": [f"Summarization failed: {str(e)}"],
                "risks": ["Unable to assess risks due to processing error"],
                "tests": ["Unable to suggest tests due to processing error"]
            }
    
    def _load_prompt_template(self, template_name: str) -> str:
        """Load prompt template from file."""
        try:
            template_path = f"docs/prompts/{template_name}.md"
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract the user prompt template from markdown
            lines = content.split('\n')
            in_template = False
            template_lines = []
            
            for line in lines:
                if "## User Prompt Template" in line:
                    in_template = True
                    continue
                elif in_template and line.startswith("##"):
                    break
                elif in_template and line.strip():
                    template_lines.append(line)
            
            return '\n'.join(template_lines)
            
        except Exception as e:
            logger.error(f"Failed to load prompt template {template_name}: {e}")
            # Return default template
            return """
            Title: {title}
            Description: {description}
            Files: {files}
            Additions: {additions}  Deletions: {deletions}
            Diff: {diff}
            
            Please provide a summary, risks, and test suggestions.
            """
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """Parse text response into structured format."""
        lines = response_text.split('\n')
        
        summary = []
        risks = []
        tests = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if 'summary' in line.lower():
                current_section = 'summary'
            elif 'risk' in line.lower():
                current_section = 'risk'
            elif 'test' in line.lower():
                current_section = 'test'
            elif line.startswith('-') or line.startswith('*'):
                # Bullet point
                content = line[1:].strip()
                if current_section == 'summary':
                    summary.append(content)
                elif current_section == 'risk':
                    risks.append(content)
                elif current_section == 'test':
                    tests.append(content)
        
        return {
            "summary": summary if summary else ["No summary provided"],
            "risks": risks if risks else ["No risks identified"],
            "tests": tests if tests else ["No tests suggested"]
        }
    
    def test_connection(self) -> bool:
        """Test Vertex AI connection."""
        try:
            response = self.generate_text("Hello, this is a test.", max_tokens=10)
            return len(response) > 0
        except Exception as e:
            logger.error(f"Vertex AI connection test failed: {e}")
            return False


# Global instance - lazy initialization
_vertex_client_instance = None

def get_vertex_client():
    """Get or create Vertex AI client instance."""
    global _vertex_client_instance
    if _vertex_client_instance is None:
        _vertex_client_instance = VertexAIClient()
    return _vertex_client_instance

class LazyVertexClient:
    """Lazy wrapper for Vertex AI client."""
    def __getattr__(self, name):
        return getattr(get_vertex_client(), name)

# For backward compatibility - this will only initialize when first accessed
vertex_client = LazyVertexClient()
