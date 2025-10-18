#!/bin/bash

# GitLab Infrastructure Teardown Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}🗑️  GitLab Infrastructure Teardown${NC}"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    echo -e "${RED}❌ Please run this script from the infra/gitlab directory${NC}"
    exit 1
fi

# Navigate to terraform directory
cd terraform

# Check if terraform state exists
if [ ! -f "terraform.tfstate" ]; then
    echo -e "${YELLOW}⚠️  No terraform state found. Nothing to destroy.${NC}"
    exit 0
fi

# Show what will be destroyed
echo -e "${YELLOW}📋 Resources that will be destroyed:${NC}"
terraform plan -destroy

# Ask for confirmation
echo -e "${RED}❓ Are you sure you want to destroy all resources? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏹️  Teardown cancelled${NC}"
    exit 0
fi

# Destroy infrastructure
echo -e "${RED}🗑️  Destroying infrastructure...${NC}"
terraform destroy -auto-approve

echo -e "${GREEN}✅ Infrastructure destroyed successfully!${NC}"

# Optional: Clean up local files
echo -e "${YELLOW}❓ Do you want to clean up local terraform files? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧹 Cleaning up local files...${NC}"
    rm -f terraform.tfvars
    rm -rf .terraform/
    rm -f .terraform.lock.hcl
    echo -e "${GREEN}✅ Local files cleaned up${NC}"
fi

echo -e "${GREEN}🎉 Teardown complete!${NC}"
