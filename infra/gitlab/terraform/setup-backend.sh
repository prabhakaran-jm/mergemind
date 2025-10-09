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

# Set project ID (force to use ai-accelerate-mergemind)
PROJECT_ID="ai-accelerate-mergemind"
echo -e "${YELLOW}🔧 Setting project to: ${PROJECT_ID}${NC}"
gcloud config set project "${PROJECT_ID}"

echo -e "${BLUE}📁 Using GCP project: ${PROJECT_ID}${NC}"

# Set bucket name
BUCKET_NAME="terraform-state-${PROJECT_ID}"
echo -e "${YELLOW}📦 Terraform state bucket: ${BUCKET_NAME}${NC}"

# Check if bucket exists using gcloud
if gcloud storage buckets describe "gs://${BUCKET_NAME}" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Bucket already exists: gs://${BUCKET_NAME}${NC}"
else
    echo -e "${YELLOW}🔨 Creating GCS bucket for Terraform state...${NC}"
    
    # Create bucket with versioning and lifecycle using gcloud
    gcloud storage buckets create "gs://${BUCKET_NAME}" \
        --project="${PROJECT_ID}" \
        --location=us-central1 \
        --default-storage-class=STANDARD
    
    # Enable versioning
    gcloud storage buckets update "gs://${BUCKET_NAME}" --versioning
    
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
    gcloud storage buckets update "gs://${BUCKET_NAME}" --lifecycle-file=lifecycle.json
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
