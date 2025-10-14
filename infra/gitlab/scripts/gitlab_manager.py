#!/usr/bin/env python3
"""
Consolidated GitLab Management Script
Handles projects, merge requests, users, and content creation for AI testing.
"""

import requests
import os
import json
from typing import Dict, List, Optional

# Configuration
GITLAB_BASE_URL = os.getenv('GITLAB_BASE_URL', 'https://35.202.37.189.sslip.io')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN', '')

class GitLabManager:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def create_project(self, name: str, description: str, visibility: str = 'private') -> Optional[Dict]:
        """Create a new GitLab project"""
        data = {
            'name': name,
            'description': description,
            'visibility': visibility,
            'initialize_with_readme': True
        }
        
        response = requests.post(f"{self.base_url}/api/v4/projects", 
                               headers=self.headers, json=data)
        
        if response.status_code == 201:
            project = response.json()
            print(f"✅ Created project '{name}' (ID: {project['id']})")
            return project
        else:
            print(f"❌ Failed to create project '{name}': {response.status_code} - {response.text}")
            return None
    
    def create_file(self, project_id: int, file_path: str, content: str, 
                   branch: str = "main", commit_message: str = "Add file") -> bool:
        """Create a file in a GitLab project"""
        data = {
            'branch': branch,
            'content': content,
            'commit_message': commit_message,
            'author_email': 'demo@mergemind.com',
            'author_name': 'Demo User'
        }
        
        response = requests.post(f"{self.base_url}/api/v4/projects/{project_id}/repository/files/{file_path}",
                               headers=self.headers, json=data)
        
        if response.status_code == 201:
            print(f"✅ Created {file_path} in project {project_id}")
            return True
        else:
            print(f"❌ Failed to create {file_path}: {response.status_code} - {response.text}")
            return False
    
    def create_branch(self, project_id: int, branch_name: str, ref: str = "main") -> bool:
        """Create a new branch"""
        data = {
            'branch': branch_name,
            'ref': ref
        }
        
        response = requests.post(f"{self.base_url}/api/v4/projects/{project_id}/repository/branches",
                               headers=self.headers, json=data)
        
        if response.status_code == 201:
            print(f"✅ Created branch {branch_name} in project {project_id}")
            return True
        else:
            print(f"❌ Failed to create branch {branch_name}: {response.status_code} - {response.text}")
            return False
    
    def create_merge_request(self, project_id: int, title: str, description: str, 
                           source_branch: str, target_branch: str = "main") -> Optional[Dict]:
        """Create a merge request"""
        data = {
            'title': title,
            'description': description,
            'source_branch': source_branch,
            'target_branch': target_branch,
            'assignee_id': 1  # Root user
        }
        
        response = requests.post(f"{self.base_url}/api/v4/projects/{project_id}/merge_requests",
                               headers=self.headers, json=data)
        
        if response.status_code == 201:
            mr = response.json()
            print(f"✅ Created MR '{title}' (ID: {mr['iid']}) in project {project_id}")
            return mr
        else:
            print(f"❌ Failed to create MR '{title}': {response.status_code} - {response.text}")
            return None
    
    def create_issue(self, project_id: int, title: str, description: str, 
                    labels: List[str] = None) -> Optional[Dict]:
        """Create an issue"""
        data = {
            'title': title,
            'description': description,
            'assignee_id': 1,
            'labels': labels or ['enhancement', 'demo']
        }
        
        response = requests.post(f"{self.base_url}/api/v4/projects/{project_id}/issues",
                               headers=self.headers, json=data)
        
        if response.status_code == 201:
            issue = response.json()
            print(f"✅ Created issue '{title}' (ID: {issue['iid']}) in project {project_id}")
            return issue
        else:
            print(f"❌ Failed to create issue '{title}': {response.status_code} - {response.text}")
            return None

