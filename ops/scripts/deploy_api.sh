#!/bin/bash

# Deploy MergeMind API to Google Cloud Run
# This script builds and deploys the API service

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
SERVICE_NAME="mergemind-api"
REGION=${VERTEX_LOCATION:-"us-central1"}
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Deploying MergeMind API to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Image: $IMAGE_NAME"

# Check if gcloud command is available
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud command not found. Please install Google Cloud SDK."
    exit 1
fi

# Check if docker command is available
if ! command -v docker &> /dev/null; then
    echo "Error: docker command not found. Please install Docker."
    exit 1
fi

# Set project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push Docker image
echo "Building Docker image..."
docker build -f ops/docker/api.Dockerfile -t $IMAGE_NAME .

echo "Pushing image to Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,BQ_DATASET_RAW=mergemind_raw,BQ_DATASET_MODELED=mergemind,VERTEX_LOCATION=$REGION" \
    --set-secrets "GITLAB_TOKEN=gitlab-token:latest"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "Deployment completed successfully!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "Health check: $SERVICE_URL/api/v1/healthz"
echo "API docs: $SERVICE_URL/docs"
echo ""
echo "To update environment variables or secrets:"
echo "  gcloud run services update $SERVICE_NAME --region=$REGION --update-env-vars KEY=VALUE"
echo "  gcloud run services update $SERVICE_NAME --region=$REGION --update-secrets KEY=SECRET_NAME:VERSION"
