#!/usr/bin/env python3
"""Populate GitLab demo projects with sample content"""

import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def create_file_in_project(base_url, token, project_id, file_path, content, branch="main", commit_message="Add sample file"):
    """Create a file in a GitLab project"""
    headers = {'Authorization': f'Bearer {token}'}
    
    data = {
        'branch': branch,
        'content': content,
        'commit_message': commit_message,
        'author_email': 'demo@mergemind.com',
        'author_name': 'Demo User'
    }
    
    url = f"{base_url}/api/v4/projects/{project_id}/repository/files/{file_path}"
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"SUCCESS Created {file_path} in project {project_id}")
        return True
    else:
        print(f"ERROR Failed to create {file_path}: {response.status_code} - {response.text}")
        return False

def create_branch(base_url, token, project_id, branch_name, ref="main"):
    """Create a new branch"""
    headers = {'Authorization': f'Bearer {token}'}
    
    data = {
        'branch': branch_name,
        'ref': ref
    }
    
    url = f"{base_url}/api/v4/projects/{project_id}/repository/branches"
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"SUCCESS Created branch {branch_name} in project {project_id}")
        return True
    else:
        print(f"ERROR Failed to create branch {branch_name}: {response.status_code} - {response.text}")
        return False

def create_merge_request(base_url, token, project_id, title, description, source_branch, target_branch="main"):
    """Create a merge request"""
    headers = {'Authorization': f'Bearer {token}'}
    
    data = {
        'title': title,
        'description': description,
        'source_branch': source_branch,
        'target_branch': target_branch,
        'assignee_id': 1  # Root user
    }
    
    url = f"{base_url}/api/v4/projects/{project_id}/merge_requests"
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        mr = response.json()
        print(f"SUCCESS Created MR '{title}' (ID: {mr['iid']}) in project {project_id}")
        return mr
    else:
        print(f"ERROR Failed to create MR '{title}': {response.status_code} - {response.text}")
        return None

def create_issue(base_url, token, project_id, title, description, labels=None):
    """Create an issue"""
    headers = {'Authorization': f'Bearer {token}'}
    
    data = {
        'title': title,
        'description': description,
        'assignee_id': 1,
        'labels': labels or ['enhancement', 'demo']
    }
    
    url = f"{base_url}/api/v4/projects/{project_id}/issues"
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        issue = response.json()
        print(f"SUCCESS Created issue '{title}' (ID: {issue['iid']}) in project {project_id}")
        return issue
    else:
        print(f"ERROR Failed to create issue '{title}': {response.status_code} - {response.text}")
        return None

