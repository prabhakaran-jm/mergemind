#!/bin/bash

# Complete setup script for MergeMind Terraform infrastructure
# This script handles both Cloud Function deployment and Terraform deployment

set -e

echo "🚀 MergeMind Infrastructure Setup"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    echo "❌ Error: Please run this script from the deploy/terraform directory"
    exit 1
fi

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v terraform >/dev/null 2>&1; then
    echo "❌ Error: Terraform not found. Please install Terraform >= 1.0"
    exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
    echo "❌ Error: gcloud CLI not found. Please install Google Cloud SDK"
    exit 1
fi

if ! command -v gsutil >/dev/null 2>&1; then
    echo "❌ Error: gsutil not found. Please install Google Cloud SDK"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Deploy Cloud Function source
echo ""
echo "📦 Deploying Cloud Function source..."
if [ -f "deploy_function.sh" ]; then
    chmod +x deploy_function.sh
    ./deploy_function.sh
    echo "✅ Cloud Function source deployed"
else
    echo "⚠️  Warning: deploy_function.sh not found, skipping Cloud Function deployment"
fi

# Initialize Terraform
echo ""
echo "🔧 Initializing Terraform..."
terraform init

# Plan deployment
echo ""
echo "📋 Planning Terraform deployment..."
terraform plan

# Ask for confirmation
echo ""
echo "🤔 Ready to deploy infrastructure?"
read -p "Do you want to proceed with terraform apply? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Deploying infrastructure..."
    terraform apply
    echo ""
    echo "✅ Infrastructure deployment completed!"
    echo ""
    echo "📊 Next steps:"
    echo "1. Check terraform output for important values"
    echo "2. Configure secrets in Secret Manager"
    echo "3. Test the Cloud Function endpoint"
    echo "4. Update Fivetran connector configuration"
else
    echo "❌ Deployment cancelled"
    exit 0
fi
