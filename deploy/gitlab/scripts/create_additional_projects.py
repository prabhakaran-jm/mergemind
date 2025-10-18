#!/usr/bin/env python3
"""
Extended GitLab Manager - Add more projects for testing
This shows how to extend the base gitlab_manager.py with additional projects
"""

import requests
import os
from typing import Dict, List, Optional
from gitlab_manager import GitLabManager, get_project_templates

# Configuration
GITLAB_BASE_URL = os.getenv('GITLAB_BASE_URL')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')

# Validate required environment variables
if not GITLAB_BASE_URL:
    raise ValueError("GITLAB_BASE_URL environment variable is required")
if not GITLAB_TOKEN:
    raise ValueError("GITLAB_TOKEN environment variable is required")

def get_additional_project_templates() -> Dict[str, Dict]:
    """Get additional project templates for more diverse testing"""
    return {
        'mergemind-security-service': {
            'description': 'Security service with authentication, authorization, and audit logging',
            'files': {
                'README.md': '''# MergeMind Security Service

A comprehensive security service handling authentication, authorization, and audit logging.

## Features
- JWT-based authentication
- Role-based access control (RBAC)
- Audit logging and compliance
- Security monitoring
- Rate limiting and DDoS protection

## Getting Started
```bash
npm install
npm run migrate
npm start
```

## Environment Variables
- JWT_SECRET
- DATABASE_URL
- REDIS_URL
- AUDIT_LOG_LEVEL
''',
                'package.json': '''{
  "name": "mergemind-security-service",
  "version": "1.0.0",
  "description": "Security service for MergeMind",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "migrate": "node migrations/migrate.js",
    "test": "jest",
    "audit": "npm audit"
  },
  "dependencies": {
    "express": "^4.18.2",
    "jsonwebtoken": "^9.0.2",
    "bcrypt": "^5.1.1",
    "express-rate-limit": "^6.10.0",
    "helmet": "^7.0.0",
    "winston": "^3.10.0",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  }
}''',
                'server.js': '''const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const winston = require('winston');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3005;

// Security middleware
app.use(helmet());
app.use(rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
}));

// Logger setup
const logger = winston.createLogger({
  level: process.env.AUDIT_LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'audit.log' }),
    new winston.transports.Console()
  ]
});

// Middleware
app.use(express.json());

// Security audit middleware
app.use((req, res, next) => {
  logger.info({
    timestamp: new Date().toISOString(),
    method: req.method,
    url: req.url,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });
  next();
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    security: 'enabled',
    audit: 'active',
    timestamp: new Date().toISOString()
  });
});

// Authentication endpoint
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    // In production, validate against database
    if (email === 'admin@mergemind.com' && password === 'secure123') {
      const token = jwt.sign(
        { email, role: 'admin' },
        process.env.JWT_SECRET || 'fallback-secret',
        { expiresIn: '1h' }
      );
      
      logger.info(`Successful login for ${email}`);
      res.json({ token, user: { email, role: 'admin' } });
    } else {
      logger.warn(`Failed login attempt for ${email}`);
      res.status(401).json({ error: 'Invalid credentials' });
    }
  } catch (error) {
    logger.error(`Login error: ${error.message}`);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.listen(PORT, () => {
  console.log(`Security service running on port ${PORT}`);
  logger.info(`Security service started on port ${PORT}`);
});'''
            },
            'branches': ['feature/rbac-implementation', 'feature/audit-logging'],
            'merge_requests': [
                {
                    'title': 'Implement Role-Based Access Control (RBAC)',
                    'description': '''## Summary
Implements comprehensive Role-Based Access Control system with fine-grained permissions.

## Changes
- Added RBAC middleware for route protection
- Implemented permission-based access control
- Created role hierarchy (admin > manager > user)
- Added permission inheritance
- Implemented resource-level permissions

## Security Features
- Hierarchical role system
- Permission inheritance
- Resource-level access control
- Dynamic permission checking
- Audit trail for all access attempts

## Roles Implemented
- **Admin**: Full system access
- **Manager**: Project and team management
- **Developer**: Code and MR access
- **Viewer**: Read-only access

## Testing
- [x] Role hierarchy works correctly
- [x] Permission inheritance functions
- [x] Resource-level access control
- [x] Audit logging captures access attempts
- [ ] Load testing with multiple roles

## Security Considerations
- All access attempts are logged
- Failed authorization attempts trigger alerts
- Role changes require admin approval
- Permission changes are audited

Closes #2''',
                    'source_branch': 'feature/rbac-implementation'
                }
            ]
        },
        'mergemind-monitoring-service': {
            'description': 'Monitoring service with metrics collection, alerting, and dashboards',
            'files': {
                'README.md': '''# MergeMind Monitoring Service

A comprehensive monitoring service with metrics collection, alerting, and dashboard capabilities.

## Features
- Real-time metrics collection
- Custom dashboards
- Alert management
- Performance monitoring
- Health checks and uptime tracking

## Getting Started
```bash
npm install
npm start
```

## Environment Variables
- PROMETHEUS_URL
- GRAFANA_URL
- ALERT_WEBHOOK_URL
- METRICS_RETENTION_DAYS
''',
                'package.json': '''{
  "name": "mergemind-monitoring-service",
  "version": "1.0.0",
  "description": "Monitoring service for MergeMind",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest",
    "metrics": "node scripts/collect-metrics.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "prom-client": "^15.0.0",
    "node-cron": "^3.0.2",
    "axios": "^1.5.0",
    "ws": "^8.14.0",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  }
}''',
                'server.js': '''const express = require('express');
const client = require('prom-client');
const cron = require('node-cron');
const WebSocket = require('ws');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3006;

// Prometheus metrics
const register = new client.Registry();
client.collectDefaultMetrics({ register });

// Custom metrics
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10]
});

const activeConnections = new client.Gauge({
  name: 'websocket_active_connections',
  help: 'Number of active WebSocket connections'
});

register.registerMetric(httpRequestDuration);
register.registerMetric(activeConnections);

// Middleware
app.use(express.json());

// Metrics middleware
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequestDuration
      .labels(req.method, req.route?.path || req.path, res.statusCode)
      .observe(duration);
  });
  
  next();
});

// WebSocket server for real-time metrics
const wss = new WebSocket.Server({ port: 8080 });
let connections = 0;

wss.on('connection', (ws) => {
  connections++;
  activeConnections.set(connections);
  
  ws.on('close', () => {
    connections--;
    activeConnections.set(connections);
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    metrics: 'active',
    websocket_connections: connections,
    timestamp: new Date().toISOString()
  });
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// Dashboard endpoint
app.get('/api/dashboard', (req, res) => {
  res.json({
    metrics: {
      http_requests: 'active',
      websocket_connections: connections,
      uptime: process.uptime(),
      memory_usage: process.memoryUsage()
    },
    alerts: [],
    last_updated: new Date().toISOString()
  });
});

// Scheduled metrics collection
cron.schedule('*/5 * * * *', () => {
  console.log('Collecting system metrics...');
  // In production, collect from various services
});

app.listen(PORT, () => {
  console.log(`Monitoring service running on port ${PORT}`);
  console.log(`WebSocket server running on port 8080`);
  console.log(`Metrics available at http://localhost:${PORT}/metrics`);
});'''
            },
            'branches': ['feature/custom-dashboards', 'feature/alert-management'],
            'merge_requests': [
                {
                    'title': 'Add custom dashboard builder with real-time updates',
                    'description': '''## Summary
Implements a custom dashboard builder with real-time metrics updates and interactive widgets.

## Changes
- Added dashboard builder interface
- Implemented real-time WebSocket updates
- Created customizable widget system
- Added drag-and-drop dashboard layout
- Implemented dashboard sharing and permissions

## Dashboard Features
- Real-time metrics visualization
- Customizable widget library
- Drag-and-drop interface
- Dashboard templates
- Export/import functionality
- Collaborative editing

## Widget Types
- **Charts**: Line, bar, pie, gauge charts
- **Tables**: Data tables with sorting/filtering
- **Alerts**: Alert status and history
- **KPIs**: Key performance indicators
- **Maps**: Geographic data visualization

## Real-time Updates
- WebSocket-based live updates
- Configurable update intervals
- Efficient data streaming
- Connection management
- Fallback to polling

## Testing
- [x] Dashboard creation and editing
- [x] Real-time updates work correctly
- [x] Widget rendering and interaction
- [x] Dashboard sharing functionality
- [ ] Performance testing with multiple dashboards

## User Experience
- Intuitive drag-and-drop interface
- Responsive design for all devices
- Keyboard shortcuts for power users
- Undo/redo functionality
- Auto-save capabilities

Closes #3''',
                    'source_branch': 'feature/custom-dashboards'
                }
            ]
        },
        'mergemind-integration-service': {
            'description': 'Integration service for third-party APIs and webhooks',
            'files': {
                'README.md': '''# MergeMind Integration Service

A service for managing third-party integrations, webhooks, and API connections.

## Features
- Third-party API integrations
- Webhook management
- Data transformation and mapping
- Error handling and retry logic
- Integration monitoring and logging

## Getting Started
```bash
npm install
npm start
```

## Environment Variables
- WEBHOOK_SECRET
- API_RATE_LIMIT
- RETRY_ATTEMPTS
- TIMEOUT_MS
''',
                'package.json': '''{
  "name": "mergemind-integration-service",
  "version": "1.0.0",
  "description": "Integration service for MergeMind",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest",
    "webhook": "node scripts/test-webhook.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "axios": "^1.5.0",
    "node-cron": "^3.0.2",
    "crypto": "^1.0.1",
    "joi": "^17.9.0",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2"
  }
}''',
                'server.js': '''const express = require('express');
const axios = require('axios');
const crypto = require('crypto');
const Joi = require('joi');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3007;

// Webhook validation middleware
const validateWebhook = (req, res, next) => {
  const signature = req.headers['x-webhook-signature'];
  const payload = JSON.stringify(req.body);
  const expectedSignature = crypto
    .createHmac('sha256', process.env.WEBHOOK_SECRET || 'default-secret')
    .update(payload)
    .digest('hex');
  
  if (signature !== expectedSignature) {
    return res.status(401).json({ error: 'Invalid webhook signature' });
  }
  
  next();
};

// Middleware
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    integrations: 'active',
    webhooks: 'enabled',
    timestamp: new Date().toISOString()
  });
});

// Webhook endpoint
app.post('/webhooks/gitlab', validateWebhook, async (req, res) => {
  try {
    const { object_kind, project, merge_request } = req.body;
    
    console.log(`Received ${object_kind} webhook from GitLab`);
    
    if (object_kind === 'merge_request') {
      // Process merge request webhook
      await processMergeRequestWebhook(merge_request, project);
    }
    
    res.json({ status: 'processed' });
  } catch (error) {
    console.error('Webhook processing error:', error);
    res.status(500).json({ error: 'Webhook processing failed' });
  }
});

// Integration endpoints
app.post('/api/integrations/:service', async (req, res) => {
  try {
    const { service } = req.params;
    const config = req.body;
    
    // Validate integration configuration
    const schema = Joi.object({
      apiKey: Joi.string().required(),
      baseUrl: Joi.string().uri().required(),
      timeout: Joi.number().default(5000)
    });
    
    const { error, value } = schema.validate(config);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }
    
    // Test the integration
    const testResult = await testIntegration(service, value);
    
    res.json({ 
      status: 'success', 
      service,
      testResult 
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

async function processMergeRequestWebhook(mr, project) {
  console.log(`Processing MR ${mr.iid} in project ${project.name}`);
  // In production, trigger AI analysis, notifications, etc.
}

async function testIntegration(service, config) {
  try {
    const response = await axios.get(`${config.baseUrl}/health`, {
      headers: { 'Authorization': `Bearer ${config.apiKey}` },
      timeout: config.timeout
    });
    
    return {
      status: 'connected',
      responseTime: response.headers['x-response-time'] || 'unknown',
      version: response.data.version || 'unknown'
    };
  } catch (error) {
    throw new Error(`Integration test failed: ${error.message}`);
  }
}

app.listen(PORT, () => {
  console.log(`Integration service running on port ${PORT}`);
  console.log(`Webhook endpoint: http://localhost:${PORT}/webhooks/gitlab`);
});'''
            },
            'branches': ['feature/webhook-management', 'feature/api-integrations'],
            'merge_requests': [
                {
                    'title': 'Implement comprehensive webhook management system',
                    'description': '''## Summary
Implements a robust webhook management system with validation, retry logic, and monitoring.

## Changes
- Added webhook signature validation
- Implemented retry mechanism with exponential backoff
- Created webhook event filtering
- Added webhook delivery monitoring
- Implemented webhook testing and debugging tools

## Webhook Features
- **Security**: HMAC signature validation
- **Reliability**: Retry logic with exponential backoff
- **Monitoring**: Delivery status tracking
- **Filtering**: Event type and condition filtering
- **Testing**: Webhook testing and debugging tools

## Retry Logic
- Exponential backoff (1s, 2s, 4s, 8s, 16s)
- Maximum 5 retry attempts
- Dead letter queue for failed webhooks
- Manual retry capability
- Delivery status notifications

## Monitoring
- Webhook delivery metrics
- Success/failure rates
- Average delivery time
- Error categorization
- Alert on high failure rates

## Testing
- [x] Webhook signature validation
- [x] Retry mechanism works correctly
- [x] Event filtering functions
- [x] Delivery monitoring tracks status
- [ ] Load testing with high webhook volume

## Debugging Tools
- Webhook payload inspection
- Delivery attempt history
- Error message categorization
- Test webhook functionality
- Webhook replay capability

Closes #4''',
                    'source_branch': 'feature/webhook-management'
                }
            ]
        }
    }

