#!/bin/bash

# Setup Terraform GCS Backend
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🗄️  Setting up Terraform GCS Backend${NC}"
echo "=================================="

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project set${NC}"
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${BLUE}📁 Using GCP project: ${PROJECT_ID}${NC}"

# Set bucket name
BUCKET_NAME="terraform-state-${PROJECT_ID}"
echo -e "${YELLOW}📦 Terraform state bucket: ${BUCKET_NAME}${NC}"

# Check if bucket exists
if gsutil ls -b "gs://${BUCKET_NAME}" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Bucket already exists: gs://${BUCKET_NAME}${NC}"
else
    echo -e "${YELLOW}🔨 Creating GCS bucket for Terraform state...${NC}"
    
    # Create bucket with versioning and lifecycle
    gsutil mb -p "${PROJECT_ID}" -c STANDARD -l us-central1 "gs://${BUCKET_NAME}"
    
    # Enable versioning
    gsutil versioning set on "gs://${BUCKET_NAME}"
    
    # Set lifecycle policy (keep 30 days of versions)
    cat > lifecycle.json <<EOF
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 30}
    }
  ]
}
EOF
    gsutil lifecycle set lifecycle.json "gs://${BUCKET_NAME}"
    rm lifecycle.json
    
    echo -e "${GREEN}✅ Created bucket: gs://${BUCKET_NAME}${NC}"
fi

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable storage.googleapis.com --project="${PROJECT_ID}"
gcloud services enable storage-component.googleapis.com --project="${PROJECT_ID}"

echo -e "${GREEN}✅ Terraform backend setup complete!${NC}"
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Run: terraform init"
echo "2. Run: terraform plan"
echo "3. Run: terraform apply"
echo ""
echo -e "${YELLOW}💡 The state will be stored in: gs://${BUCKET_NAME}/gitlab-infrastructure${NC}"