def get_project_templates() -> Dict[str, Dict]:
    """Get project templates with files, branches, and merge requests"""
    return {
        'mergemind-database-service': {
            'description': 'Database service with PostgreSQL and Redis integration',
            'files': {
                'README.md': '''# MergeMind Database Service

A microservice for database operations with PostgreSQL and Redis caching.

## Features
- PostgreSQL database operations
- Redis caching layer
- Connection pooling
- Database migrations
- Query optimization

## Getting Started
```bash
npm install
npm run migrate
npm start
```

## Environment Variables
- DATABASE_URL
- REDIS_URL
- NODE_ENV
''',
                'package.json': '''{
  "name": "mergemind-database-service",
  "version": "1.0.0",
  "description": "Database service for MergeMind",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "migrate": "node migrations/migrate.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.0",
    "redis": "^4.6.0",
    "sequelize": "^6.32.0",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  }
}''',
                'server.js': '''const express = require('express');
const { Pool } = require('pg');
const redis = require('redis');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3002;

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Redis connection
const redisClient = redis.createClient({
  url: process.env.REDIS_URL
});

redisClient.on('error', (err) => {
  console.error('Redis error:', err);
});

redisClient.connect();

// Middleware
app.use(express.json());

// Health check
app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    await redisClient.ping();
    res.json({ 
      status: 'OK', 
      database: 'connected',
      redis: 'connected',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'ERROR', 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

app.listen(PORT, () => {
  console.log(`Database service running on port ${PORT}`);
});'''
            },
            'branches': ['feature/redis-caching', 'feature/query-optimization'],
            'merge_requests': [
                {
                    'title': 'Implement Redis caching layer for database queries',
                    'description': '''## Summary
Adds Redis caching layer to improve database query performance and reduce load.

## Changes
- Added Redis client configuration
- Implemented cache middleware for GET requests
- Added cache invalidation for POST/PUT/DELETE operations
- Added cache TTL configuration
- Implemented cache warming strategies

## Performance Improvements
- Reduced database load by 60%
- Improved response times by 40%
- Added cache hit/miss metrics
- Implemented cache warming for frequently accessed data

## Testing
- [x] Cache hit/miss scenarios
- [x] Cache invalidation works correctly
- [x] TTL expiration handling
- [ ] Load testing with cache

Closes #1''',
                    'source_branch': 'feature/redis-caching'
                }
            ]
        },
        'mergemind-notification-service': {
            'description': 'Notification service with email, SMS, and push notifications',
            'files': {
                'README.md': '''# MergeMind Notification Service

A comprehensive notification service supporting multiple channels.

## Features
- Email notifications (SMTP)
- SMS notifications (Twilio)
- Push notifications (FCM)
- Notification templates
- Delivery tracking
- Retry mechanisms

## Getting Started
```bash
npm install
npm start
```

## Environment Variables
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
- FCM_SERVER_KEY
''',
                'package.json': '''{
  "name": "mergemind-notification-service",
  "version": "1.0.0",
  "description": "Notification service for MergeMind",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "nodemailer": "^6.9.0",
    "twilio": "^4.15.0",
    "firebase-admin": "^11.10.0",
    "handlebars": "^4.7.8",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  }
}''',
                'server.js': '''const express = require('express');
const nodemailer = require('nodemailer');
const twilio = require('twilio');
const admin = require('firebase-admin');
const handlebars = require('handlebars');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3003;

// Initialize Firebase Admin
admin.initializeApp({
  credential: admin.credential.cert({
    projectId: process.env.FIREBASE_PROJECT_ID,
    clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
    privateKey: process.env.FIREBASE_PRIVATE_KEY.replace(/\\n/g, '\\n')
  })
});

// Email transporter
const emailTransporter = nodemailer.createTransporter({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  secure: true,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  }
});

// Twilio client
const twilioClient = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);

// Middleware
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    services: {
      email: 'configured',
      sms: 'configured',
      push: 'configured'
    },
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`Notification service running on port ${PORT}`);
});'''
            },
            'branches': ['feature/email-templates', 'feature/delivery-tracking'],
            'merge_requests': [
                {
                    'title': 'Add email template system with Handlebars',
                    'description': '''## Summary
Implements a flexible email template system using Handlebars for dynamic content generation.

## Changes
- Added Handlebars template engine
- Created template management system
- Implemented template compilation and rendering
- Added template validation
- Created default templates for common notifications

## Template Features
- Dynamic content insertion
- Conditional rendering
- Loop support for lists
- Custom helpers for formatting
- Template inheritance

## Templates Added
- Welcome email template
- Password reset template
- Notification template
- Invoice template

## Testing
- [x] Template compilation works
- [x] Dynamic data insertion
- [x] Conditional rendering
- [ ] Template validation tests

Closes #1''',
                    'source_branch': 'feature/email-templates'
                }
            ]
        },
        'mergemind-analytics-service': {
            'description': 'Analytics service with data processing and visualization',
            'files': {
                'README.md': '''# MergeMind Analytics Service

Advanced analytics service for processing and visualizing data.

## Features
- Real-time data processing
- Statistical analysis
- Data visualization
- Report generation
- Export capabilities

## Getting Started
```bash
npm install
npm run build
npm start
```

## Environment Variables
- DATABASE_URL
- REDIS_URL
- ELASTICSEARCH_URL
''',
                'package.json': '''{
  "name": "mergemind-analytics-service",
  "version": "1.0.0",
  "description": "Analytics service for MergeMind",
  "main": "dist/server.js",
  "scripts": {
    "start": "node dist/server.js",
    "dev": "ts-node src/server.ts",
    "build": "tsc",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "typescript": "^5.2.0",
    "@types/express": "^4.17.17",
    "elasticsearch": "^16.7.0",
    "d3": "^7.8.0",
    "chart.js": "^4.4.0"
  },
  "devDependencies": {
    "ts-node": "^10.9.0",
    "@types/node": "^20.5.0",
    "jest": "^29.6.2"
  }
}''',
                'src/server.ts': '''import express from 'express';
import { Client } from 'elasticsearch';
import * as d3 from 'd3';

const app = express();
const PORT = process.env.PORT || 3004;

// Elasticsearch client
const esClient = new Client({
  host: process.env.ELASTICSEARCH_URL || 'localhost:9200'
});

// Middleware
app.use(express.json());

// Health check
app.get('/health', async (req, res) => {
  try {
    await esClient.ping();
    res.json({ 
      status: 'OK', 
      elasticsearch: 'connected',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'ERROR', 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

app.listen(PORT, () => {
  console.log(`Analytics service running on port ${PORT}`);
});'''
            },
            'branches': ['feature/real-time-processing', 'feature/data-visualization'],
            'merge_requests': [
                {
                    'title': 'Implement real-time data processing with Elasticsearch',
                    'description': '''## Summary
Adds real-time data processing capabilities using Elasticsearch for fast analytics and search.

## Changes
- Integrated Elasticsearch client
- Implemented real-time event indexing
- Added data aggregation queries
- Created dashboard data endpoints
- Added time-series data processing

## Performance Features
- Sub-second query response times
- Horizontal scaling support
- Real-time data ingestion
- Advanced aggregation capabilities
- Full-text search functionality

## Data Processing
- Event streaming and indexing
- Real-time aggregations
- Time-series data handling
- Data retention policies
- Backup and recovery

## Testing
- [x] Elasticsearch connection
- [x] Data indexing works
- [x] Aggregation queries
- [ ] Performance testing

Closes #1''',
                    'source_branch': 'feature/real-time-processing'
                }
            ]
        }
    }

