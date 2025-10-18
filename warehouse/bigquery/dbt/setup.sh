#!/bin/bash
# Cloud Build Triggers setup for dbt automation
# This creates a trigger that runs dbt transformations when you push changes

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"$(gcloud config get-value project)"}
TRIGGER_NAME="dbt-transform-trigger"

echo "🚀 Setting up Cloud Build Triggers for dbt automation..."
echo "Project: $PROJECT_ID"

# Enable required APIs
echo "📋 Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "⚠️  Not in a git repository. Running manual build instead..."
    
    # Create a manual build trigger
    gcloud builds submit \
        --config=cloudbuild-trigger.yaml \
        --project=$PROJECT_ID
    
    echo "✅ Manual build completed!"
    echo "📊 To automate this, set up a GitHub repository and run this script again"
    
else
    # Get repository info
    REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
    REPO_NAME=$(basename "$REPO_URL" .git 2>/dev/null || echo "mergemind")
    
    echo "📁 Repository: $REPO_NAME"
    
    # Create GitHub trigger
    gcloud builds triggers create github \
        --repo-name=$REPO_NAME \
        --repo-owner=$(git config user.name || echo "your-github-username") \
        --branch-pattern="main" \
        --build-config=cloudbuild-trigger.yaml \
        --name=$TRIGGER_NAME \
        --project=$PROJECT_ID
    
    echo "✅ Cloud Build trigger created!"
    echo ""
    echo "🎯 How to trigger dbt runs:"
    echo "1. Push to main branch:"
    echo "   git add . && git commit -m 'Trigger dbt run' && git push"
    echo ""
    echo "2. Manual trigger:"
    echo "   gcloud builds triggers run $TRIGGER_NAME --branch=main"
    echo ""
    echo "3. Monitor builds:"
    echo "   gcloud builds list --filter='trigger.name:$TRIGGER_NAME'"
fi

echo ""
echo "📊 Cost estimate: ~$0.003 per build + compute time (~$0.01-0.05 per run)"
echo "🎯 Benefits:"
echo "  - Event-driven (runs when you push changes)"
echo "  - Cost-effective (pay only when triggered)"
echo "  - Integrated with your development workflow"
echo "  - Easy to monitor and debug"
