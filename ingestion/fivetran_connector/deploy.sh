#!/bin/bash

# GitLab Fivetran Connector Deployment Script
set -e

# Configuration
CONNECTOR_NAME="gitlab-connector"
REGION="us-central1"
PROJECT_ID="${GCP_PROJECT_ID}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying GitLab Fivetran Connector${NC}"

# Check required environment variables
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}❌ GCP_PROJECT_ID is required${NC}"
    exit 1
fi

if [ -z "$GITLAB_TOKEN" ]; then
    echo -e "${RED}❌ GITLAB_TOKEN is required${NC}"
    exit 1
fi

# Set default values
GITLAB_BASE_URL="${GITLAB_BASE_URL:-https://gitlab.com}"
GITLAB_PROJECT_IDS="${GITLAB_PROJECT_IDS:-100,101,102}"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  GitLab Base URL: $GITLAB_BASE_URL"
echo "  Project IDs: $GITLAB_PROJECT_IDS"

# Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t gcr.io/$PROJECT_ID/$CONNECTOR_NAME:latest .

# Push to Google Container Registry
echo -e "${YELLOW}📤 Pushing to GCR...${NC}"
docker push gcr.io/$PROJECT_ID/$CONNECTOR_NAME:latest

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $CONNECTOR_NAME \
    --image gcr.io/$PROJECT_ID/$CONNECTOR_NAME:latest \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10 \
    --set-env-vars "GITLAB_BASE_URL=$GITLAB_BASE_URL,GITLAB_PROJECT_IDS=$GITLAB_PROJECT_IDS" \
    --set-secrets "GITLAB_TOKEN=gitlab-token:latest" \
    --allow-unauthenticated

# Get service URL
SERVICE_URL=$(gcloud run services describe $CONNECTOR_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --format 'value(status.url)')

echo -e "${GREEN}✅ Connector deployed successfully!${NC}"
echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "  1. Configure Fivetran to use this connector"
echo "  2. Set up monitoring and alerting"
echo "  3. Test data sync with your GitLab projects"
