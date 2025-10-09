# GitLab Demo Resources Terraform Configuration
# This creates demo projects, branches, commits, and merge requests

terraform {
  required_providers {
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "~> 16.0"
    }
  }
}

# Configure GitLab Provider
provider "gitlab" {
  token    = var.gitlab_token
  base_url = var.gitlab_base_url
}

# Demo Projects
resource "gitlab_project" "demo_frontend" {
  name                   = "mergemind-demo-frontend"
  description            = "Frontend application for MergeMind demo"
  visibility_level       = "private"
  default_branch         = "main"
  issues_enabled         = true
  merge_requests_enabled  = true
  wiki_enabled           = false
  snippets_enabled       = false
  container_registry_enabled = true
}

resource "gitlab_project" "demo_backend" {
  name                   = "mergemind-demo-backend"
  description            = "Backend API for MergeMind demo"
  visibility_level       = "private"
  default_branch         = "main"
  issues_enabled         = true
  merge_requests_enabled  = true
  wiki_enabled           = false
  snippets_enabled       = false
  container_registry_enabled = true
}

resource "gitlab_project" "demo_api" {
  name                   = "mergemind-demo-api"
  description            = "API service for MergeMind demo"
  visibility_level       = "private"
  default_branch         = "main"
  issues_enabled         = true
  merge_requests_enabled  = true
  wiki_enabled           = false
  snippets_enabled       = false
  container_registry_enabled = true
}

# Demo Branches (created via repository files)
resource "gitlab_repository_file" "frontend_feature_branch" {
  project        = gitlab_project.demo_frontend.id
  file_path      = "src/components/Auth.js"
  branch         = "feature/user-auth"
  content        = base64encode(<<-EOF
import React, { useState } from 'react';

const Auth = () => {
  const [user, setUser] = useState(null);
  
  const handleLogin = async (credentials) => {
    // JWT authentication implementation
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

export default Auth;
EOF
  )
  commit_message = "Add user authentication component"
  author_email   = var.demo_user_email
  author_name    = var.demo_user_name
}

resource "gitlab_repository_file" "backend_feature_branch" {
  project        = gitlab_project.demo_backend.id
  file_path      = "src/auth/jwt.js"
  branch         = "feature/jwt-auth"
  content        = base64encode(<<-EOF
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

class AuthService {
  constructor() {
    this.secretKey = process.env.JWT_SECRET || 'demo-secret';
  }

  async generateToken(user) {
    return jwt.sign(
      { 
        id: user.id, 
        email: user.email,
        role: user.role 
      },
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

  async hashPassword(password) {
    return bcrypt.hash(password, 10);
  }

  async comparePassword(password, hash) {
    return bcrypt.compare(password, hash);
  }
}

module.exports = new AuthService();
EOF
  )
  commit_message = "Implement JWT authentication service"
  author_email   = var.demo_user_email
  author_name    = var.demo_user_name
}

resource "gitlab_repository_file" "api_feature_branch" {
  project        = gitlab_project.demo_api.id
  file_path      = "routes/auth.js"
  branch         = "feature/auth-endpoints"
  content        = base64encode(<<-EOF
const express = require('express');
const router = express.Router();
const AuthService = require('../services/auth');

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    // Validate credentials
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

// POST /api/auth/register
router.post('/register', async (req, res) => {
  try {
    const { email, password, name } = req.body;
    
    const passwordHash = await AuthService.hashPassword(password);
    const user = await User.create({ email, passwordHash, name });
    
    const token = await AuthService.generateToken(user);
    res.status(201).json({ token, user: { id: user.id, email: user.email } });
  } catch (error) {
    res.status(400).json({ error: 'Registration failed' });
  }
});

module.exports = router;
EOF
  )
  commit_message = "Add authentication API endpoints"
  author_email   = var.demo_user_email
  author_name    = var.demo_user_name
}

# Demo Merge Requests
resource "gitlab_project_push_rules" "frontend_push_rules" {
  project_id = gitlab_project.demo_frontend.id
}

resource "gitlab_merge_request" "frontend_auth_mr" {
  project_id = gitlab_project.demo_frontend.id
  title      = "Add user authentication component"
  description = <<-EOF
## Summary
Implements JWT-based user authentication for the frontend application.

## Changes
- Added Auth component with login/logout functionality
- Integrated with backend JWT API
- Added form validation and error handling

## Testing
- [x] Login flow works correctly
- [x] Token storage and retrieval
- [x] Logout functionality
- [ ] Error handling edge cases

## Screenshots
![Auth Component](https://via.placeholder.com/400x200)

Closes #1
EOF
  source_branch = "feature/user-auth"
  target_branch = "main"
  assignee_id   = 1  # Root user
  reviewer_ids  = [1]
  
  depends_on = [gitlab_repository_file.frontend_feature_branch]
}

resource "gitlab_merge_request" "backend_auth_mr" {
  project_id = gitlab_project.demo_backend.id
  title      = "Implement JWT authentication service"
  description = <<-EOF
## Summary
Adds JWT-based authentication service to the backend.

## Changes
- Created AuthService class with JWT operations
- Added password hashing with bcrypt
- Implemented token generation and verification

## Security Considerations
- Uses environment variables for secret key
- Implements proper password hashing
- Token expiration set to 24 hours

## Testing
- [x] Token generation
- [x] Token verification
- [x] Password hashing/verification
- [ ] Integration tests

Closes #2
EOF
  source_branch = "feature/jwt-auth"
  target_branch = "main"
  assignee_id   = 1
  reviewer_ids  = [1]
  
  depends_on = [gitlab_repository_file.backend_feature_branch]
}

resource "gitlab_merge_request" "api_auth_mr" {
  project_id = gitlab_project.demo_api.id
  title      = "Add authentication API endpoints"
  description = <<-EOF
## Summary
Implements REST API endpoints for user authentication.

## Endpoints Added
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

## Request/Response Examples

### Login
```json
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { "id": 1, "email": "user@example.com" }
}
```

## Testing
- [x] Login endpoint
- [x] Registration endpoint
- [x] Error handling
- [ ] Rate limiting

Closes #3
EOF
  source_branch = "feature/auth-endpoints"
  target_branch = "main"
  assignee_id   = 1
  reviewer_ids  = [1]
  
  depends_on = [gitlab_repository_file.api_feature_branch]
}

# Demo Issues
resource "gitlab_issue" "frontend_auth_issue" {
  project_id = gitlab_project.demo_frontend.id
  title      = "Implement user authentication"
  description = "Need to add JWT-based authentication to the frontend application"
  assignee_id = 1
  labels     = ["enhancement", "frontend", "auth"]
}

resource "gitlab_issue" "backend_auth_issue" {
  project_id = gitlab_project.demo_backend.id
  title      = "Add JWT authentication service"
  description = "Create authentication service with JWT token management"
  assignee_id = 1
  labels     = ["enhancement", "backend", "auth"]
}

resource "gitlab_issue" "api_auth_issue" {
  project_id = gitlab_project.demo_api.id
  title      = "Create authentication API endpoints"
  description = "Implement REST API endpoints for login and registration"
  assignee_id = 1
  labels     = ["enhancement", "api", "auth"]
}
