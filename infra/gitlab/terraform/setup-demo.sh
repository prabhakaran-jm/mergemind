#!/bin/bash

# GitLab Demo Resources Setup Script
# Creates demo projects, branches, commits, and merge requests

set -e

echo "🎭 GitLab Demo Resources Setup"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "demo-resources.tf" ]; then
    echo "❌ Error: Please run this script from the terraform directory"
    echo "   Expected files: demo-resources.tf, demo-variables.tf, demo-outputs.tf"
    exit 1
fi

# Check for terraform.tfvars
if [ ! -f "terraform.tfvars" ]; then
    echo "📝 Creating terraform.tfvars from example..."
    if [ -f "demo-terraform.tfvars.example" ]; then
        cp demo-terraform.tfvars.example terraform.tfvars
        echo "✅ Created terraform.tfvars"
        echo "⚠️  Please edit terraform.tfvars and add your GitLab token!"
        echo "   Required: gitlab_token = \"glpat-xxxxxxxxxxxxxxxxxxxx\""
        exit 1
    else
        echo "❌ Error: demo-terraform.tfvars.example not found"
        exit 1
    fi
fi

# Check if gitlab_token is set
if ! grep -q 'gitlab_token.*glpat-' terraform.tfvars; then
    echo "❌ Error: Please set your GitLab token in terraform.tfvars"
    echo "   Required: gitlab_token = \"glpat-xxxxxxxxxxxxxxxxxxxx\""
    exit 1
fi

echo "🔧 Initializing Terraform..."
terraform init

echo "📋 Planning demo resources creation..."
terraform plan -out=demo-resources.tfplan

echo "🚀 Creating demo resources..."
terraform apply demo-resources.tfplan

echo "✅ Demo resources created successfully!"
echo ""
echo "📊 Summary:"
echo "==========="
terraform output -json | jq -r '
  "Projects: " + (.demo_projects | to_entries | map(.value.name) | join(", ")),
  "Merge Requests: " + (.demo_merge_requests | to_entries | map(.value.title) | join(", ")),
  "Issues: " + (.demo_issues | to_entries | map(.value.title) | join(", ")),
  "",
  "Project IDs for Fivetran: " + (.project_ids_for_config | join(", "))
'

echo ""
echo "🔗 Access your GitLab instance:"
echo "   URL: https://35.202.37.189.sslip.io"
echo ""
echo "📝 Next steps:"
echo "   1. Copy the project IDs above to your config.env"
echo "   2. Test the Fivetran connector"
echo "   3. Run MergeMind API to see the demo data"