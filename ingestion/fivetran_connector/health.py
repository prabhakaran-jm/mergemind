"""
Health check endpoint for GitLab Fivetran Connector
"""

from flask import Flask, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        # Check GitLab API connectivity
        gitlab_token = os.getenv('GITLAB_TOKEN')
        gitlab_base_url = os.getenv('GITLAB_BASE_URL', 'https://gitlab.com')
        
        if not gitlab_token:
            return jsonify({
                'status': 'unhealthy',
                'error': 'GITLAB_TOKEN not configured'
            }), 503
        
        # Test GitLab API
        headers = {'Authorization': f'Bearer {gitlab_token}'}
        response = requests.get(
            f'{gitlab_base_url}/api/v4/user',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'gitlab_api': 'connected',
                'version': '1.0.0'
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'error': f'GitLab API returned {response.status_code}'
            }), 503
            
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@app.route('/ready')
def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check all required environment variables
        required_vars = ['GITLAB_TOKEN']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            return jsonify({
                'status': 'not_ready',
                'missing_variables': missing_vars
            }), 503
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e)
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
