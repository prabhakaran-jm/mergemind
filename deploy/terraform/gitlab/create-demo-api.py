# GitLab Demo Resources - Alternative API Approach
# This script creates demo resources using GitLab API directly

import requests
import json
import time
import base64

class GitLabDemoCreator:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_project(self, name, description):
        """Create a GitLab project"""
        data = {
            'name': name,
            'description': description,
            'visibility': 'private',
            'issues_enabled': True,
            'merge_requests_enabled': True,
            'wiki_enabled': False,
            'snippets_enabled': False
        }
        
        response = requests.post(
            f'{self.base_url}/api/v4/projects',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def create_branch(self, project_id, branch_name, ref='main'):
        """Create a new branch"""
        data = {
            'branch': branch_name,
            'ref': ref
        }
        
        response = requests.post(
            f'{self.base_url}/api/v4/projects/{project_id}/repository/branches',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def create_file(self, project_id, file_path, content, branch, commit_message):
        """Create a file in the repository"""
        data = {
            'branch': branch,
            'content': content,
            'commit_message': commit_message,
            'author_email': 'demo@example.com',
            'author_name': 'Demo User'
        }
        
        response = requests.post(
            f'{self.base_url}/api/v4/projects/{project_id}/repository/files/{file_path}',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def create_merge_request(self, project_id, title, description, source_branch, target_branch):
        """Create a merge request"""
        data = {
            'title': title,
            'description': description,
            'source_branch': source_branch,
            'target_branch': target_branch,
            'assignee_id': 1  # Root user
        }
        
        response = requests.post(
            f'{self.base_url}/api/v4/projects/{project_id}/merge_requests',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def create_issue(self, project_id, title, description):
        """Create an issue"""
        data = {
            'title': title,
            'description': description,
            'assignee_id': 1,
            'labels': ['enhancement', 'demo']
        }
        
        response = requests.post(
            f'{self.base_url}/api/v4/projects/{project_id}/issues',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def setup_demo_resources(self):
        """Create all demo resources"""
        print("🎭 Creating GitLab Demo Resources via API")
        print("=" * 50)
        
        # Create projects
        projects = {}
        for name, desc in [
            ('mergemind-demo-frontend', 'Frontend application for MergeMind demo'),
            ('mergemind-demo-backend', 'Backend API for MergeMind demo'),
            ('mergemind-demo-api', 'API service for MergeMind demo')
        ]:
            print(f"📁 Creating project: {name}")
            project = self.create_project(name, desc)
            projects[name] = project
            print(f"   ✅ Created with ID: {project['id']}")
        
        # Create branches and files for each project
        demo_files = {
            'mergemind-demo-frontend': {
                'branch': 'feature/user-auth',
                'file': 'src/components/Auth.js',
                'content': '''import React, { useState } from 'react';

const Auth = () => {
  const [user, setUser] = useState(null);
  
  const handleLogin = async (credentials) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    if (response.ok) {
      const userData = await response.json();
      setUser(userData);
    }
  };

  return (
    <div className="auth-container">
      {user ? (
        <div>Welcome, {user.name}!</div>
      ) : (
        <form onSubmit={handleLogin}>
          <input type="email" placeholder="Email" />
          <input type="password" placeholder="Password" />
          <button type="submit">Login</button>
        </form>
      )}
    </div>
  );
};

export default Auth;''',
                'commit_msg': 'Add user authentication component'
            },
            'mergemind-demo-backend': {
                'branch': 'feature/jwt-auth',
                'file': 'src/auth/jwt.js',
                'content': '''const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

class AuthService {
  constructor() {
    this.secretKey = process.env.JWT_SECRET || 'demo-secret';
  }

  async generateToken(user) {
    return jwt.sign(
      { id: user.id, email: user.email, role: user.role },
      this.secretKey,
      { expiresIn: '24h' }
    );
  }

  async verifyToken(token) {
    try {
      return jwt.verify(token, this.secretKey);
    } catch (error) {
      throw new Error('Invalid token');
    }
  }
}

module.exports = new AuthService();''',
                'commit_msg': 'Implement JWT authentication service'
            },
            'mergemind-demo-api': {
                'branch': 'feature/auth-endpoints',
                'file': 'routes/auth.js',
                'content': '''const express = require('express');
const router = express.Router();
const AuthService = require('../services/auth');

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const isValid = await AuthService.comparePassword(password, user.passwordHash);
    if (!isValid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = await AuthService.generateToken(user);
    res.json({ token, user: { id: user.id, email: user.email } });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;''',
                'commit_msg': 'Add authentication API endpoints'
            }
        }
        
        merge_requests = {}
        for project_name, file_info in demo_files.items():
            project = projects[project_name]
            print(f"🌿 Creating branch: {file_info['branch']} in {project_name}")
            
            # Create branch
            self.create_branch(project['id'], file_info['branch'])
            
            # Create file
            print(f"📄 Creating file: {file_info['file']}")
            self.create_file(
                project['id'],
                file_info['file'],
                file_info['content'],
                file_info['branch'],
                file_info['commit_msg']
            )
            
            # Create merge request
            print(f"🔄 Creating merge request")
            mr = self.create_merge_request(
                project['id'],
                f"Add {file_info['branch'].replace('feature/', '').replace('-', ' ')}",
                f"Implements {file_info['branch'].replace('feature/', '').replace('-', ' ')} functionality",
                file_info['branch'],
                'main'
            )
            merge_requests[project_name] = mr
        
        # Create issues
        print("📋 Creating demo issues...")
        for project_name, project in projects.items():
            issue = self.create_issue(
                project['id'],
                f"Implement {project_name.split('-')[-1]} features",
                f"Add core functionality to {project_name}"
            )
            print(f"   ✅ Created issue #{issue['iid']} in {project_name}")
        
        print("\n✅ Demo resources created successfully!")
        print("\n📊 Summary:")
        print("=" * 30)
        
        project_ids = []
        for name, project in projects.items():
            print(f"Project: {name}")
            print(f"  ID: {project['id']}")
            print(f"  URL: {project['web_url']}")
            project_ids.append(str(project['id']))
        
        print(f"\nProject IDs for Fivetran: {', '.join(project_ids)}")
        
        return {
            'projects': projects,
            'merge_requests': merge_requests,
            'project_ids': project_ids
        }

if __name__ == "__main__":
    # Configuration - Set these values
    GITLAB_BASE_URL = "https://your-gitlab-domain.com"
    GITLAB_TOKEN = "your-token-here"  # Replace with your actual token
    
    if GITLAB_TOKEN == "your-token-here":
        print("❌ Please set your GitLab token in the script")
        print("   Edit the GITLAB_TOKEN variable with your actual token")
        exit(1)
    
    creator = GitLabDemoCreator(GITLAB_BASE_URL, GITLAB_TOKEN)
    creator.setup_demo_resources()
