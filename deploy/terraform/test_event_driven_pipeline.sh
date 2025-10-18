#!/bin/bash

# Test script for event-driven dbt pipeline
# This script tests the complete flow from BigQuery data insertion to dbt run

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"ai-accelerate-mergemind"}
DATASET_RAW="mergemind_raw"
DATASET_MODELED="mergemind"
REGION=${GCP_REGION:-"us-central1"}

echo "Testing Event-Driven dbt Pipeline"
echo "Project: $PROJECT_ID"
echo "Raw Dataset: $DATASET_RAW"
echo "Modeled Dataset: $DATASET_MODELED"
echo "Region: $REGION"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists gcloud; then
    echo "Error: gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

if ! command_exists bq; then
    echo "Error: bq CLI not found. Please install BigQuery CLI."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Error: No active gcloud authentication found."
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Check if datasets exist
echo "Checking if datasets exist..."
if ! bq ls -d --project_id=$PROJECT_ID | grep -q $DATASET_RAW; then
    echo "Error: Dataset $DATASET_RAW not found."
    exit 1
fi

if ! bq ls -d --project_id=$PROJECT_ID | grep -q $DATASET_MODELED; then
    echo "Error: Dataset $DATASET_MODELED not found."
    exit 1
fi

echo "Datasets found successfully!"

# Check if Cloud Function exists and get its URL
echo "Checking Cloud Function..."
FUNCTION_URL=$(gcloud functions describe dbt-trigger-function --region=$REGION --format="value(serviceConfig.uri)" 2>/dev/null)

if [ -z "$FUNCTION_URL" ]; then
    echo "Warning: dbt-trigger-function not found. Please deploy infrastructure first."
    echo "Run: terraform apply"
    exit 1
fi

echo "Cloud Function URL: $FUNCTION_URL"

# Insert test data
echo "Inserting test data into $DATASET_RAW.merge_requests..."

# Generate a unique test ID
TEST_ID=$(date +%s)
TEST_TITLE="Event-Driven Test MR - $TEST_ID"

# Insert test merge request
bq query --use_legacy_sql=false --project_id=$PROJECT_ID "
INSERT INTO \`$PROJECT_ID.$DATASET_RAW.merge_requests\`
(id, project_id, title, description, state, author_id, created_at, updated_at, source_branch, target_branch, web_url)
VALUES 
($TEST_ID, 1, '$TEST_TITLE', 'Test merge request for event-driven dbt pipeline', 'opened', 1, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), 'feature/test-event-driven', 'main', 'https://gitlab.example.com/test-project/-/merge_requests/$TEST_ID')
"

if [ $? -eq 0 ]; then
    echo "Test data inserted successfully!"
    echo "Test MR ID: $TEST_ID"
    echo "Test MR Title: $TEST_TITLE"
else
    echo "Error: Failed to insert test data."
    exit 1
fi

# Trigger dbt run via HTTP (simulating Fivetran connector call)
echo "Triggering dbt run via Cloud Function (simulating Fivetran connector)..."
RESPONSE=$(curl -s -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{"source": "fivetran_connector", "action": "run_dbt", "sync_info": {"sync_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "project_count": 1, "sync_interval_hours": 1}}')

echo "Cloud Function response: $RESPONSE"

# Wait for dbt processing
echo "Waiting for dbt processing (30 seconds)..."
sleep 30

# Check if dbt models were updated
echo "Checking if dbt models were updated..."

# Query the mr_activity_view to see if our test data appears
RESULT=$(bq query --use_legacy_sql=false --project_id=$PROJECT_ID --format=csv "
SELECT COUNT(*) as count
FROM \`$PROJECT_ID.$DATASET_MODELED.mr_activity_view\`
WHERE mr_id = $TEST_ID
" | tail -n +2)

if [ "$RESULT" -gt 0 ]; then
    echo "SUCCESS: Test data found in dbt model!"
    echo "Event-driven dbt pipeline is working correctly."
    
    # Show the test data
    echo "Test data in mr_activity_view:"
    bq query --use_legacy_sql=false --project_id=$PROJECT_ID "
    SELECT mr_id, title, state, age_hours, source_branch, target_branch
    FROM \`$PROJECT_ID.$DATASET_MODELED.mr_activity_view\`
    WHERE mr_id = $TEST_ID
    "
else
    echo "WARNING: Test data not found in dbt model."
    echo "This could mean:"
    echo "1. Event processing is still in progress"
    echo "2. Cloud Function failed to process the event"
    echo "3. dbt run failed"
    
    # Check Cloud Function logs
    echo "Checking Cloud Function logs..."
    gcloud functions logs read dbt-trigger-function --region=$REGION --limit=10
fi

# Clean up test data
echo "Cleaning up test data..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID "
DELETE FROM \`$PROJECT_ID.$DATASET_RAW.merge_requests\`
WHERE id = $TEST_ID
"

echo "Test completed!"
echo ""
echo "Next steps:"
echo "1. Check Cloud Function logs for detailed execution information"
echo "2. Monitor Cloud Function metrics in the GCP Console"
echo "3. Test the dbt trigger endpoint manually with curl"
echo "4. The Fivetran connector will automatically call this URL when sync completes"
echo "5. Update dbt_trigger_url in fivetran_config.json with the actual Cloud Function URL"
