"""
Simplified Cloud Function to trigger dbt runs.
This function is called directly by the Fivetran connector when sync completes.
"""

import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

import functions_framework
from google.cloud import bigquery
from google.cloud import logging as cloud_logging
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Google Cloud clients
bq_client = bigquery.Client()
storage_client = storage.Client()

# Configuration from environment variables
PROJECT_ID = os.getenv('PROJECT_ID')
BQ_DATASET_RAW = os.getenv('BQ_DATASET_RAW', 'mergemind_raw')
BQ_DATASET_MODELED = os.getenv('BQ_DATASET_MODELED', 'mergemind')
DBT_PROFILES_DIR = os.getenv('DBT_PROFILES_DIR', '/tmp')


def setup_dbt_environment() -> str:
    """Set up dbt environment and return the working directory."""
    work_dir = tempfile.mkdtemp()
    
    # Create dbt profiles.yml
    profiles_content = f"""
mergemind:
  target: prod
  outputs:
    prod:
      type: bigquery
      method: oauth
      project: "{PROJECT_ID}"
      dataset: "{BQ_DATASET_MODELED}"
      location: "US"
      threads: 4
      timeout_seconds: 300
      priority: batch
      retries: 3
"""
    
    profiles_path = os.path.join(work_dir, 'profiles.yml')
    with open(profiles_path, 'w') as f:
        f.write(profiles_content)
    
    logger.info(f"Created dbt profiles.yml at {profiles_path}")
    return work_dir


def download_dbt_project(work_dir: str) -> str:
    """Download dbt project from Cloud Storage."""
    # For now, we'll create a minimal dbt project structure
    # In production, this would download from a Cloud Storage bucket
    
    dbt_project_path = os.path.join(work_dir, 'dbt_project')
    os.makedirs(dbt_project_path, exist_ok=True)
    
    # Create dbt_project.yml
    dbt_project_content = """
name: 'mergemind'
version: '1.0.0'
config-version: 2

profile: 'mergemind'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  mergemind:
    +materialized: view
    
    mr_activity_view:
      +materialized: view
      
    cycle_time_view:
      +materialized: view
      
    merge_risk_features:
      +materialized: view
"""
    
    with open(os.path.join(dbt_project_path, 'dbt_project.yml'), 'w') as f:
        f.write(dbt_project_content)
    
    # Create models directory
    models_dir = os.path.join(dbt_project_path, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Create sources.yml
    sources_content = f"""
version: 2

sources:
  - name: raw
    description: "Raw GitLab data from Fivetran connector"
    database: {PROJECT_ID}
    schema: {BQ_DATASET_RAW}
    tables:
      - name: merge_requests
        description: "Raw merge requests data from GitLab"
      - name: projects
        description: "Raw projects data from GitLab"
      - name: users
        description: "Raw users data from GitLab"
"""
    
    with open(os.path.join(models_dir, 'sources.yml'), 'w') as f:
        f.write(sources_content)
    
    # Create a simple model
    model_content = """
{{ config(materialized='view') }}

-- MR activity view using raw data
SELECT
  id as mr_id,
  project_id, 
  title, 
  author_id, 
  created_at, 
  state,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) AS age_hours,
  source_branch,
  target_branch,
  web_url,
  assignee_id,
  updated_at,
  merged_at,
  closed_at
FROM {{ source('raw', 'merge_requests') }}
"""
    
    with open(os.path.join(models_dir, 'mr_activity_view.sql'), 'w') as f:
        f.write(model_content)
    
    logger.info(f"Created dbt project structure at {dbt_project_path}")
    return dbt_project_path


def run_dbt_command(dbt_project_path: str, command: str) -> tuple[bool, str]:
    """Run a dbt command and return success status and output."""
    try:
        # Set environment variables
        env = os.environ.copy()
        env['DBT_PROFILES_DIR'] = os.path.dirname(dbt_project_path)
        env['GCP_PROJECT_ID'] = PROJECT_ID
        env['BQ_DATASET_MODELED'] = BQ_DATASET_MODELED
        
        # Run dbt command
        result = subprocess.run(
            ['dbt', command],
            cwd=dbt_project_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        logger.info(f"dbt {command} completed with return code: {result.returncode}")
        logger.info(f"dbt output: {output}")
        
        return success, output
        
    except subprocess.TimeoutExpired:
        logger.error(f"dbt {command} timed out after 5 minutes")
        return False, "Command timed out"
    except Exception as e:
        logger.error(f"Error running dbt {command}: {e}")
        return False, str(e)


def _run_dbt_commands() -> bool:
    """Trigger dbt run to transform data."""
    try:
        logger.info("Starting dbt run...")
        
        # Set up dbt environment
        work_dir = setup_dbt_environment()
        dbt_project_path = download_dbt_project(work_dir)
        
        # Run dbt deps (install dependencies)
        logger.info("Installing dbt dependencies...")
        success, output = run_dbt_command(dbt_project_path, 'deps')
        if not success:
            logger.error(f"Failed to install dbt dependencies: {output}")
            return False
        
        # Run dbt run (transform data)
        logger.info("Running dbt transformations...")
        success, output = run_dbt_command(dbt_project_path, 'run')
        if not success:
            logger.error(f"Failed to run dbt transformations: {output}")
            return False
        
        # Run dbt test (validate data)
        logger.info("Running dbt tests...")
        success, output = run_dbt_command(dbt_project_path, 'test')
        if not success:
            logger.warning(f"dbt tests failed: {output}")
            # Don't fail the entire process if tests fail
        
        logger.info("dbt run completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in _run_dbt_commands: {e}")
        return False


@functions_framework.http
def trigger_dbt_run(request):
    """
    HTTP Cloud Function entry point for triggering dbt runs.
    Called by Fivetran connector when sync completes.
    
    Args:
        request: HTTP request object
    """
    try:
        # Check authentication token
        auth_token = os.getenv('AUTH_TOKEN')
        if auth_token and auth_token != "your-secure-token-here":
            # Check for Authorization header
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer ') or auth_header[7:] != auth_token:
                logger.warning("Unauthorized access attempt")
                return json.dumps({
                    "status": "error",
                    "message": "Unauthorized access"
                }), 401
        
        # Parse request data
        if request.method == 'POST':
            try:
                request_json = request.get_json()
                source = request_json.get('source', 'unknown')
                sync_info = request_json.get('sync_info', {})
            except:
                request_json = {}
                source = 'fivetran'
                sync_info = {}
        else:
            request_json = {}
            source = 'fivetran'
            sync_info = {}
        
        logger.info(f"Received dbt trigger request from {source}")
        logger.info(f"Request data: {request_json}")
        logger.info(f"Sync info: {sync_info}")
        
        # Trigger dbt run
        success = _run_dbt_commands()
        
        if success:
            logger.info("Successfully completed dbt run")
            return json.dumps({
                "status": "success",
                "message": "dbt run completed successfully",
                "source": source,
                "sync_info": sync_info,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
        else:
            logger.error("Failed to complete dbt run")
            return json.dumps({
                "status": "error",
                "message": "dbt run failed",
                "source": source,
                "sync_info": sync_info,
                "timestamp": datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing dbt trigger request: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


if __name__ == "__main__":
    # For local testing
    _run_dbt_commands()