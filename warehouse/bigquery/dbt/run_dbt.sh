#!/bin/bash
# Simple dbt run script
# Usage: ./run_dbt.sh

set -e

echo "Starting dbt transformations..."

# Load environment variables from dbt.env if it exists
if [ -f "dbt.env" ]; then
    echo "Loading environment variables from dbt.env..."
    # Only export lines that don't start with # and contain =
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            # Check if line contains =
            if [[ "$line" == *"="* ]]; then
                # Remove any leading/trailing whitespace
                line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                export "$line"
                echo "Exported: $line"
            fi
        fi
    done < dbt.env
fi

# Get GCP project ID from gcloud if not set
if [ -z "$GCP_PROJECT_ID" ]; then
    export GCP_PROJECT_ID=$(gcloud config get-value project)
fi

echo "Using GCP Project: $GCP_PROJECT_ID"

# Debug: Check if environment variables are set correctly
echo "Environment variables:"
echo "GCP_PROJECT_ID: '$GCP_PROJECT_ID'"
echo "BQ_DATASET_RAW: '$BQ_DATASET_RAW'"
echo "BQ_DATASET_MODELED: '$BQ_DATASET_MODELED'"

# Navigate to dbt directory
cd "$(dirname "$0")"

# Verify environment variables are set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "ERROR: GCP_PROJECT_ID is not set!"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "dbt_packages" ]; then
    echo "Installing dbt dependencies..."
    dbt deps
fi

# Run dbt transformations
echo "Running dbt models..."
dbt run --profiles-dir .

# Run dbt tests
echo "Running dbt tests..."
dbt test --profiles-dir .

# Generate docs (optional)
echo "Generating dbt docs..."
dbt docs generate --profiles-dir .

echo "dbt transformations completed successfully!"

# Optional: Show run results
echo "Last run results:"
dbt show --profiles-dir . --select mr_activity_view --limit 5
