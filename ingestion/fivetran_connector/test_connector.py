#!/usr/bin/env python3
"""
Test script for GitLab Fivetran Connector
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from connector import GitLabConnector

def test_connector():
    """Test the connector functionality."""
    print("🧪 Testing GitLab Fivetran Connector")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Checking environment variables...")
    required_vars = ['GITLAB_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required variables: {missing_vars}")
        return False
    
    print("✅ All required environment variables present")
    
    try:
        # Initialize connector
        print("\n🔧 Initializing connector...")
        connector = GitLabConnector()
        print("✅ Connector initialized successfully")
        
        # Test schema
        print("\n📊 Testing schema definition...")
        schema = connector.get_schema()
        print(f"✅ Schema defined with {len(schema)} tables")
        
        for table in schema:
            print(f"  - {table.name}: {len(table.columns)} columns")
        
        # Test data reading
        print("\n📖 Testing data reading...")
        test_tables = ['merge_requests', 'mr_notes', 'pipelines', 'projects', 'users']
        
        for table_name in test_tables:
            print(f"\n  Testing {table_name}...")
            try:
                records = list(connector.read(table_name))
                print(f"    ✅ Read {len(records)} records")
                
                if records:
                    # Show sample record
                    sample = records[0]
                    print(f"    📝 Sample record keys: {list(sample.keys())}")
                
            except Exception as e:
                print(f"    ❌ Error reading {table_name}: {e}")
                return False
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connector test failed: {e}")
        return False

def test_api_connectivity():
    """Test GitLab API connectivity."""
    print("\n🌐 Testing GitLab API connectivity...")
    
    try:
        import requests
        
        gitlab_token = os.getenv('GITLAB_TOKEN')
        gitlab_base_url = os.getenv('GITLAB_BASE_URL', 'https://gitlab.com')
        
        headers = {'Authorization': f'Bearer {gitlab_token}'}
        response = requests.get(
            f'{gitlab_base_url}/api/v4/user',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Connected to GitLab as {user_data.get('username', 'unknown')}")
            return True
        else:
            print(f"❌ GitLab API returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False

def test_data_quality():
    """Test data quality and validation."""
    print("\n🔍 Testing data quality...")
    
    try:
        connector = GitLabConnector()
        
        # Test merge requests
        mrs = list(connector.read('merge_requests'))
        if mrs:
            mr = mrs[0]
            required_fields = ['mr_id', 'project_id', 'title', 'author_id']
            missing_fields = [field for field in required_fields if not mr.get(field)]
            
            if missing_fields:
                print(f"❌ Missing required fields in MR data: {missing_fields}")
                return False
            
            print("✅ MR data quality check passed")
        
        # Test notes
        notes = list(connector.read('mr_notes'))
        if notes:
            note = notes[0]
            required_fields = ['note_id', 'project_id', 'mr_id', 'author_id']
            missing_fields = [field for field in required_fields if not note.get(field)]
            
            if missing_fields:
                print(f"❌ Missing required fields in note data: {missing_fields}")
                return False
            
            print("✅ Note data quality check passed")
        
        print("✅ All data quality checks passed")
        return True
        
    except Exception as e:
        print(f"❌ Data quality test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 GitLab Fivetran Connector Test Suite")
    print("=" * 50)
    
    # Run tests
    tests = [
        test_api_connectivity,
        test_connector,
        test_data_quality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test error in {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Connector is ready for production.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