def main():
    """Main function to manage GitLab projects and content"""
    print("🚀 MergeMind GitLab Management Script")
    print(f"Base URL: {GITLAB_BASE_URL}")
    print()
    
    # Initialize GitLab manager
    gitlab = GitLabManager(GITLAB_BASE_URL, GITLAB_TOKEN)
    
    # Get project templates
    templates = get_project_templates()
    
    created_projects = []
    
    # Create projects
    for project_name, config in templates.items():
        print(f"\n=== Creating Project: {project_name} ===")
        
        project = gitlab.create_project(
            project_name, 
            config['description']
        )
        
        if project:
            created_projects.append(project)
            project_id = project['id']
            
            # Create files in main branch
            for file_path, content in config['files'].items():
                gitlab.create_file(
                    project_id, 
                    file_path, 
                    content, 
                    'main', 
                    f"Add {file_path}"
                )
            
            # Create feature branches
            for branch in config['branches']:
                gitlab.create_branch(project_id, branch)
            
            # Create merge requests
            for mr in config['merge_requests']:
                gitlab.create_merge_request(
                    project_id, 
                    mr['title'], 
                    mr['description'], 
                    mr['source_branch']
                )
    
    print(f"\n=== Project Creation Complete ===")
    print(f"Created {len(created_projects)} new projects:")
    
    for project in created_projects:
        print(f"  - {project['name']} (ID: {project['id']})")
        print(f"    URL: {project['web_url']}")
    
    print(f"\nTotal projects now available for AI testing:")
    print(f"  - mergemind-demo-backend (ID: 4)")
    print(f"  - mergemind-demo-frontend (ID: 5)")
    print(f"  - mergemind-demo-api (ID: 6)")
    for project in created_projects:
        print(f"  - {project['name']} (ID: {project['id']})")
    
    print(f"\nNext steps:")
    print(f"1. Update Fivetran connector to include new project IDs")
    print(f"2. Wait for data sync to BigQuery")
    print(f"3. Test AI analysis with diverse code changes")

if __name__ == "__main__":
    main()
