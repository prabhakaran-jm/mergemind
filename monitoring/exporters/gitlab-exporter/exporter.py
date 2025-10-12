#!/usr/bin/env python3
"""
GitLab metrics exporter for Prometheus.
"""

import os
import time
import logging
import requests
from flask import Flask, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
gitlab_api_requests_total = Counter(
    'gitlab_api_requests_total',
    'Total GitLab API requests',
    ['endpoint', 'status']
)

gitlab_api_duration_seconds = Histogram(
    'gitlab_api_duration_seconds',
    'GitLab API request duration',
    ['endpoint']
)

gitlab_rate_limit_remaining = Gauge(
    'gitlab_rate_limit_remaining',
    'GitLab API rate limit remaining'
)

gitlab_rate_limit_reset = Gauge(
    'gitlab_rate_limit_reset',
    'GitLab API rate limit reset timestamp'
)

gitlab_projects_total = Gauge(
    'gitlab_projects_total',
    'Total number of GitLab projects'
)

gitlab_merge_requests_total = Gauge(
    'gitlab_merge_requests_total',
    'Total number of merge requests',
    ['state']
)

gitlab_users_total = Gauge(
    'gitlab_users_total',
    'Total number of GitLab users'
)

gitlab_pipelines_total = Gauge(
    'gitlab_pipelines_total',
    'Total number of pipelines',
    ['status']
)

# Flask app
app = Flask(__name__)

class GitLabExporter:
    def __init__(self):
        self.base_url = os.getenv('GITLAB_BASE_URL', 'https://gitlab.com')
        self.token = os.getenv('GITLAB_TOKEN')
        
        if not self.token:
            raise ValueError("GITLAB_TOKEN environment variable is required")
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"GitLab exporter initialized for: {self.base_url}")
    
    def collect_metrics(self):
        """Collect GitLab metrics."""
        try:
            # Get rate limit info
            self._collect_rate_limit_metrics()
            
            # Get project metrics
            self._collect_project_metrics()
            
            # Get merge request metrics
            self._collect_merge_request_metrics()
            
            # Get user metrics
            self._collect_user_metrics()
            
            # Get pipeline metrics
            self._collect_pipeline_metrics()
            
            logger.info("GitLab metrics collected successfully")
            
        except Exception as e:
            logger.error(f"Failed to collect GitLab metrics: {e}")
            gitlab_api_requests_total.labels(endpoint='unknown', status='error').inc()
    
    def _make_request(self, endpoint, params=None):
        """Make a request to GitLab API."""
        url = f"{self.base_url}/api/v4{endpoint}"
        
        start_time = time.time()
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            duration = time.time() - start_time
            
            # Record metrics
            gitlab_api_requests_total.labels(endpoint=endpoint, status=str(response.status_code)).inc()
            gitlab_api_duration_seconds.labels(endpoint=endpoint).observe(duration)
            
            # Update rate limit info
            if 'X-RateLimit-Remaining' in response.headers:
                gitlab_rate_limit_remaining.set(int(response.headers['X-RateLimit-Remaining']))
            
            if 'X-RateLimit-Reset' in response.headers:
                gitlab_rate_limit_reset.set(int(response.headers['X-RateLimit-Reset']))
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            gitlab_api_requests_total.labels(endpoint=endpoint, status='error').inc()
            gitlab_api_duration_seconds.labels(endpoint=endpoint).observe(duration)
            raise e
    
    def _collect_rate_limit_metrics(self):
        """Collect rate limit metrics."""
        try:
            # Make a simple request to get rate limit headers
            self._make_request('/user')
        except Exception as e:
            logger.error(f"Failed to collect rate limit metrics: {e}")
    
    def _collect_project_metrics(self):
        """Collect project metrics."""
        try:
            # Get total project count
            projects = self._make_request('/projects', {'per_page': 1, 'statistics': 'true'})
            
            # Get total count from headers
            response = requests.get(
                f"{self.base_url}/api/v4/projects",
                headers=self.headers,
                params={'per_page': 1, 'statistics': 'true'},
                timeout=10
            )
            
            if 'X-Total' in response.headers:
                total_projects = int(response.headers['X-Total'])
                gitlab_projects_total.set(total_projects)
            
        except Exception as e:
            logger.error(f"Failed to collect project metrics: {e}")
    
    def _collect_merge_request_metrics(self):
        """Collect merge request metrics."""
        try:
            # Get merge requests by state
            states = ['opened', 'closed', 'merged']
            
            for state in states:
                try:
                    response = requests.get(
                        f"{self.base_url}/api/v4/merge_requests",
                        headers=self.headers,
                        params={'state': state, 'per_page': 1},
                        timeout=10
                    )
                    
                    if 'X-Total' in response.headers:
                        total_mrs = int(response.headers['X-Total'])
                        gitlab_merge_requests_total.labels(state=state).set(total_mrs)
                        
                except Exception as e:
                    logger.error(f"Failed to collect MR metrics for state {state}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to collect merge request metrics: {e}")
    
    def _collect_user_metrics(self):
        """Collect user metrics."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v4/users",
                headers=self.headers,
                params={'per_page': 1},
                timeout=10
            )
            
            if 'X-Total' in response.headers:
                total_users = int(response.headers['X-Total'])
                gitlab_users_total.set(total_users)
                
        except Exception as e:
            logger.error(f"Failed to collect user metrics: {e}")
    
    def _collect_pipeline_metrics(self):
        """Collect pipeline metrics."""
        try:
            # Get pipelines by status
            statuses = ['success', 'failed', 'running', 'pending']
            
            for status in statuses:
                try:
                    response = requests.get(
                        f"{self.base_url}/api/v4/pipelines",
                        headers=self.headers,
                        params={'status': status, 'per_page': 1},
                        timeout=10
                    )
                    
                    if 'X-Total' in response.headers:
                        total_pipelines = int(response.headers['X-Total'])
                        gitlab_pipelines_total.labels(status=status).set(total_pipelines)
                        
                except Exception as e:
                    logger.error(f"Failed to collect pipeline metrics for status {status}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to collect pipeline metrics: {e}")

# Global exporter instance
exporter = GitLabExporter()

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    exporter.collect_metrics()
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        # Test GitLab API connection
        exporter._make_request('/user')
        return Response("OK", status=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response("ERROR", status=500)

@app.route('/')
def index():
    """Index page."""
    return """
    <h1>GitLab Exporter</h1>
    <p><a href="/metrics">Metrics</a></p>
    <p><a href="/health">Health</a></p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
