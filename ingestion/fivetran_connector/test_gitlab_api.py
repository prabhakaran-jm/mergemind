#!/usr/bin/env python3
"""Test GitLab API access for Fivetran connector"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def test_gitlab_api():
    """Test GitLab API access with configured projects"""
    
    base_url = os.getenv('GITLAB_BASE_URL')
    token = os.getenv('GITLAB_TOKEN')
    project_ids = os.getenv('GITLAB_PROJECT_IDS', '').split(',')
    
    if not all([base_url, token, project_ids]):
        print("ERROR Missing required environment variables")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"Testing GitLab API: {base_url}")
    print(f"Using token: {token[:20]}...")
    print(f"Project IDs: {project_ids}")
    print()
    
    # Test each project
    for project_id in project_ids:
        project_id = project_id.strip()
        if not project_id:
            continue
            
        try:
            url = f"{base_url}/api/v4/projects/{project_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                project = response.json()
                print(f"SUCCESS Project {project_id}: {project['name']}")
                print(f"   Description: {project['description']}")
                print(f"   URL: {project['web_url']}")
                print(f"   Visibility: {project['visibility']}")
                print()
            else:
                print(f"ERROR Project {project_id}: HTTP {response.status_code}")
                print(f"   Error: {response.text}")
                print()
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR Project {project_id}: Request failed - {e}")
            print()
    
    # Test merge requests endpoint
    print("Testing merge requests endpoint...")
    try:
        url = f"{base_url}/api/v4/projects/{project_ids[0].strip()}/merge_requests"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            mrs = response.json()
            print(f"SUCCESS Found {len(mrs)} merge requests in project {project_ids[0].strip()}")
        else:
            print(f"ERROR Merge requests endpoint: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR Merge requests endpoint: Request failed - {e}")
    
    print()
    print("GitLab API test completed!")

if __name__ == "__main__":
    test_gitlab_api()