def populate_projects():
    """Populate all demo projects with sample content"""
    
    base_url = os.getenv('GITLAB_BASE_URL')
    token = os.getenv('GITLAB_TOKEN')
    project_ids = os.getenv('GITLAB_PROJECT_IDS', '').split(',')
    
    if not all([base_url, token, project_ids]):
        print("ERROR Missing required environment variables")
        return False
    
    print(f"Populating GitLab projects: {project_ids}")
    print(f"Base URL: {base_url}")
    print()
    
    # Project configurations
    projects = {
        '4': {  # mergemind-demo-backend
            'name': 'mergemind-demo-backend',
            'files': {
                'README.md': '''# MergeMind Demo Backend

A Node.js backend service for the MergeMind demo application.

## Features

- JWT Authentication
- User Management
- API Endpoints
- Database Integration

## Getting Started

```bash
npm install
npm start
```

## API Endpoints

- POST /api/auth/login
- POST /api/auth/register
- GET /api/users
- POST /api/users

## Environment Variables

- JWT_SECRET
- DATABASE_URL
- PORT
''',
                'package.json': '''{
  "name": "mergemind-demo-backend",
  "version": "1.0.0",
  "description": "Backend API for MergeMind demo",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "jsonwebtoken": "^9.0.2",
    "bcrypt": "^5.1.1",
    "mongoose": "^7.5.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  }
}''',
                'server.js': '''const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});''',
                'routes/auth.js': '''const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

// Mock user database
const users = [
  {
    id: 1,
    email: 'admin@mergemind.com',
    password: '$2b$10$example.hash.here',
    name: 'Admin User'
  }
];

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    const user = users.find(u => u.email === email);
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // In a real app, you'd verify the password hash
    const isValid = password === 'demo123'; // Demo password
    if (!isValid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign(
      { id: user.id, email: user.email },
      process.env.JWT_SECRET || 'demo-secret',
      { expiresIn: '24h' }
    );

    res.json({ 
      token, 
      user: { id: user.id, email: user.email, name: user.name } 
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/auth/register
router.post('/register', async (req, res) => {
  try {
    const { email, password, name } = req.body;
    
    // Check if user already exists
    const existingUser = users.find(u => u.email === email);
    if (existingUser) {
      return res.status(400).json({ error: 'User already exists' });
    }

    const passwordHash = await bcrypt.hash(password, 10);
    const newUser = {
      id: users.length + 1,
      email,
      password: passwordHash,
      name
    };
    
    users.push(newUser);

    const token = jwt.sign(
      { id: newUser.id, email: newUser.email },
      process.env.JWT_SECRET || 'demo-secret',
      { expiresIn: '24h' }
    );

    res.status(201).json({ 
      token, 
      user: { id: newUser.id, email: newUser.email, name: newUser.name } 
    });
  } catch (error) {
    res.status(400).json({ error: 'Registration failed' });
  }
});

module.exports = router;'''
            },
            'branches': ['feature/user-auth', 'feature/api-endpoints'],
            'merge_requests': [
                {
                    'title': 'Implement JWT authentication service',
                    'description': '''## Summary
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

Closes #1''',
                    'source_branch': 'feature/user-auth'
                }
            ],
            'issues': [
                {
                    'title': 'Add JWT authentication service',
                    'description': 'Create authentication service with JWT token management for secure API access.',
                    'labels': ['enhancement', 'backend', 'auth', 'security']
                }
            ]
        },
        '5': {  # mergemind-demo-frontend
            'name': 'mergemind-demo-frontend',
            'files': {
                'README.md': '''# MergeMind Demo Frontend

A React frontend application for the MergeMind demo.

## Features

- User Authentication
- Dashboard
- Merge Request Management
- Real-time Updates

## Getting Started

```bash
npm install
npm start
```

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests

## Environment Variables

- REACT_APP_API_URL
- REACT_APP_VERSION''',
                'package.json': '''{
  "name": "mergemind-demo-frontend",
  "version": "1.0.0",
  "description": "Frontend application for MergeMind demo",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "axios": "^1.5.0",
    "@mui/material": "^5.14.0",
    "@mui/icons-material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "devDependencies": {
    "react-scripts": "5.0.1"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}''',
                'src/App.js': '''import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import MergeRequests from './components/MergeRequests';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/merge-requests" element={<MergeRequests />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;''',
                'src/components/Login.js': '''import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert
} from '@mui/material';
import axios from 'axios';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/auth/login', {
        email,
        password
      });

      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Invalid credentials. Use demo@mergemind.com / demo123');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            MergeMind Demo
          </Typography>
          <Typography variant="subtitle1" align="center" color="textSecondary" gutterBottom>
            Sign in to continue
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          
          <Typography variant="body2" align="center" color="textSecondary">
            Demo credentials: demo@mergemind.com / demo123
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;'''
            },
            'branches': ['feature/auth-component', 'feature/dashboard'],
            'merge_requests': [
                {
                    'title': 'Add user authentication component',
                    'description': '''## Summary
Implements JWT-based user authentication for the frontend application.

## Changes
- Added Login component with form validation
- Integrated with backend JWT API
- Added error handling and loading states
- Implemented token storage

## Testing
- [x] Login flow works correctly
- [x] Token storage and retrieval
- [x] Error handling
- [ ] Logout functionality

## Screenshots
![Login Component](https://via.placeholder.com/400x200)

Closes #1''',
                    'source_branch': 'feature/auth-component'
                }
            ],
            'issues': [
                {
                    'title': 'Implement user authentication',
                    'description': 'Need to add JWT-based authentication to the frontend application with login/logout functionality.',
                    'labels': ['enhancement', 'frontend', 'auth', 'ui']
                }
            ]
        },
        '6': {  # mergemind-demo-api
            'name': 'mergemind-demo-api',
            'files': {
                'README.md': '''# MergeMind Demo API

A comprehensive API service for the MergeMind demo application.

## Features

- RESTful API Design
- Authentication & Authorization
- Rate Limiting
- API Documentation
- Health Monitoring

## Getting Started

```bash
npm install
npm start
```

## API Documentation

Visit `/api/docs` for interactive API documentation.

## Endpoints

### Authentication
- POST /api/auth/login
- POST /api/auth/register
- POST /api/auth/refresh

### Users
- GET /api/users
- GET /api/users/:id
- PUT /api/users/:id

### Merge Requests
- GET /api/merge-requests
- POST /api/merge-requests
- GET /api/merge-requests/:id''',
                'package.json': '''{
  "name": "mergemind-demo-api",
  "version": "1.0.0",
  "description": "API service for MergeMind demo",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest",
    "docs": "swagger-jsdoc -d swaggerDef.js src/routes/*.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "express-rate-limit": "^6.10.0",
    "helmet": "^7.0.0",
    "cors": "^2.8.5",
    "swagger-jsdoc": "^6.2.8",
    "swagger-ui-express": "^5.0.0",
    "jsonwebtoken": "^9.0.2",
    "bcrypt": "^5.1.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  }
}''',
                'server.js': '''const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const mrRoutes = require('./routes/merge-requests');

const app = express();
const PORT = process.env.PORT || 3001;

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(limiter);
app.use(express.json());

// Swagger configuration
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'MergeMind Demo API',
      version: '1.0.0',
      description: 'API service for MergeMind demo application',
    },
    servers: [
      {
        url: `http://localhost:${PORT}`,
        description: 'Development server',
      },
    ],
  },
  apis: ['./routes/*.js'],
};

const specs = swaggerJsdoc(swaggerOptions);
app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(specs));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/merge-requests', mrRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'MergeMind Demo API',
    version: '1.0.0',
    docs: '/api/docs'
  });
});

app.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`);
  console.log(`API documentation available at http://localhost:${PORT}/api/docs`);
});''',
                'routes/merge-requests.js': '''const express = require('express');
const router = express.Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     MergeRequest:
 *       type: object
 *       required:
 *         - title
 *         - description
 *         - source_branch
 *         - target_branch
 *       properties:
 *         id:
 *           type: integer
 *           description: The auto-generated id of the merge request
 *         title:
 *           type: string
 *           description: The title of the merge request
 *         description:
 *           type: string
 *           description: The description of the merge request
 *         source_branch:
 *           type: string
 *           description: The source branch name
 *         target_branch:
 *           type: string
 *           description: The target branch name
 *         status:
 *           type: string
 *           enum: [open, merged, closed]
 *           description: The status of the merge request
 */

/**
 * @swagger
 * /api/merge-requests:
 *   get:
 *     summary: Get all merge requests
 *     tags: [Merge Requests]
 *     responses:
 *       200:
 *         description: List of merge requests
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/MergeRequest'
 */
router.get('/', (req, res) => {
  const mergeRequests = [
    {
      id: 1,
      title: 'Add user authentication',
      description: 'Implement JWT-based authentication system',
      source_branch: 'feature/auth',
      target_branch: 'main',
      status: 'open',
      author: 'John Doe',
      created_at: '2025-10-09T10:00:00Z'
    },
    {
      id: 2,
      title: 'Update dashboard UI',
      description: 'Improve the dashboard user interface',
      source_branch: 'feature/dashboard-ui',
      target_branch: 'main',
      status: 'merged',
      author: 'Jane Smith',
      created_at: '2025-10-08T15:30:00Z'
    }
  ];
  
  res.json(mergeRequests);
});

/**
 * @swagger
 * /api/merge-requests/{id}:
 *   get:
 *     summary: Get merge request by ID
 *     tags: [Merge Requests]
 *     parameters:
 *       - in: path
 *         name: id
 *         schema:
 *           type: integer
 *         required: true
 *         description: The merge request ID
 *     responses:
 *       200:
 *         description: The merge request
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/MergeRequest'
 *       404:
 *         description: Merge request not found
 */
router.get('/:id', (req, res) => {
  const { id } = req.params;
  const mergeRequest = {
    id: parseInt(id),
    title: 'Add user authentication',
    description: 'Implement JWT-based authentication system',
    source_branch: 'feature/auth',
    target_branch: 'main',
    status: 'open',
    author: 'John Doe',
    created_at: '2025-10-09T10:00:00Z'
  };
  
  res.json(mergeRequest);
});

module.exports = router;'''
            },
            'branches': ['feature/api-docs', 'feature/rate-limiting'],
            'merge_requests': [
                {
                    'title': 'Add API documentation with Swagger',
                    'description': '''## Summary
Implements comprehensive API documentation using Swagger/OpenAPI.

## Changes
- Added Swagger JSDoc configuration
- Documented all API endpoints
- Added interactive API documentation at /api/docs
- Included request/response schemas

## Features
- Interactive API explorer
- Request/response examples
- Authentication documentation
- Error response schemas

## Testing
- [x] Swagger UI loads correctly
- [x] All endpoints documented
- [x] Schema validation works
- [ ] Add more detailed examples

Closes #1''',
                    'source_branch': 'feature/api-docs'
                }
            ],
            'issues': [
                {
                    'title': 'Create comprehensive API documentation',
                    'description': 'Need to add Swagger/OpenAPI documentation for all API endpoints to improve developer experience.',
                    'labels': ['enhancement', 'api', 'documentation', 'developer-experience']
                }
            ]
        }
    }
    
    # Populate each project
    for project_id in project_ids:
        project_id = project_id.strip()
        if not project_id or project_id not in projects:
            continue
            
        project_config = projects[project_id]
        print(f"\n=== Populating Project {project_id}: {project_config['name']} ===")
        
        # Create files in main branch
        for file_path, content in project_config['files'].items():
            create_file_in_project(base_url, token, project_id, file_path, content)
        
        # Create feature branches
        for branch in project_config['branches']:
            create_branch(base_url, token, project_id, branch)
            
            # Add a file to the feature branch
            feature_file = f"feature-{branch.replace('feature/', '')}.md"
            feature_content = f"# {branch.replace('feature/', '').replace('-', ' ').title()}\n\nThis is a feature branch for {project_config['name']}.\n\n## Changes\n- Feature implementation\n- Bug fixes\n- Improvements"
            create_file_in_project(base_url, token, project_id, feature_file, feature_content, branch, f"Add {branch} feature")
        
        # Create merge requests
        for mr in project_config['merge_requests']:
            create_merge_request(base_url, token, project_id, mr['title'], mr['description'], mr['source_branch'])
        
        # Create issues
        for issue in project_config['issues']:
            create_issue(base_url, token, project_id, issue['title'], issue['description'], issue['labels'])
    
    print("\n=== Population Complete ===")
    print("All projects have been populated with sample content!")
    print("You can now:")
    print("1. Visit the GitLab web interface to see the projects")
    print("2. Test the Fivetran connector with real data")
    print("3. Run MergeMind API to analyze the merge requests")

if __name__ == "__main__":
    populate_projects()