def create_additional_projects():
    """Create additional GitLab projects for more comprehensive testing"""
    print("🚀 Creating Additional GitLab Projects for Testing")
    print(f"Base URL: {GITLAB_BASE_URL}")
    print()
    
    # Initialize GitLab manager
    gitlab = GitLabManager(GITLAB_BASE_URL, GITLAB_TOKEN)
    
    # Get additional project templates
    templates = get_additional_project_templates()
    
    created_projects = []
    
    # Create additional projects
    for project_name, config in templates.items():
        print(f"\n=== Creating Additional Project: {project_name} ===")
        
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
    
    print(f"\n=== Additional Projects Created ===")
    print(f"Created {len(created_projects)} additional projects:")
    
    for project in created_projects:
        print(f"  - {project['name']} (ID: {project['id']})")
        print(f"    URL: {project['web_url']}")
    
    print(f"\nTotal projects now available:")
    print(f"  - Original projects: mergemind-demo-backend (4), mergemind-demo-frontend (5), mergemind-demo-api (6)")
    print(f"  - Database projects: mergemind-database-service (7), mergemind-notification-service (8), mergemind-analytics-service (9)")
    print(f"  - Additional projects:")
    for project in created_projects:
        print(f"    - {project['name']} (ID: {project['id']})")
    
    print(f"\nNext steps:")
    print(f"1. Update config.env with new project IDs")
    print(f"2. Fivetran will automatically discover new projects")
    print(f"3. Wait for data sync to BigQuery")
    print(f"4. Test AI analysis with diverse project types")

if __name__ == "__main__":
    create_additional_projects()
