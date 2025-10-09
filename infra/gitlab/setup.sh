#!/bin/bash

# GitLab Infrastructure Setup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 GitLab Infrastructure Setup${NC}"
echo "=================================="

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    echo "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ terraform is not installed${NC}"
    echo "Please install terraform: https://www.terraform.io/downloads"
    exit 1
fi

# Check if authenticated with gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with gcloud${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project set${NC}"
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${BLUE}📁 Using GCP project: ${PROJECT_ID}${NC}"

# Navigate to terraform directory
cd terraform

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}📝 Creating terraform.tfvars...${NC}"
    cp terraform.tfvars.example terraform.tfvars
    sed -i "s/YOUR_GCP_PROJECT_ID/${PROJECT_ID}/g" terraform.tfvars
    echo -e "${GREEN}✅ Created terraform.tfvars with project ID${NC}"
fi

# Initialize terraform
echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
terraform init

# Plan deployment
echo -e "${YELLOW}📋 Planning deployment...${NC}"
terraform plan

# Ask for confirmation
echo -e "${YELLOW}❓ Do you want to proceed with the deployment? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏹️  Deployment cancelled${NC}"
    exit 0
fi

# Apply terraform
echo -e "${YELLOW}🚀 Deploying infrastructure...${NC}"
terraform apply -auto-approve

# Get outputs
echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
echo -e "${BLUE}📊 Deployment outputs:${NC}"
terraform output

# Get values for bootstrap
IP=$(terraform output -raw gitlab_external_ip)
HOST=$(terraform output -raw suggested_gitlab_host)

echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Copy bootstrap script to VM:"
echo "   gcloud compute scp ../scripts/bootstrap-gitlab.sh gitlab-ce:~/"
echo ""
echo "2. Run bootstrap script:"
echo "   gcloud compute ssh gitlab-ce --command \"chmod +x ~/bootstrap-gitlab.sh && sudo ./bootstrap-gitlab.sh --host '${HOST}' --tls letsencrypt --email 'your-email@example.com'\""
echo ""
echo "3. Access GitLab:"
echo "   https://${HOST}"
echo ""
echo "4. Get initial password:"
echo "   gcloud compute ssh gitlab-ce --command \"sudo cat /etc/gitlab/initial_root_password\""

echo -e "${GREEN}🎉 Setup complete!${NC}"
