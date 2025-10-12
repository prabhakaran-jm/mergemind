#!/usr/bin/env python3
"""
Vertex AI metrics exporter for Prometheus.
"""

import os
import time
import logging
from flask import Flask, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
import vertexai
from vertexai.generative_models import GenerativeModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
vertex_ai_requests_total = Counter(
    'vertex_ai_requests_total',
    'Total Vertex AI requests',
    ['model', 'status']
)

vertex_ai_request_duration_seconds = Histogram(
    'vertex_ai_request_duration_seconds',
    'Vertex AI request duration',
    ['model']
)

vertex_ai_tokens_total = Counter(
    'vertex_ai_tokens_total',
    'Total tokens processed',
    ['model', 'token_type']
)

vertex_ai_quota_usage = Gauge(
    'vertex_ai_quota_usage',
    'Vertex AI quota usage percentage',
    ['quota_type']
)

vertex_ai_model_availability = Gauge(
    'vertex_ai_model_availability',
    'Vertex AI model availability',
    ['model']
)

vertex_ai_error_rate = Gauge(
    'vertex_ai_error_rate',
    'Vertex AI error rate',
    ['model']
)

# Flask app
app = Flask(__name__)

class VertexAIExporter:
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.location = os.getenv('VERTEX_LOCATION', 'us-central1')
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel("gemini-1.5-pro")
        
        logger.info(f"Vertex AI exporter initialized for project: {self.project_id}")
    
    def collect_metrics(self):
        """Collect Vertex AI metrics."""
        try:
            # Test model availability
            self._test_model_availability()
            
            # Get quota usage (placeholder)
            self._collect_quota_metrics()
            
            # Test a simple request to get metrics
            self._test_model_request()
            
            logger.info("Vertex AI metrics collected successfully")
            
        except Exception as e:
            logger.error(f"Failed to collect Vertex AI metrics: {e}")
            vertex_ai_requests_total.labels(model='gemini-1.5-pro', status='error').inc()
    
    def _test_model_availability(self):
        """Test model availability."""
        try:
            # Simple test to check if model is available
            start_time = time.time()
            response = self.model.generate_content(
                "Hello, this is a test.",
                generation_config={
                    "max_output_tokens": 10,
                    "temperature": 0.1,
                }
            )
            duration = time.time() - start_time
            
            # Record metrics
            vertex_ai_requests_total.labels(model='gemini-1.5-pro', status='success').inc()
            vertex_ai_request_duration_seconds.labels(model='gemini-1.5-pro').observe(duration)
            vertex_ai_model_availability.labels(model='gemini-1.5-pro').set(1.0)
            
            # Count tokens (approximate)
            if response.text:
                input_tokens = len("Hello, this is a test.") // 4  # Rough estimate
                output_tokens = len(response.text) // 4  # Rough estimate
                
                vertex_ai_tokens_total.labels(model='gemini-1.5-pro', token_type='input').inc(input_tokens)
                vertex_ai_tokens_total.labels(model='gemini-1.5-pro', token_type='output').inc(output_tokens)
            
        except Exception as e:
            logger.error(f"Model availability test failed: {e}")
            vertex_ai_requests_total.labels(model='gemini-1.5-pro', status='error').inc()
            vertex_ai_model_availability.labels(model='gemini-1.5-pro').set(0.0)
    
    def _collect_quota_metrics(self):
        """Collect quota usage metrics."""
        try:
            # Note: Quota metrics require special permissions and may not be available
            # This is a placeholder for future implementation
            
            # For now, we'll set placeholder values
            vertex_ai_quota_usage.labels(quota_type='requests').set(0.0)
            vertex_ai_quota_usage.labels(quota_type='tokens').set(0.0)
            vertex_ai_quota_usage.labels(quota_type='models').set(0.0)
            
        except Exception as e:
            logger.error(f"Failed to collect quota metrics: {e}")
    
    def _test_model_request(self):
        """Test a model request to get performance metrics."""
        try:
            start_time = time.time()
            response = self.model.generate_content(
                "What is 2+2?",
                generation_config={
                    "max_output_tokens": 50,
                    "temperature": 0.1,
                }
            )
            duration = time.time() - start_time
            
            # Record metrics
            vertex_ai_requests_total.labels(model='gemini-1.5-pro', status='success').inc()
            vertex_ai_request_duration_seconds.labels(model='gemini-1.5-pro').observe(duration)
            
            # Count tokens
            if response.text:
                input_tokens = len("What is 2+2?") // 4  # Rough estimate
                output_tokens = len(response.text) // 4  # Rough estimate
                
                vertex_ai_tokens_total.labels(model='gemini-1.5-pro', token_type='input').inc(input_tokens)
                vertex_ai_tokens_total.labels(model='gemini-1.5-pro', token_type='output').inc(output_tokens)
            
        except Exception as e:
            logger.error(f"Model request test failed: {e}")
            vertex_ai_requests_total.labels(model='gemini-1.5-pro', status='error').inc()

# Global exporter instance
exporter = VertexAIExporter()

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    exporter.collect_metrics()
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        # Test Vertex AI connection
        exporter._test_model_availability()
        return Response("OK", status=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response("ERROR", status=500)

@app.route('/')
def index():
    """Index page."""
    return """
    <h1>Vertex AI Exporter</h1>
    <p><a href="/metrics">Metrics</a></p>
    <p><a href="/health">Health</a></p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
